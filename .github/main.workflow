workflow "On Push" {
  on = "push"
  resolves = ["Ansible Lint"]
}

action "Ansible Lint" {
  uses = "ansible/ansible-lint-action@master"
  env = {
    ACTION_PLAYBOOK_NAME = "playbook.yml"
  }
}

workflow "On PR" {
  on = "pull_request"
  resolves = ["Ansible Lint"]
}
