# SUSE Multi-Linux Manager Inventory Plugin

This document provides comprehensive documentation for the SUSE Multi-Linux Manager (MLM) inventory plugin, which allows you to dynamically source hosts from a SUSE Multi-Linux Manager server for use in your Ansible playbooks.

## Overview

The MLM inventory plugin connects to a SUSE Multi-Linux Manager server via its API, retrieves information about registered systems, and creates an Ansible inventory from this data. This allows you to:

- Automatically discover all systems managed by your MLM server
- Filter systems based on various criteria (patch status, system groups, etc.)
- Group systems based on their properties
- Create custom host variables using Jinja2 expressions

## Installation

This plugin is part of the `goldyfruit.mlm` collection. To use it, ensure the collection is installed:

```bash
ansible-galaxy collection install goldyfruit.mlm
```

## Configuration File

The MLM inventory plugin uses a YAML configuration file that must end with `mlm.yml` or `mlm.yaml`. A typical configuration file looks like this:

```yaml
---
plugin: goldyfruit.mlm.mlm

# Connection details (only if ~/.config/smlm/credentials.yaml doesn't exist)
url: "https://mlm.example.com"
username: "admin"
password: "password"
validate_certs: true

# Filtering and grouping
filters:
  status: active
  patch_status: needs_patches
  system_groups:
    - web_servers
    - database_servers

group_by:
  - patch_status
  - system_groups

# Custom variables
compose:
  ansible_host: "ip | default(hostname, true)"
  needs_reboot: "patch_status == 'needs_reboot'"
```

## Usage

### Basic Usage

To use the inventory plugin with a playbook:

```bash
ansible-playbook -i /path/to/mlm.yml your_playbook.yml
```

To list hosts from the dynamic inventory:

```bash
ansible-inventory -i /path/to/mlm.yml --list
```

### Environment Variables

Instead of hardcoding credentials in the inventory file, you can use environment variables:

```bash
export MLM_URL="https://your-mlm-server.example.com"
export MLM_USERNAME="your-username"
export MLM_PASSWORD="your-password"

ansible-playbook -i /path/to/mlm.yml your_playbook.yml
```

## Configuration Options

### Connection Settings

| Option           | Description                            | Default | Environment Variable |
| ---------------- | -------------------------------------- | ------- | -------------------- |
| `url`            | URL of the MLM server                  | -       | `MLM_URL`            |
| `username`       | Username for authentication            | -       | `MLM_USERNAME`       |
| `password`       | Password for authentication            | -       | `MLM_PASSWORD`       |
| `validate_certs` | Whether to validate SSL certificates   | `true`  | -                    |
| `timeout`        | Timeout in seconds for API requests    | `60`    | -                    |
| `retries`        | Number of retry attempts for API calls | `3`     | -                    |

### Cache Settings

| Option             | Description                              | Default                                |
| ------------------ | ---------------------------------------- | -------------------------------------- |
| `cache`            | Enable/disable caching of inventory data | `true`                                 |
| `cache_plugin`     | Cache plugin to use                      | `jsonfile`                             |
| `cache_timeout`    | Cache duration in seconds                | `3600` (1 hour)                        |
| `cache_connection` | Path to the cache connection file        | `~/.ansible/tmp/ansible_mlm_inventory` |
| `cache_prefix`     | Prefix to use for the cache file         | `mlm`                                  |

### Filtering Options

The `filters` option allows you to filter systems based on various criteria. All filters are applied as AND conditions (all must match).

```yaml
filters:
  status: active # 'active', 'inactive', or 'all'
  patch_status: needs_patches # 'up_to_date', 'needs_patches', 'needs_reboot', or 'all'
  system_groups: # Filter by system group membership
    - web_servers
    - production
```

### Grouping Options

The `group_by` option allows you to create Ansible inventory groups based on system properties.

```yaml
group_by:
  - patch_status # Creates groups like 'patch_status_needs_patches'
  - system_groups # Ensures systems are added to their respective groups
```

Note: Systems are always added to their respective system groups regardless of the `group_by` configuration to ensure groups are exposed.

### Custom Variables

The `compose` option allows you to create custom host variables using Jinja2 expressions:

```yaml
compose:
  ansible_host: "ip | default(hostname, true)"
  registration_date: "registration_date | string"
  needs_reboot: "patch_status == 'needs_reboot'"
  has_patches: "errata_count > 0"
```

