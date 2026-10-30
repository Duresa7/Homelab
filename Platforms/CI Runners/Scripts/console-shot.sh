#!/bin/sh
# Screenshot a VM's console to /tmp/vm-<id>.png. Usage: console-shot.sh <vmid> [node-ip]
# Needs python3-pil on the workstation.
VMID=$1; NODE=${2:-192.168.70.14}
ssh -o BatchMode=yes root@"$NODE" "echo 'screendump /tmp/vm-$VMID.ppm' | qm monitor $VMID >/dev/null" &&
scp -q root@"$NODE":/tmp/vm-$VMID.ppm /tmp/vm-$VMID.ppm &&
python3 -c "from PIL import Image; Image.open('/tmp/vm-$VMID.ppm').save('/tmp/vm-$VMID.png')" && echo /tmp/vm-$VMID.png
