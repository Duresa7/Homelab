#!/usr/bin/python3
import datetime as dt
import fcntl
import fnmatch
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

CATEGORIES = {'tv-sonarr': 'sonarr', 'radarr': 'radarr'}
VIDEO = {'.mkv', '.mp4', '.m4v', '.avi', '.ts', '.m2ts', '.mts', '.mpg', '.mpeg', '.wmv', '.mov', '.vob', '.webm', '.ogm', '.ogv', '.strm', '.iso', '.img'}
ARCHIVE = {'.rar', '.zip', '.7z', '.tar', '.gz', '.bz2', '.xz'}
CODE = {'.exe', '.com', '.scr', '.msi', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.jse', '.lnk', '.hta', '.dll', '.sh', '.appimage', '.apk'}
ROOT = Path('/data/downloads')

def classify(files, patterns):
    if not files:
        return None
    for f in files:
        name = f['name'].casefold()
        if PurePosixPath(name).suffix in CODE or any(fnmatch.fnmatchcase(PurePosixPath(name).name, p.casefold()) for p in patterns):
            return 'blocked_file_type'
    suffixes = {PurePosixPath(f['name'].casefold()).suffix for f in files}
    if suffixes & VIDEO:
        return None
    # Nothing here unpacks, so an archive with no video can never import; it is
    # also how fake releases hide an executable from the excluded-name filter.
    if suffixes & ARCHIVE or any(s.startswith('.r') and s[2:].isdigit() for s in suffixes):
        return 'archive_payload'
    # Leave unknown formats for review.
    if suffixes and suffixes <= {'.txt', '.nfo', '.jpg', '.jpeg', '.png', '.srt', '.sub', '.idx', '.url', '.html', '.htm'}:
        return 'no_video_payload'
    return None

def safe_delete(t, files):
    try:
        save = Path(t['save_path'])
        content = Path(t['content_path'])
        if not save.is_relative_to(ROOT) or not content.is_relative_to(ROOT) or content in (ROOT, save):
            return False
        for p in [save, content] + [save / f['name'] for f in files]:
            if not p.is_relative_to(ROOT) or '..' in p.parts or not p.resolve().is_relative_to(ROOT):
                return False
            if any(x.is_symlink() for x in [p, *p.parents] if x.is_relative_to(ROOT)):
                return False
        return bool(files)
    except (KeyError, OSError, ValueError):
        return False

class Client:
    def q(self, path, data=None):
        cmd = ['docker', 'exec', 'qbittorrent', 'curl', '--fail', '--silent', '--max-time', '15']
        if data is not None:
            cmd += ['--data', urllib.parse.urlencode(data)]
        p = subprocess.run(cmd + ['http://127.0.0.1:8080/api/v2/' + path], capture_output=True, text=True, timeout=20)
        if p.returncode:
            raise RuntimeError('qBittorrent API unavailable')
        return json.loads(p.stdout) if p.stdout else None

    def arr(self, app, path, data=None, method=None):
        port = {'sonarr': 8989, 'radarr': 7878}[app]
        key = ET.parse('/opt/media-stack/config/' + app + '/config.xml').findtext('ApiKey')
        req = urllib.request.Request('http://127.0.0.1:' + str(port) + '/api/v3/' + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'X-Api-Key': key, 'Content-Type': 'application/json'}, method=method)
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            return json.loads(body) if body else None

    def queue(self, app):
        rows = []
        page = 1
        while True:
            d = self.arr(app, 'queue?pageSize=200&page=' + str(page) + '&includeUnknownSeriesItems=true&includeUnknownMovieItems=true')
            rows.extend(d['records'])
            if len(rows) >= d['totalRecords']:
                return rows
            if not d['records']:
                raise RuntimeError('Incomplete queue response')
            page += 1


class State:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.folder / 'state.json'
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {'version': 1, 'denied': {}, 'targets': {}, 'searches': []}
        if self.data.get('version') != 1 or not all(k in self.data for k in ['denied', 'targets', 'searches']):
            raise RuntimeError('Invalid guard state')

    def save(self):
        temp = self.folder / 'state.tmp'
        with open(temp, 'w') as f:
            os.chmod(temp, 0o600)
            json.dump(self.data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, self.path)

