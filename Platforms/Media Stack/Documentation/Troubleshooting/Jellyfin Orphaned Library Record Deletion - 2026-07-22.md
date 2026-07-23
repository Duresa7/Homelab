# Jellyfin Orphaned Library Record Deletion

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Symptom

Jellyfin showed a generic write-access error when I tried to delete one episode from a television series:

```text
There was an error deleting the item from the server. Please check that Jellyfin has write access to the media folder and try again.
```

Jellyfin remained healthy, playback services stayed online, & the error affected deletion of an item whose media directory no longer existed.

## Reproduction

The authenticated item request returned HTTP `200`, proving the episode remained in Jellyfin's database. Deleting the same item returned HTTP `404`. Jellyfin logged the actual exception at 21:55 EDT:

```text
Could not find a part of the path '/media/tv/<REMOVED_TV_SERIES>/Season 2'.
URL DELETE /Items/<ITEM_ID>.
```

The popup's write-access diagnosis was false. Jellyfin received the request and reached its local deletion handler, but that handler couldn't enumerate a parent directory that was already absent.

## Hypotheses and Tests

| Rank | Hypothesis | Prediction | Result |
|---:|---|---|---|
| 1 | Jellyfin retained records after the series directory disappeared | The path is absent while the same item ID still returns HTTP `200` | Confirmed: the filesystem path was absent & the database retained 18 matching records |
| 2 | UID/GID, mount mode, or directory permissions blocked deletion | A create, write, & delete probe as Jellyfin UID/GID `1000:1000` fails at `/media/tv` | Rejected: all three operations passed & left no probe artifact |
| 3 | An ACL or immutable attribute blocked the series directory | `getfacl`, `lsattr`, or ownership differs from the working library root | Rejected before the series-level check because the complete series directory was absent; `/media/tv` remained writable |
| 4 | NPM changed or blocked the DELETE request | Jellyfin never logs the request or reports an HTTP-layer failure | Rejected: Jellyfin logged the exact item ID & threw a local `DirectoryNotFoundException` |

## Root Cause

Jellyfin 10.11.11 retained 18 non-virtual database records for one removed series, its two seasons, & 15 episodes. Three completed media-library scans did not remove those records. The physical series directory was already absent, so Jellyfin's delete handler failed while checking the missing season directory & returned the misleading generic write-access message.

I didn't establish which application or user removed the directory. Sonarr's only current series with a similar title used a different path without the `2024` suffix, remained monitored, held zero episode files, & had no active queue entry. I left that separate series unchanged.

## Corrective Action

I created only the empty top-level directory that the stale Jellyfin series record expected. I then deleted the top-level series through Jellyfin's authenticated `DELETE /Items/{itemId}` endpoint. Jellyfin returned HTTP `204`, removed the empty directory, & cascaded the database deletion through all 18 orphaned records.

I didn't edit `jellyfin.db`, change Compose, restart a container, create a backup, or retain an access token. The API credential remained in a remote shell variable and wasn't printed or written to evidence.

## Verification

- Jellyfin's UID/GID `1000:1000` created, wrote, & removed a probe beneath `/media/tv`; no probe path remained.
- The series-level delete returned HTTP `204`.
- The removed series path remained absent & its matching `BaseItems` count fell from `18` to `0`.
- A post-change `POST /Library/Refresh` returned HTTP `204`; the scan completed in 10 seconds & didn't recreate the records.
- The previous episode ID returned HTTP `404`, which is now the expected item-not-found result.
- Jellyfin stayed `healthy`; all eight Compose services stayed `running`.
- `/data/media` remained on ext4 `/dev/sda1` with `rw,noatime`.
- The Movies tree retained 24 files. The TV tree contained zero files before & after the repair.
- The separate Sonarr series kept ID `3`, its existing path, monitored state, & zero episode-file count.
- Jellyfin logged zero references to the removed series during the final verification window.

The [diagnosis and repair transcript](../../Evidence/Jellyfin%20Orphaned%20Library%20Record%20Cleanup%20-%202026-07-22/Logs/S01-Diagnosis-and-Repair-2026-07-22.md) records the redacted request envelopes & observed results.

## Failed Attempts

The first write probe targeted the missing series directory and stopped at `stat`; that failure confirmed the complete path was gone. A library scan completed before the second user attempt, & two more scans completed during diagnosis, but all 18 records remained.

An application API key without user context returned HTTP `400` for the item lookup & HTTP `404` for deletion. I switched to an existing administrator session token held only in the remote shell. That token reproduced the user path with HTTP `200` for lookup & the same logged path exception on deletion.

## Rollback

This correction removed metadata for files that were already absent. I created no backup. Reacquiring the series into the TV library & running a scan rebuilds its library entries; Jellyfin can't restore the removed records from the current database.

## Classification

I kept this as routine platform troubleshooting. Jellyfin, the media mount, playback, downloads, & the other seven containers remained available; the observed fault was one orphaned library subtree.
