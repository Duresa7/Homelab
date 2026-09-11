#!/usr/bin/env python3
"""Bounded offline copy for VM 116, 2026-09-11. Does not switch VM disks."""
import json
import os
from pathlib import Path
import subprocess
import time

SOURCE = '/dev/ssd-lvm1/vm-116-disk-1'
TARGET = '/dev/ssd-lvm1/vm-116-disk-2'
ROOT_UUID = '21a6acef-87a5-46a8-9038-5387d0da0725'
SWAP_UUID = '328621fb-5141-4d0a-8219-ebe2491617b0'
WORK = Path('/mnt/app01-disk-replacement-20260911')


def run(*args, capture=False, input=None, allowed=(0,)):
    print(time.strftime('%Y-%m-%d %H:%M:%S %Z'), ' '.join(args), flush=True)
    p = subprocess.run(args, text=True, input=input, capture_output=capture)
    if p.returncode not in allowed:
        if capture:
            print(p.stdout, p.stderr, flush=True)
        raise RuntimeError(f'{args[0]} exited {p.returncode}')
    return p.stdout.strip() if capture else None


def main():
    assert os.geteuid() == 0
    assert run('qm', 'status', '116', capture=True) == 'status: stopped'
    config = run('qm', 'config', '116', capture=True)
    assert 'name: app-01\n' in config
    assert 'scsi0: ssd-lvm1:vm-116-disk-1,' in config
    assert 'vm-116-disk-2' not in config
    assert int(run('blockdev', '--getsize64', SOURCE, capture=True)) == 200 * 2**30
    assert int(run('blockdev', '--getsize64', TARGET, capture=True)) == 64 * 2**30
    assert not run('wipefs', '--noheadings', '--output', 'TYPE', TARGET, capture=True)
    assert not WORK.exists()
    original = json.loads(run('sfdisk', '--json', SOURCE, capture=True))['partitiontable']
    parts = original['partitions']
    assert original['label'] == 'gpt' and original['sectorsize'] == 512
    assert len(parts) == 3
    assert parts[0]['start'] == 2048 and parts[0]['size'] == 1998848
    assert parts[1]['start'] == 2000896 and parts[1]['size'] == 413235200
    assert parts[2]['start'] == 415236096 and parts[2]['size'] == 4192256
    sectors = 64 * 2**30 // 512
    swap_start = (sectors - 34 - parts[2]['size']) // 2048 * 2048
    layout = ['label: gpt', 'label-id: ' + original['id'], 'unit: sectors']
    for p, start, size in [
        (parts[0], parts[0]['start'], parts[0]['size']),
        (parts[1], parts[1]['start'], swap_start - parts[1]['start']),
        (parts[2], swap_start, parts[2]['size']),
    ]:
        layout.append(f'start={start}, size={size}, type={p["type"]}, uuid={p["uuid"]}')
    source_loop = target_loop = None
    mounted = []
    WORK.mkdir(mode=0o700)
    try:
        source_loop = run('losetup', '--find', '--show', '--read-only', '--partscan', SOURCE, capture=True)
        assert run('blkid', '-s', 'UUID', '-o', 'value', source_loop + 'p2', capture=True) == ROOT_UUID
        assert run('blkid', '-s', 'UUID', '-o', 'value', source_loop + 'p3', capture=True) == SWAP_UUID
        run('e2fsck', '-f', '-n', source_loop + 'p2')
        run('sfdisk', TARGET, input='\n'.join(layout) + '\n')
        target_loop = run('losetup', '--find', '--show', '--partscan', TARGET, capture=True)
        run('udevadm', 'settle')
        run('dd', 'if=' + source_loop + 'p1', 'of=' + target_loop + 'p1', 'bs=4M', 'conv=fsync', 'status=progress')
        run('cmp', source_loop + 'p1', target_loop + 'p1')
        run('mkfs.ext4', '-U', ROOT_UUID, target_loop + 'p2')
        run('mkswap', '-U', SWAP_UUID, target_loop + 'p3')
        src, dst = WORK / 'source', WORK / 'target'
        src.mkdir()
        dst.mkdir()
        run('mount', '-o', 'ro,noload', source_loop + 'p2', str(src))
        mounted.append(src)
        run('mount', target_loop + 'p2', str(dst))
        mounted.append(dst)
        run('rsync', '-aHAXSx', '--numeric-ids', '--stats', str(src) + '/', str(dst) + '/')
        # Verify file contents, metadata, ACLs, xattrs, and extra destination paths.
        delta = run('rsync', '-aHAXSxnc', '--numeric-ids', '--delete', '--itemize-changes',
                    str(src) + '/', str(dst) + '/', capture=True)
        if delta:
            print(delta, flush=True)
            raise RuntimeError('Post-copy checksum comparison found differences')
        for relative in ['etc/fstab', 'boot/grub/grub.cfg']:
            assert (src / relative).read_bytes() == (dst / relative).read_bytes()
        run('sync', '-f', str(dst))
        while mounted:
            run('umount', str(mounted[-1]))
            mounted.pop()
        run('e2fsck', '-f', '-n', target_loop + 'p2')
        for n in [1, 2, 3]:
            assert run('blkid', '-s', 'UUID', '-o', 'value', source_loop + f'p{n}', capture=True) == run('blkid', '-s', 'UUID', '-o', 'value', target_loop + f'p{n}', capture=True)
        print('COPY_VERIFIED: 64 GiB target, identical file contents and boot identifiers', flush=True)
    finally:
        for path in reversed(mounted):
            run('umount', str(path))
        if target_loop:
            run('losetup', '--detach', target_loop)
        if source_loop:
            run('losetup', '--detach', source_loop)
        for child in WORK.iterdir():
            child.rmdir()
        WORK.rmdir()


if __name__ == '__main__':
    main()
