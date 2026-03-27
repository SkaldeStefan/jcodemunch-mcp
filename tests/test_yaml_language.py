"""Tests for YAML and Ansible parsing support."""

from jcodemunch_mcp.parser import parse_file
from jcodemunch_mcp.parser.languages import get_language_for_path


GENERIC_YAML_SOURCE = """
services:
  api:
    image: example/api:latest
    ports:
      - "8080:8080"
feature_flags:
  signup: true
"""


ANSIBLE_PLAYBOOK_SOURCE = """
- name: Configure web nodes
  hosts: web
  tasks:
    - name: Install nginx
      ansible.builtin.package:
        name: nginx
        state: present
    - name: Start service
      ansible.builtin.service:
        name: nginx
        state: started
  handlers:
    - name: Restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
"""


ANSIBLE_TASKS_SOURCE = """
- name: Create app directory
  ansible.builtin.file:
    path: /srv/app
    state: directory

- ansible.builtin.template:
    src: app.conf.j2
    dest: /etc/app.conf
"""


ANSIBLE_VARS_SOURCE = """
app_port: 8080
app_debug: true
database:
  host: db.internal
  port: 5432
"""


MULTI_DOC_YAML_SOURCE = """
services:
  api:
    image: example/api:latest
---
feature_flags:
  signup: true
"""


def test_yaml_extension_mapping():
    assert get_language_for_path("settings.yaml") == "yaml"
    assert get_language_for_path("settings.yml") == "yaml"


def test_ansible_path_heuristics_override_yaml():
    assert get_language_for_path("playbooks/site.yml") == "ansible"
    assert get_language_for_path("playbooks/deploy.yml") == "ansible"
    assert get_language_for_path("roles/web/tasks/main.yaml") == "ansible"
    assert get_language_for_path("group_vars/all.yml") == "ansible"
    assert get_language_for_path("inventory/group_vars/all.yml") == "ansible"


def test_openapi_basename_still_wins_over_yaml():
    assert get_language_for_path("openapi.yaml") == "openapi"
    assert get_language_for_path("swagger.yml") == "openapi"


def test_parse_generic_yaml_symbols():
    symbols = parse_file(GENERIC_YAML_SOURCE, "config/settings.yaml", "yaml")
    by_qualified = {symbol.qualified_name: symbol for symbol in symbols}

    assert "services" in by_qualified
    assert by_qualified["services"].kind == "type"
    assert "services.api" in by_qualified
    assert by_qualified["services.api"].kind == "type"
    assert "services.api.image" in by_qualified
    assert by_qualified["services.api.image"].kind == "constant"
    assert "feature_flags.signup" in by_qualified
    assert by_qualified["feature_flags.signup"].kind == "constant"


def test_parse_multi_document_yaml_symbols():
    symbols = parse_file(MULTI_DOC_YAML_SOURCE, "config/settings.yaml", "yaml")
    by_qualified = {symbol.qualified_name: symbol for symbol in symbols}

    assert "services.api.image" in by_qualified
    assert "feature_flags.signup" in by_qualified


def test_parse_ansible_playbook_symbols():
    symbols = parse_file(ANSIBLE_PLAYBOOK_SOURCE, "playbooks/site.yml", "ansible")
    by_qualified = {symbol.qualified_name: symbol for symbol in symbols}

    assert "Configure web nodes" in by_qualified
    assert by_qualified["Configure web nodes"].kind == "class"
    assert "Configure web nodes.tasks.Install nginx" in by_qualified
    assert by_qualified["Configure web nodes.tasks.Install nginx"].kind == "function"
    assert "Configure web nodes.handlers.Restart nginx" in by_qualified
    assert by_qualified["Configure web nodes.handlers.Restart nginx"].kind == "function"


def test_parse_ansible_tasks_file_symbols():
    symbols = parse_file(ANSIBLE_TASKS_SOURCE, "roles/app/tasks/main.yml", "ansible")
    by_qualified = {symbol.qualified_name: symbol for symbol in symbols}

    assert "task.tasks.Create app directory" in by_qualified
    assert by_qualified["task.tasks.Create app directory"].kind == "function"
    assert "task.tasks.ansible.builtin.template" in by_qualified
    assert by_qualified["task.tasks.ansible.builtin.template"].kind == "function"


def test_parse_ansible_var_symbols():
    symbols = parse_file(ANSIBLE_VARS_SOURCE, "inventory/group_vars/all.yml", "ansible")
    by_qualified = {symbol.qualified_name: symbol for symbol in symbols}

    assert "app_port" in by_qualified
    assert by_qualified["app_port"].kind == "constant"
    assert "database" in by_qualified
    assert by_qualified["database"].kind == "type"
    assert "database.host" in by_qualified
    assert by_qualified["database.host"].kind == "constant"
