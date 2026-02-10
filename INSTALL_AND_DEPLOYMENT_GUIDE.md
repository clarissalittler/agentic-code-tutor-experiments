# Code Tutor Installation, Usage, and Deployment Guide

This guide is intentionally detailed and operational.
It covers:

1. Single-user install and daily usage.
2. Shared Linux server install as `root` (recommended for key lock-down).
3. Faculty user-space executable sharing (testing-only scenario).


## 1. Single-User Install and Usage

### 1.1 Prerequisites

- OS: Linux/macOS (Windows via WSL is recommended).
- Python: 3.9+.
- Git.
- Network egress to your LLM provider endpoint.
- Provider API key:
  - Anthropic (`ANTHROPIC_API_KEY` style key), or
  - OpenAI-compatible provider key.

Check prerequisites:

```bash
python3 --version
git --version
```


### 1.2 Clone and install

```bash
git clone https://github.com/clarissalittler/agentic-code-tutor-experiments.git
cd agentic-code-tutor-experiments

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
```

Verify the CLI:

```bash
code-tutor --help
code-tutor info
```


### 1.3 First-time setup

Run setup:

```bash
code-tutor setup
```

You will be prompted for:

- Provider (`anthropic` or `openai_compatible`).
- API key.
- Model.
- Optional base URL (for OpenAI-compatible).
- Experience level.
- Question style.
- Focus areas.
- Logging preferences.

Config location (default):

```text
~/.config/code-tutor/config.json
```


### 1.4 Daily command usage

Review one file:

```bash
code-tutor review path/to/file.py
```

Review a directory:

```bash
code-tutor review path/to/project
code-tutor review --no-recursive path/to/project
```

Teach-me mode:

```bash
code-tutor teach-me
```

Roguelike mode:

```bash
code-tutor roguelike generate "binary search" --language Python --type implementation
code-tutor roguelike list
code-tutor roguelike show <run-id>
code-tutor roguelike hint <run-id>
code-tutor roguelike submit <run-id>
code-tutor roguelike archive <run-id>
```

Alias (same commands, legacy name):

```bash
code-tutor exercise list
```

Proof mode:

```bash
code-tutor proof review path/to/proof.md
code-tutor proof teach --domain "real analysis"
code-tutor proof info
```

Config / diagnostics:

```bash
code-tutor config
code-tutor export-logs
code-tutor export-logs --clear
```


### 1.5 Upgrade and maintenance

```bash
cd agentic-code-tutor-experiments
git pull
source .venv/bin/activate
pip install -e ".[dev]"

ruff check src tests
pytest -q
```


### 1.6 Uninstall (single user)

```bash
deactivate
rm -rf .venv
```

Optional config/log cleanup:

```bash
rm -rf ~/.config/code-tutor
rm -rf ~/code-tutor-exercises
```


## 2. Shared Linux Server Install as root (Recommended)

This section is for a real multi-student/shared-host deployment where API key exposure should be minimized.

### 2.1 Security model

- Install app once in `/opt/code-tutor`.
- Run the CLI as a dedicated service account (example: `code-tutor-svc`).
- Keep API key only in service account config.
- Grant students command access via `sudo` rule, not file read access to the key.
- Set `api_key_locked: true` so env vars cannot override key.


### 2.2 Create service account and install path

As `root`:

```bash
useradd --system --create-home --home-dir /var/lib/code-tutor --shell /bin/bash code-tutor-svc
mkdir -p /opt/code-tutor
chown root:root /opt/code-tutor
chmod 755 /opt/code-tutor
```


### 2.3 Deploy code and venv in /opt

As `root`:

```bash
cd /opt/code-tutor
git clone https://github.com/clarissalittler/agentic-code-tutor-experiments.git app
cd app

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
deactivate
```

Set ownership:

```bash
chown -R root:root /opt/code-tutor/app
```


### 2.4 Create locked service config

Create config directory owned by service user:

```bash
mkdir -p /var/lib/code-tutor/.config/code-tutor
chown -R code-tutor-svc:code-tutor-svc /var/lib/code-tutor/.config
chmod 700 /var/lib/code-tutor/.config
chmod 700 /var/lib/code-tutor/.config/code-tutor
```

Create `/var/lib/code-tutor/.config/code-tutor/config.json`:

```json
{
  "config_version": 2,
  "provider": "anthropic",
  "api_key": "REPLACE_WITH_REAL_KEY",
  "api_key_locked": true,
  "model": "claude-sonnet-4-5",
  "base_url": "",
  "experience_level": "intermediate",
  "exercises_dir": "/var/lib/code-tutor/exercises",
  "preferences": {
    "question_style": "socratic",
    "verbosity": "medium",
    "focus_areas": ["design", "readability"]
  },
  "logging": {
    "enabled": true,
    "log_interactions": true,
    "log_api_calls": false,
    "redact_content": true,
    "allow_unredacted": false
  }
}
```

