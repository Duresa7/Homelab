#!/bin/sh
# Read back the Linux Host Baseline Standard checks on e2b-01. Run as root through Ansible's script module.
echo "id dkadi: $(id dkadi)"
echo "sudo -l -U ai-agent: $(sudo -l -U ai-agent 2>&1 | tail -1)"
echo "ansible sudo -n: $(su -s /bin/sh ansible -c 'sudo -n true' && echo rc0)"
echo "passwd -S root: $(passwd -S root | awk '{print $2}')"
echo "passwd -S ai-agent: $(passwd -S ai-agent | awk '{print $2}')"
sshd -T | grep -E '^(permitrootlogin|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication) '
ls -l /etc/sudoers.d/ | tail -n +2 | awk '{print $1,$9}'
echo "ansible key comment: $(ssh-keygen -lf /home/ansible/.ssh/authorized_keys | awk '{print $3}')"
echo "ai-agent key comment: $(ssh-keygen -lf /home/ai-agent/.ssh/authorized_keys | awk '{print $3}')"
echo "cloud-init disabled: $(test -f /etc/cloud/cloud-init.disabled && echo yes)"
timedatectl | grep "Time zone"; stat -c '%a %U %n' /home/dkadi /home/ai-agent /home/ansible
echo "sudo is: $(readlink -f /usr/bin/sudo)"
systemctl is-active ssh wazuh-agent qemu-guest-agent docker e2b-nft-guard | tr '\n' ' '; echo
