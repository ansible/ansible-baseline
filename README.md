# ansible-baseline
A baseline playbook for testing Ansible performance

## Notes

These playbooks are meant to be run with whatever your inventory is, and make no assumptions about that inventory.

The only thing to note, is that `ansible_connection` will be overridden for each play, to either `local`, `ssh`, or `paramiko` for testing performance amongst different connection methods.

## Use

```
$ ansible-playbook -i /path/to/inventory playbook.yml
```

### Baseline callback plugin

This repo ships a custom callback plugin named `baseline` that does *not* require whitelisting, and will always run.

By default host timings are also shown, but this can be disabled using `BASELINE_SHOW_HOST_TIMINGS=0 ansible-playbook ...`

#### Output description

The output of the callback will look similar to:

```
Play: Local baseline ************************************************** 68.74s
    Gather Facts ------------------------------------------------------- 2.78s
        localhost0 ............................................. 1.99s / 0.00s
        localhost1 ............................................. 1.71s / 0.02s
        localhost2 ............................................. 1.75s / 0.04s
        localhost3 ............................................. 1.61s / 0.06s
        localhost4 ............................................. 1.79s / 0.08s
        localhost5 ............................................. 0.97s / 1.65s
        localhost6 ............................................. 0.93s / 1.70s
        localhost7 ............................................. 0.89s / 1.77s
        localhost8 ............................................. 0.91s / 1.80s
        localhost9 ............................................. 0.86s / 1.92s
```

1. The first line in the output above is the name of the play, and the execution time for that play. In this case `68.74s`.
1. The second line in the output shows the name of the task, and the execution time for that task. In this case `2.78s`.
1. The remaining lines are host timings
    1. The first number is the execution time for the specific host
    2. The second number is the time the host was waiting in the queue before starting execution

## Testing Matrix

There are a few things that this baseline is ignorant of, that should be accounted for in a testing matrix.

Those configurations are things such as:

1. Use of password auth via `sshpass` instead of key based auth
1. Use of a jumphost/bastion via `ProxyCommand`
1. Whether `ControlPersist` is enabled or not