Protect key file:

```bash
chown code-tutor-svc:code-tutor-svc /var/lib/code-tutor/.config/code-tutor/config.json
chmod 600 /var/lib/code-tutor/.config/code-tutor/config.json
mkdir -p /var/lib/code-tutor/exercises
chown -R code-tutor-svc:code-tutor-svc /var/lib/code-tutor/exercises
chmod 700 /var/lib/code-tutor/exercises
```


### 2.5 Expose command to students via sudoers

Assume student Unix group is `students`.

Create `/etc/sudoers.d/code-tutor` using `visudo -f /etc/sudoers.d/code-tutor`:

```text
Cmnd_Alias CODE_TUTOR = /opt/code-tutor/app/.venv/bin/code-tutor *
%students ALL=(code-tutor-svc) NOPASSWD: CODE_TUTOR
Defaults!CODE_TUTOR !setenv
```

Create wrapper `/usr/local/bin/code-tutor-shared`:

```bash
cat >/usr/local/bin/code-tutor-shared <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec sudo -u code-tutor-svc /opt/code-tutor/app/.venv/bin/code-tutor "$@"
EOF
chmod 755 /usr/local/bin/code-tutor-shared
```

Student usage:

```bash
code-tutor-shared info
code-tutor-shared review path/to/file.py
code-tutor-shared roguelike list
```


### 2.6 Operational notes for root-managed deployment

- Do not run `code-tutor-shared setup` in student sessions.
- Rotate key by editing service config as root/service user.
- Keep logging redacted unless you have explicit policy and consent.
- All student activity in this model runs under service account storage locations.


### 2.7 Why this is safer

- Students do not need read access to the API key file.
- `api_key_locked: true` prevents env-var key override.
- Key does not appear in world-readable wrapper scripts.
- Access is centrally revocable via sudoers/group membership.


## 3. Faculty User-Space Executable Sharing (Testing-only)

This scenario is possible but less secure.
Use it only when root-managed deployment is unavailable and you accept key-exposure risk.

### 3.1 Install under faculty account

As faculty user (example username `prof_a`):

```bash
mkdir -p ~/apps
cd ~/apps
git clone https://github.com/clarissalittler/agentic-code-tutor-experiments code-tutor
cd code-tutor

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
deactivate
```


### 3.2 Create faculty wrapper command

```bash
mkdir -p ~/bin
cat >~/bin/code-tutor-faculty <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /home/prof_a/apps/code-tutor/.venv/bin/code-tutor "$@"
EOF
chmod 755 ~/bin/code-tutor-faculty
```

Adjust `/home/prof_a/...` to your actual path.


### 3.3 Make executable reachable to test users

If users can already traverse your home dir, share `~/bin/code-tutor-faculty` path directly.

If not, grant ACLs to selected users:

```bash
setfacl -m u:student1:rx /home/prof_a
setfacl -R -m u:student1:rx /home/prof_a/apps/code-tutor
setfacl -m u:student1:rx /home/prof_a/bin
setfacl -m u:student1:rx /home/prof_a/bin/code-tutor-faculty
```

Repeat for each student account.


### 3.4 Two ways students can run it

Option A (better): each student keeps their own API key/config.

- Student runs:

```bash
/home/prof_a/bin/code-tutor-faculty setup
/home/prof_a/bin/code-tutor-faculty review my_file.py
```

- Config is stored in student home by default.
- No key sharing through faculty config.

Option B (testing-only): force shared faculty config with `--config-dir`.

- Wrapper example:

```bash
exec /home/prof_a/apps/code-tutor/.venv/bin/code-tutor --config-dir /home/prof_a/shared-config "$@"
```

- Important: if students can run with that shared config, they can usually read that key material too.
- `api_key_locked` prevents edits/overrides, but does not make a readable file secret.


### 3.5 Recommendation for faculty user-space testing

- Prefer Option A.
- If Option B is required, use a throwaway/low-limit key.
- Rotate that key frequently.
- Move to root-managed service-account deployment for real usage.


## 4. Troubleshooting Checklist

Command not found:

```bash
which code-tutor
echo $PATH
```

Wrong Python environment:

```bash
which python3
which pip
python3 -c "import code_tutor; print(code_tutor.__file__)"
```

Config confusion:

```bash
code-tutor config
code-tutor --config-dir /path/to/config config
```

Provider/network failures:

- Verify outbound network to provider API.
- Check base URL for OpenAI-compatible provider.
- Check model id is supported by provider.

Permission errors on shared hosts:

- Verify ownership and modes on config and exercises directories.
- Verify sudoers entry syntax via `visudo -c`.


## 5. Quick Decision Table

- Need best shared-server key protection: use Section 2 (root + service account + sudoers).
- Need quick test from faculty home without root: use Section 3 (Option A preferred).
- Need normal personal workstation usage: use Section 1.