class Guard:
    def __init__(self, client, state, categories=None, now=None):
        self.c = client
        self.s = state
        self.categories = CATEGORIES if categories is None else categories
        self.now = time.time() if now is None else now

    def log(self, event, **fields):
        print(json.dumps({'event': event, **fields}), flush=True)

    def targets(self, app, rows):
        for row in rows:
            item = row.get('episodeId') if app == 'sonarr' else row.get('movieId')
            if item:
                key = app + ':' + str(item)
                self.s.data['targets'].setdefault(key, {'app': app, 'id': item, 'attempts': 0, 'last': 0})

    def run(self, dry=False):
        prefs = self.c.q('app/preferences')
        patterns = prefs.get('excluded_file_names', '').splitlines()
        if not prefs.get('excluded_file_names_enabled') or '*.exe' not in [x.casefold() for x in patterns]:
            raise RuntimeError('Required filename filter is disabled')
        qs = {}
        for t in self.c.q('torrents/info'):
            try:
                app = self.categories.get(t.get('category'))
                if not app:
                    continue
                h = t['hash'].lower()
                files = self.c.q('torrents/files?hash=' + h)
                prior = self.s.data['denied'].get(h)
                reason = prior['reason'] if prior else classify(files, patterns)
                if not reason:
                    continue
                if reason == 'no_video_payload' and self.now - t.get('added_on', self.now) < 120:
                    continue
                self.log('reject_candidate', hash=h, reason=reason, dry_run=dry)
                if dry:
                    continue
                record = self.s.data['denied'].setdefault(h, {'reason': reason, 'first': self.now})
                self.s.save()
                self.c.q('torrents/stop', {'hashes': h})
                # An Arr read failure leaves this torrent stopped for the next run.
                if app not in qs:
                    qs[app] = self.c.queue(app)
                rows = [r for r in qs[app] if r.get('downloadId', '').lower() == h]
                if not rows and self.now - record['first'] < 600:
                    self.log('awaiting_arr_tracking', hash=h)
                    continue
                self.targets(app, rows)
                self.s.save()
                # Blocklist before deleting; path checks govern download-file removal.
                for row_id in sorted({r['id'] for r in rows}):
                    self.c.arr(app, 'queue/' + str(row_id) + '?removeFromClient=false&blocklist=true&skipRedownload=true', method='DELETE')
                delete_files = safe_delete(t, files)
                self.c.q('torrents/delete', {'hashes': h, 'deleteFiles': 'true' if delete_files else 'false'})
                self.log('rejected', hash=h, reason=reason, files_deleted=delete_files, tracked=bool(rows))
            except Exception as e:
                self.log('torrent_check_error', hash=t.get('hash'), type=type(e).__name__)
        if not dry:
            self.retry()
            self.s.save()

    def retry(self):
        recent = [x for x in self.s.data['searches'] if x > self.now - 86400]
        self.s.data['searches'] = recent
        for key, target in self.s.data['targets'].items():
            try:
                if target.get('done') or target['attempts'] >= 2 or self.now - target['last'] < 1800 or len(recent) >= 6:
                    continue
                app, item = target['app'], target['id']
                entity = self.c.arr(app, ('episode/' if app == 'sonarr' else 'movie/') + str(item))
                if entity.get('hasFile'):
                    target['done'] = True
                    continue
                if not entity.get('monitored'):
                    continue
                if app == 'sonarr':
                    series = self.c.arr(app, 'series/' + str(entity['seriesId']))
                    if not series.get('monitored'):
                        continue
                    air = entity.get('airDateUtc')
                    if not air or dt.datetime.fromisoformat(air.replace('Z', '+00:00')).timestamp() > self.now:
                        continue
                    command = {'name': 'EpisodeSearch', 'episodeIds': [item]}
                else:
                    if not entity.get('isAvailable'):
                        continue
                    command = {'name': 'MoviesSearch', 'movieIds': [item]}
                queue = self.c.queue(app)
                field = 'episodeId' if app == 'sonarr' else 'movieId'
                if any(r.get(field) == item for r in queue):
                    continue
                # Reserve first so ambiguous timeouts cannot cause unbounded searches.
                target['attempts'] += 1
                target['last'] = self.now
                recent.append(self.now)
                self.s.save()
                result = self.c.arr(app, 'command', data=command)
                self.log('replacement_search', target=key, attempt=target['attempts'], command_id=result.get('id'))
            except Exception as e:
                self.log('retry_error', target=key, type=type(e).__name__)

def main():
    os.umask(0o077)
    folder = Path('/var/lib/media-download-guard')
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    with open(folder / 'lock', 'w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        Guard(Client(), State(folder)).run(dry='--dry-run' in sys.argv)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'event': 'guard_error', 'type': type(e).__name__}), flush=True)
        sys.exit(1)
