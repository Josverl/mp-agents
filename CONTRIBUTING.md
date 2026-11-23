# Contributing

Focus contributions on MicroPython workflows. Support multiple clients without
duplicating shared skill content or excluding otherwise compatible tools.
Prefer Python scripts over Node.js scripts for repository automation. Keep
validation and synchronization dependency-free where practical.

## Add or change a plugin

1. Create `plugins/<name>/plugin.json` using Agent Plugins 1.0. Include a stable
   kebab-case name, version, description, repository URL, and license.
2. Add a `.claude-plugin/plugin.json` with matching metadata for Claude support.
3. Put shared skills in `skills/<skill-name>/SKILL.md` with matching `name` and
   descriptive `description` frontmatter. Keep resource links relative so the
   whole plugin can move between hosts.
4. Include a README describing installation, requirements, supported tasks,
   permissions, and limitations, plus a versioned CHANGELOG.
5. Add the plugin to the root `marketplace.json`. Sources are relative to the
   repository root, not to the catalog's own directory.
6. Update the plugin table in the repository README and run:

   ```sh
   python3 scripts/validate.py --sync
   python3 scripts/validate.py
   ```

For released plugins, bump versions in both plugin manifests and the catalog
together, and add a changelog entry. Keep the initial version while preparing
an unreleased first release.

## Shared serial-permission helper

The canonical implementation is
[`plugins/mpremote/skills/mpremote/scripts/setup_serial_permissions.py`](plugins/mpremote/skills/mpremote/scripts/setup_serial_permissions.py).
Do not edit the bundled copies in mpflash or mpbuild. After editing the primary
version, generate and validate all copies:

```sh
python3 scripts/validate.py --sync
python3 scripts/validate.py
python3 -B -m unittest discover -s test -p 'test_*.py' -v
```

Commit the primary script and both generated copies together. The ordinary
validator never repairs drift: CI rejects missing files or any byte difference.
The sync command also updates both marketplace catalog aliases. Runtime users
need only their selected plugin; scripts never import from sibling installs.

To run only the safety suite against the primary helper:

```sh
python3 -B -m unittest discover -s test -p 'test_serial_permissions.py' -v
```

These tests automatically skip on non-Linux systems. They do not access devices
or install rules.
Use Python 3.10 or newer; on Windows, substitute `python` for `python3`.

Catalog aliases are generated from the root `marketplace.json`; commit all
three catalogs and do not maintain different plugin lists per client.

Keep existing rule contents, filenames, and group names compatible when moving
or sharing the helper; its legacy `mpbuild` names are not a reason to reinstall
host permissions.

## Validation and safety

Run the dependency-free structural check before submitting a change. Where
available, also validate and install with both Copilot and Claude, and record
which clients and hardware workflows were actually tested. Do not claim runtime
compatibility based only on JSON validation.

Keep device and host operations explicitly scoped. Do not auto-select ambiguous
boards, build mpremote, flash firmware, delete broad trees, install unnecessary
tools, or require unrestricted container privileges. Ask users before disruptive
operations. Never include credentials, personal serial numbers, or device backups.

Plugins with hooks, MCP servers, or executable helpers need clear documentation
of what runs and where. Do not enable plugins or execute hardware tests for users
merely because they cloned the marketplace.

Use issues for proposed changes and pull requests for contributions. Include the
exact validation commands and their results in the pull request description.
