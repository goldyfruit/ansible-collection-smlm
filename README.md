# 🚀 Ansible Collection: goldyfruit.mlm

[![Ansible Collection](https://img.shields.io/badge/ansible-collection-blue.svg)](https://galaxy.ansible.com/goldyfruit/mlm)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/goldyfruit/ansible-collection-smlm.svg)](https://github.com/goldyfruit/ansible-collection-smlm)
[![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen.svg)](https://github.com/goldyfruit/ansible-collection-smlm)

> **Making SUSE Manager Lifecycle Management as easy as ordering pizza! 🍕**

Welcome to the most comprehensive Ansible collection for managing SUSE Multi-Linux Manager (SMLM)! This collection transforms complex system management tasks into simple, declarative playbooks that even your coffee machine could understand. ☕

## 🎯 What's This All About?

SUSE Manager Lifecycle Management (MLM) is powerful, but let's be honest – clicking through web interfaces gets old fast. This collection brings the power of automation to your fingertips, letting you manage activation keys, system groups, and more with the elegance of Ansible.

Think of it as your personal DevOps assistant that never sleeps, never complains, and always remembers to apply security patches! 🛡️

## 🎁 What's In The Box?

### 🛠️ Awesome Features

- **🔐 Multiple Authentication Methods** - Credentials files, explicit auth, you name it!
- **✅ Idempotent Operations** - Run it once, run it a thousand times, same result
- **🧪 Check Mode Support** - Test your changes without breaking anything
- **🔄 Automatic ID/Name Conversion** - We handle the boring stuff for you
- **📊 Comprehensive Error Handling** - Helpful messages, not cryptic errors

## 🚀 Quick Start

### Installation

```bash
# Install from Ansible Galaxy (coming soon!)
ansible-galaxy collection install goldyfruit.mlm

# Or install from source (for the adventurous)
git clone https://github.com/goldyfruit/ansible-collection-smlm.git
cd ansible-collection-smlm
ansible-galaxy collection build --force
ansible-galaxy collection install goldyfruit-mlm-*.tar.gz --force
```

### Setup Your Credentials

Create a credentials file (because nobody likes hardcoding passwords):

```bash
mkdir -p ~/.config/smlm
cat > ~/.config/smlm/credentials.yaml << EOF
default: staging
instances:
  prod:
    url: https://your-suse-manager.example.com
    username: admin
    password: your-super-secret-password
    validate_certs: true

  staging:
    url: https://staging-suse-manager.example.com
    username: staging_admin
    password: staging-password
    validate_certs: false
EOF
```

### Your First Playbook

Let's create something awesome! Here's a playbook that sets up an activation key with all the bells and whistles:

```yaml
---
- name: 🎭 SUSE Manager Automation Magic
  hosts: localhost
  tasks:
    - name: 🔑 Create the ultimate activation key
      goldyfruit.mlm.activationkey:
        key_name: "production-web-servers"
        description: "Production web servers with all the goodies"
        base_channel_label: "sles15-sp4-pool-x86_64"
        usage_limit: 50
        universal_default: false
        entitlements:
          - "monitoring_entitled"
          - "virtualization_host"
        child_channels:
          - "sles15-sp4-updates-x86_64"
          - "sles15-sp4-installer-updates-x86_64"
        packages:
          - "vim"
          - "htop"
          - "curl"
          - "git"
        server_groups:
          - "Production Servers"
          - "Web Servers"
        state: present
      register: activation_key

    - name: 🎉 Celebrate success!
      debug:
        msg: "🚀 Activation key '{{ activation_key.activation_key.key }}' is ready for action!"
```

## 🎯 Dynamic Inventory Usage

### 🔍 Discovering Your Infrastructure

The MLM inventory plugin automatically discovers and organizes your managed systems, making it easy to target specific groups for automation tasks.

#### Basic Inventory Usage

```bash
# List all discovered systems
ansible-inventory -i goldyfruit.mlm.inventory --list

# Get specific host information
ansible-inventory -i goldyfruit.mlm.inventory --host server01.example.com

# Use with ansible commands
ansible all -i goldyfruit.mlm.inventory -m ping

# Run playbooks against discovered systems
ansible-playbook -i goldyfruit.mlm.inventory site.yml
```

#### Configuration Options

Create an inventory configuration file:

```yaml
# inventory_mlm.yml
plugin: goldyfruit.mlm.inventory
url: https://your-suse-manager.example.com
username: admin
password: your-password
# Optional: Use credentials file instead
# instance: default

# Group systems by various attributes
keyed_groups:
  - key: system_groups
    prefix: group
  - key: base_channel
    prefix: channel
  - key: entitlements
    prefix: entitlement

# Create custom groups
groups:
  production: "'prod' in inventory_hostname"
  staging: "'stage' in inventory_hostname"
  web_servers: "'web' in system_groups"
  databases: "'db' in system_groups"

# Add custom host variables
compose:
  ansible_host: network_hostname
  system_id: id
  last_checkin: last_checkin_date
```

#### Using the Inventory in Playbooks

```yaml
---
- name: 🎯 Target systems discovered by MLM inventory
  hosts: group_web_servers  # Systems in "Web Servers" group
  tasks:
    - name: 📊 Show system information
      debug:
        msg: |
          System: {{ inventory_hostname }}
          System ID: {{ system_id }}
          Last Check-in: {{ last_checkin }}
          Groups: {{ system_groups }}

- name: 🔄 Update specific channel systems
  hosts: channel_sles15_sp4_pool_x86_64
  tasks:
    - name: 🚀 Apply patches
      # Your patching tasks here
      debug:
        msg: "Patching {{ inventory_hostname }}"

- name: 🏷️ Work with systems by entitlement
  hosts: entitlement_monitoring_entitled
  tasks:
    - name: 📊 Configure monitoring
      # Your monitoring configuration here
      debug:
        msg: "Configuring monitoring on {{ inventory_hostname }}"
```

#### Advanced Inventory Features

```bash
# Filter systems by specific criteria
ansible-inventory -i inventory_mlm.yml --list | jq '.group_web_servers.hosts'

# Use with ansible-vault for encrypted credentials
ansible-playbook -i inventory_mlm.yml --ask-vault-pass site.yml

# Combine with static inventory
ansible-playbook -i static_inventory -i inventory_mlm.yml site.yml
```

#### Integration with ansible.cfg

```ini
# ansible.cfg
[defaults]
inventory = inventory_mlm.yml
host_key_checking = False
timeout = 30

[inventory]
enable_plugins = goldyfruit.mlm.inventory
```

## 🎨 Advanced Usage Patterns

### 🔄 The GitOps Approach

```yaml
---
- name: 🌊 GitOps-style SUSE Manager management
  hosts: localhost
  vars:
    activation_keys:
      - name: "production-web"
        description: "Production web servers"
        base_channel: "sles15-sp4-pool-x86_64"
        limit: 50
        groups: ["Web Servers", "Production"]
        packages: ["nginx", "php", "mysql-client"]

      - name: "staging-web"
        description: "Staging web servers"
        base_channel: "sles15-sp4-pool-x86_64"
        limit: 10
        groups: ["Web Servers", "Staging"]
        packages: ["nginx", "php"]

  tasks:
    - name: 🔑 Create activation keys from config
      goldyfruit.mlm.activationkey:
        key_name: "{{ item.name }}"
        description: "{{ item.description }}"
        base_channel_label: "{{ item.base_channel }}"
        usage_limit: "{{ item.limit }}"
        packages: "{{ item.packages }}"
        server_groups: "{{ item.groups }}"
        state: present
      loop: "{{ activation_keys }}"
```

### 🚀 The Zero-Touch Deployment

```yaml
---
- name: 🤖 Fully automated environment setup
  hosts: localhost
  tasks:
    - name: 👥 Create system groups
      goldyfruit.mlm.systemgroup:
        name: "{{ item }}"
        description: "Automatically created {{ item }} group"
        state: present
      loop:
        - "Web Servers"
        - "Database Servers"
        - "Load Balancers"
        - "Monitoring Servers"

    - name: 🔑 Create environment-specific activation keys
      goldyfruit.mlm.activationkey:
        key_name: "{{ item.env }}-{{ item.role }}"
        description: "{{ item.env | title }} {{ item.role }}"
        base_channel_label: "{{ item.channel }}"
        usage_limit: "{{ item.limit }}"
        server_groups: ["{{ item.role | title }}"]
        entitlements: "{{ item.entitlements }}"
        packages: "{{ item.packages }}"
        state: present
      loop:
        - {
            env: "prod",
            role: "web",
            channel: "sles15-sp4-pool-x86_64",
            limit: 20,
            entitlements: ["monitoring_entitled"],
            packages: ["nginx", "php"],
          }
        - {
            env: "prod",
            role: "db",
            channel: "sles15-sp4-pool-x86_64",
            limit: 5,
            entitlements: ["monitoring_entitled"],
            packages: ["mysql-server"],
          }
        - {
            env: "staging",
            role: "web",
            channel: "sles15-sp4-pool-x86_64",
            limit: 5,
            entitlements: [],
            packages: ["nginx", "php"],
          }
```

## 🔍 Troubleshooting Guide

### Common Issues & Solutions

#### 🔐 Authentication Problems

**Problem**: `Invalid credentials` error
**Solution**:

```bash
# Check your credentials file
cat ~/.config/smlm/credentials.yaml

# Test with explicit credentials
ansible-playbook -e "mlm_url=https://your-server.com" \
                 -e "mlm_username=admin" \
                 -e "mlm_password=yourpassword" \
                 your-playbook.yml
```

#### 🌐 SSL Certificate Issues

**Problem**: `SSL certificate verification failed`
**Solution**:

```yaml
# In your playbook, disable SSL verification
- name: Create activation key with SSL disabled
  goldyfruit.mlm.activationkey:
    validate_certs: false
    # ... other parameters
```

#### 🔍 Can't Find Activation Keys

**Problem**: `Activation key 'mykey' does not exist`
**Solution**:

```yaml
# List all keys first to see what's available
- name: List all activation keys
  goldyfruit.mlm.activationkey_info:
  register: all_keys

- name: Show all keys
  debug:
    var: all_keys.activation_keys
```

#### 🏷️ Server Group Not Found

**Problem**: `Server group 'My Group' not found`
**Solution**:

```yaml
# Create the group first
- name: Create server group
  goldyfruit.mlm.systemgroup:
    name: "My Group"
    description: "My awesome group"
    state: present

# Then use it in activation key
- name: Use the group
  goldyfruit.mlm.activationkey:
    key_name: "my-key"
    server_groups: ["My Group"]
    state: present
```

## 🎉 Fun Facts & Easter Eggs

- 🚀 This collection was built with 100% pure automation love
- 🤖 It contains exactly 0 hardcoded credentials (we checked!)
- 🔧 The utilities are shared between modules to eliminate code duplication
- 🎯 Every module supports check mode for safe testing
- 🎨 The code follows Python and Ansible best practices religiously
- 🧪 All modules are tested and working (batteries included!)

## 🤝 Contributing

Want to make this collection even more awesome? We'd love your help!

### 🛠️ Development Setup

```bash
# Clone the repository
git clone https://github.com/goldyfruit/ansible-collection-smlm.git
cd ansible-collection-smlm

# Run the tests
ansible-test sanity --python 3.9
ansible-test units --python 3.9
```

### 🎯 What We're Looking For

- 🐛 **Bug fixes** - Found something broken? Fix it!
- ✨ **New features** - More modules, more functionality
- 📚 **Documentation** - Help others understand how to use this
- 🧪 **Tests** - Make sure everything works perfectly
- 🎨 **Code quality** - Clean, readable, maintainable code

### 📝 Contribution Guidelines

1. **Fork the repository** and create your feature branch
2. **Follow the existing code style** - consistency is key!
3. **Add tests** for any new functionality
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description

## 📄 License

This collection is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **SUSE** - For creating an amazing Linux management platform
- **Ansible Community** - For the fantastic automation framework
- **Coffee** - For keeping developers caffeinated during development ☕
- **You** - For using this collection and making it better!

## 📞 Support & Community

- 🐛 **Issues**: [GitHub Issues](https://github.com/goldyfruit/ansible-collection-smlm/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/goldyfruit/ansible-collection-smlm/discussions)
- 📧 **Email**: [gaetan.trellu@suse.com](mailto:gaetan.trellu@suse.com)
- 🐦 **Twitter**: [@goldyfruit](https://twitter.com/goldyfruit)

---

## 🎪 That's a Wrap!

You've made it to the end of our README adventure! 🎉

If you're still reading this, you're clearly as passionate about automation as we are. Why not star this repository, contribute some code, or just say hi? We promise we're friendly!

Remember: **Life's too short for manual deployments!** 🚀

**Happy automating!** 🎭✨

---

_Made with ❤️ and lots of ☕ by the SUSE automation team_

> "In automation we trust, in manual processes we don't!" - Ancient DevOps proverb

<div align="center">
  <img src="https://img.shields.io/badge/Powered%20by-Ansible-red.svg" alt="Powered by Ansible">
  <img src="https://img.shields.io/badge/Made%20with-Python-blue.svg" alt="Made with Python">
  <img src="https://img.shields.io/badge/Status-Awesome-brightgreen.svg" alt="Status: Awesome">
</div>
