import subprocess,json,datetime,hashlib
def run(*args):
 return subprocess.check_output(args,text=True).strip()
def digest(x):
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def snapshot():
 ids=run('docker','ps','-aq','--no-trunc').split()
 raw=json.loads(run('docker','inspect',*ids)) if ids else []
 containers=[]
 for c in raw:
  containers.append({'id':c['Id'],'name':c['Name'].lstrip('/'),'image':c['Image'],'status':c['State']['Status'],'started_at':c['State']['StartedAt'],'restart_count':c['RestartCount'],'health':c['State'].get('Health',{}).get('Status'),'mounts_hash':digest(c['Mounts'])})
 containers.sort(key=lambda c:c['name'])
 volumes=sorted(run('docker','volume','ls','-q').split())
 volume_defs=json.loads(run('docker','volume','inspect',*volumes)) if volumes else []
 tagged=sorted(x for x in run('docker','image','ls','--no-trunc','--format','{{.Repository}}:{{.Tag}} {{.ID}}').splitlines() if not x.startswith('<none>:'))
 dangling_ids=sorted(set(run('docker','image','ls','--filter','dangling=true','-q','--no-trunc').split()))
 dangling_raw=json.loads(run('docker','image','inspect',*dangling_ids)) if dangling_ids else []
 used={c['image'] for c in containers}
 dangling=[{'id':i['Id'],'size':i['Size'],'created':i['Created'],'tags':i.get('RepoTags') or [],'used_by_container':i['Id'] in used,'prune_excluded':(i.get('Config',{}).get('Labels') or {}).get('dockhand.prune')=='false'} for i in dangling_raw]
 return {'containers':containers,'volumes':volumes,'volume_definitions_hash':digest(volume_defs),'tagged_images':tagged,'dangling_images':dangling}
def summary(s):
 return {'container_count':len(s['containers']),'running_count':sum(c['status']=='running' for c in s['containers']),'containers':[{'name':c['name'],'status':c['status'],'health':c['health']} for c in s['containers']],'containers_hash':digest(s['containers']),'volume_count':len(s['volumes']),'volume_definitions_hash':s['volume_definitions_hash'],'tagged_images_count':len(s['tagged_images']),'tagged_images_hash':digest(s['tagged_images']),'dangling_images':s['dangling_images']}

import os,sys
plan=json.loads(sys.argv[1])
def small(s):
 r=summary(s)
 r['dangling_image_count']=len(r.pop('dangling_images'))
 return r
def storage():
 root=run('docker','info','--format','{{.DockerRootDir}}')
 probe=root
 try:v=os.statvfs(probe)
 except PermissionError:
  probe='/'
  v=os.statvfs(probe)
 return {'docker_root':root,'filesystem_probe_path':probe,'filesystem_available_bytes':v.f_bavail*v.f_frsize,'docker_usage':[json.loads(x) for x in run('docker','system','df','--format','{{json .}}').splitlines()]}
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
before=snapshot()
bs=summary(before)
for key in ['containers_hash','volume_definitions_hash','tagged_images_hash']:
 if bs[key]!=plan[key]:
  raise SystemExit('Preflight state changed: '+key)
eligible={i['id'] for i in before['dangling_images'] if not i['tags'] and not i['used_by_container'] and not i['prune_excluded']}
assert set(plan['candidates'])<=eligible,'Candidate eligibility changed'
disk_before=storage()
results=[]
for image_id in plan['candidates']:
 live=json.loads(run('docker','image','inspect',image_id))[0]
 ids=run('docker','ps','-aq','--no-trunc').split()
 used={c['Image'] for c in json.loads(run('docker','inspect',*ids))} if ids else set()
 if live.get('RepoTags') or image_id in used or (live.get('Config',{}).get('Labels') or {}).get('dockhand.prune')=='false':
  results.append({'id':image_id,'skipped':'now tagged, referenced, or protected'})
  continue
 cmd=['docker','image','rm','--no-prune',image_id]
 p=subprocess.run(cmd,text=True,capture_output=True)
 results.append({'id':image_id,'exit_code':p.returncode,'stdout_hash':digest(p.stdout),'stderr':p.stderr})
 if p.returncode:
  break
after=snapshot()
disk_after=storage()
checks={'containers_unchanged':before['containers']==after['containers'],'volumes_unchanged':before['volumes']==after['volumes'] and before['volume_definitions_hash']==after['volume_definitions_hash'],'tagged_images_unchanged':before['tagged_images']==after['tagged_images']}
all_ids=set(run('docker','image','ls','-aq','--no-trunc').split())
checks['removed_images_absent']=all(r['id'] not in all_ids for r in results if r.get('exit_code')==0)
checks['all_candidates_removed']=len(results)==len(plan['candidates']) and all(r.get('exit_code')==0 for r in results)
out={'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before':small(before),'after':small(after),'storage_before':disk_before,'storage_after':disk_after,'results':results,'checks':checks}
print(json.dumps(out,separators=(',',':')))
sys.exit(0 if all(checks.values()) else 2)
