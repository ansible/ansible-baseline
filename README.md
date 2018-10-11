# ansible-baseline
A baseline playbook for testing Ansible performance

## Notes

These playbooks are meant to be run with whatever your inventory is, and make no assumptions about that inventory.

The only thing to note, is that `ansible_connection` will be overridden for each play, to either `local`, `ssh`, or `paramiko` for testing performance amongst different connection methods.

## Use

```
$ ansible-playbook -i /path/to/inventory playbook.yml
```

## Testing Matrix

There are a few things that this baseline is ignorant of, that should be accounted for in a testing matrix.

Those configurations are things such as:

1. Use of password auth via `sshpass` instead of key based auth
1. Use of a jumphost/bastion via `ProxyCommand`
1. Whether `ControlPersist` is enabled or not