### Field Mappings

You can customize the field mappings to control how API response fields are mapped to inventory variables:

```yaml
field_mappings:
  system:
    id: "id"
    name: "name"
    hostname: "hostname"
    active: "active"
    registration_date: ["created", "registered", "registrationDate"]
    last_checkin: "lastCheckin"
    last_boot: "lastBoot"
```

## Inventory Structure

The MLM inventory plugin creates the following inventory structure:

### Groups

- `mlm_systems`: All systems from MLM
- `patch_status_<status>`: Systems grouped by patch status (e.g., `patch_status_needs_patches`, `patch_status_needs_reboot`, `patch_status_up_to_date`)
- System groups: Systems are automatically added to their respective groups (e.g., `web_servers`, `k8s`)

All group names are automatically sanitized to ensure they are valid Ansible group names:

- Converted to lowercase
- Spaces and special characters replaced with underscores
- Names start with a letter or underscore

### Host Variables

Each host in the inventory has the following variables:

- `id`: System ID in MLM
- `hostname`: System hostname
- `system_name`: System name in MLM
- `active`: Whether the system is active
- `patch_status`: Patch status (up_to_date, needs_patches, needs_reboot)
- `errata_count`: Number of available errata (patches)
- `registration_date`: Date when the system was registered
- `groups`: List of system groups the system belongs to
- Any custom variables defined in the `compose` section

## Examples

### Minimal Configuration

```yaml
plugin: goldyfruit.mlm.mlm
url: "https://mlm.example.com"
username: "admin"
password: "password"
```

### Configuration with Filtering and Grouping

```yaml
plugin: goldyfruit.mlm.mlm
url: "https://mlm.example.com"
username: "admin"
password: "password"
filters:
  status: active
  patch_status: needs_patches
  system_groups:
    - web_servers
group_by:
  - patch_status
  - system_groups
```

### Using System Groups in Playbooks

Systems are automatically added to their respective groups, allowing you to target them directly:

```yaml
# If a system belongs to a 'web_servers' group in MLM:
- name: Update web servers
  hosts: web_servers
  tasks:
    - name: Update packages
      ansible.builtin.package:
        name: "*"
        state: latest
```

### Using Patch Status Groups

```yaml
- name: Patch systems that need updates
  hosts: patch_status_needs_patches
  tasks:
    - name: Update packages
      ansible.builtin.package:
        name: "*"
        state: latest
```

### Using Reboot Status for Maintenance Windows

```yaml
- name: Reboot systems that require it after patching
  hosts: patch_status_needs_reboot
  tasks:
    - name: Reboot systems
      ansible.builtin.reboot:
        msg: "Rebooting for required patches"
        reboot_timeout: 300
```

### Filtering for Maintenance Workflows

```yaml
# inventory_reboot_only.yml - Only get systems that need reboot
plugin: goldyfruit.mlm.mlm
url: "https://mlm.example.com"
username: "admin"
password: "password"
filters:
  status: active
  patch_status: needs_reboot
  system_groups:
    - production
```

Use this configuration for targeted reboot operations:

```bash
ansible-playbook -i inventory_reboot_only.yml reboot_playbook.yml
```

## Troubleshooting

### Cache Issues

If you encounter issues with cached data, you can disable caching:

```yaml
plugin: goldyfruit.mlm.mlm
url: "https://mlm.example.com"
username: "admin"
password: "password"
cache: false
```

### SSL Certificate Issues

If you're using self-signed certificates for testing:

```yaml
plugin: goldyfruit.mlm.mlm
url: "https://mlm.example.com"
username: "admin"
password: "password"
validate_certs: false # Only use in testing environments
```

### Common Mistakes

❌ **Do not run the inventory configuration file as a playbook**:

```bash
# This will fail with "A playbook must be a list of plays" error
ansible-playbook examples/inventory/mlm.yml
```

The inventory configuration file is not a playbook - it's a configuration file for the inventory plugin.

## Related Documentation

- [Ansible Inventory Plugins Documentation](https://docs.ansible.com/ansible/latest/plugins/inventory.html)
- [SUSE Multi-Linux Manager API Documentation](https://documentation.suse.com/suma/5.0/api/suse-manager/api/index.html)
