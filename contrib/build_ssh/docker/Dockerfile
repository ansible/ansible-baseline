FROM alpine

RUN set -eux && \
    apk add --no-cache openssh python sudo && \
    /usr/sbin/adduser -D ansible && \
    echo 'ansible:ansible' | chpasswd

COPY --chown=ansible:ansible vagrant.pub /home/ansible/.ssh/authorized_keys
COPY vagrant.pub /root/.ssh/authorized_keys
COPY ssh.sh /usr/local/bin/ssh.sh
COPY ansible.sudoers /etc/sudoers.d/ansible

CMD ["/bin/sh", "/usr/local/bin/ssh.sh"]
