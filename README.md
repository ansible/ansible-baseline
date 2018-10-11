# ansible-baseline
A baseline playbook for testing Ansible performance

## Notes

These playbooks are meant to be run with whatever your inventory is, and make no assumptions about that inventory.

The only thing to note, is that `ansible_connection` will be overridden for each play, to either `local`, `ssh`, or `paramiko` for testing performance amongst different connection methods.

# Use

```
$ ansible-playbook -i /path/to/inventory playbook.yml
```
