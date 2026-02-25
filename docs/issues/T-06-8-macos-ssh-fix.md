# Task

- user story: [US-06](US-06-inference-server.md)
- type: bug

# Description

**macOS SSH config breaks Ansible container**

When running `deploy.sh` from a Mac, the Ansible container fails because macOS-specific SSH config options (`UseKeychain`) are not supported by OpenSSH on Linux (inside the container).

## Problem

macOS adds `UseKeychain yes` to `~/.ssh/config` for Keychain integration. The container mounts the host's `~/.ssh` directory read-only. OpenSSH inside the container (Debian-based) does not recognize this option and terminates:

```
/root/.ssh/config: line 19: Bad configuration option: usekeychain
/root/.ssh/config: terminating, 1 bad configuration options
```

## Root Cause

SSH resolves `~/.ssh/config` via `getpwuid()` (from `/etc/passwd`), **not** via the `$HOME` environment variable. Setting `HOME=/tmp` in `ansible-run.sh` does not prevent SSH from reading `/root/.ssh/config`. The `sed` cleanup that strips `UseKeychain` from `/tmp/.ssh/config` has no effect because SSH never reads that file.

## Proposed Fix

Use the `-F` flag in `ansible.cfg` to explicitly point SSH to the cleaned config copy:

```ini
ssh_args = -F /tmp/.ssh/config -o ControlMaster=auto -o ControlPersist=60s -o IdentitiesOnly=yes
```

Additionally, `ansible-run.sh` should `touch /tmp/.ssh/config` to ensure the file exists even when the host has no SSH config (e.g. Windows without `~/.ssh/config`).

## Affected Platform

- macOS (confirmed on MacBook M3)
- Windows and Linux are not affected (`UseKeychain` is macOS-only)

## How to Test

1. On a Mac with `UseKeychain yes` in `~/.ssh/config`
2. Run `./scripts/deploy.sh`
3. Verify that the playbook connects successfully without SSH config errors

# Status

A partial fix was attempted in T-06-2 (`sed -i '/UseKeychain/Id'` in `ansible-run.sh`), but it is ineffective because SSH does not read the cleaned copy (see Root Cause above). The fix is committed but untested — no macOS tester currently available.

# Branches

- `feature/T-06-2-ansible-setup` (partial fix committed, untested)

# Acceptance Criteria

- [ ] `deploy.sh` works from macOS without SSH config errors
- [ ] `deploy.sh` still works from Windows and Linux (no regression)
- [ ] No image rebuild required for the fix (config-only change)
