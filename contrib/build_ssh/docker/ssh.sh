#!/bin/sh

/usr/bin/ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa -b 4096 -N ""
/usr/bin/ssh-keygen -f /etc/ssh/ssh_host_ecdsa_key -t ecdsa -b 521 -N ""
/usr/bin/ssh-keygen -f /etc/ssh/ssh_host_ed25519_key -t ed25519 -N ""
/usr/sbin/sshd -D
