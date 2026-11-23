# mpremote

A skill plugin for **MicroPython** device workflows on Windows, Linux,
WSL2, and Docker. It uses the installed `mpremote`, with `uvx mpremote` as the
fallback; it never builds `mpremote` from source.

## Capabilities

- Discover serial ports and identify the intended board before opening it.
- Upload and download files and directories.
- Run host scripts or scripts already on the board.
- Run scripts with a local folder mounted as `/remote`.
- Install requested packages with `mpremote mip install`.
- Inspect ROMFS partitions, build host images, and deploy to a confirmed ROMFS
  partition with explicit approval.
- List files and directory trees; remove only explicitly scoped files/folders.
- List, bind, attach, detach, and unbind a selected Windows USB board with
  `usbipd-win` for WSL2 use.
- Pass a Linux serial node into Docker when the Docker daemon can access it.
- Prepare persistent Linux/WSL serial access with a reviewed one-time setup
  helper instead of repeated per-reset sudo calls.

## Install

Follow the [marketplace installation instructions](../../README.md#use-the-marketplace).
For example:

```sh
copilot plugin marketplace add josverl/mp-agents
copilot plugin install mpremote@mp-agents
```

If VS Code in WSL reports that the selected agent does not support plugin
installation, use the [Copilot CLI WSL workaround](../../README.md#work-around-plugin-installation-errors-in-wsl).

```sh
claude plugin marketplace add josverl/mp-agents
claude plugin install mpremote@mp-agents
```

## Use

Start a new session in an environment that can see the board and your scripts:

> Use mpremote to list the serial ports and help identify my MicroPython board.

> Run my app from a mounted folder without copying it to the board.

> Download /demo/demo.py to a new local file.

Read the full [skill](skills/mpremote/SKILL.md) for command syntax and precautions.
Commands can interrupt the running application. File deletion is irreversible,
and code using a host mount may modify host files. ROMFS deployment replaces
partition contents. Never select a board, reset it, deploy ROMFS, or remove a
directory based on guesswork.

## Persistent serial permissions

The optional [helper](skills/mpremote/scripts/setup_serial_permissions.py) is
the canonical source for all three plugins. mpflash and mpbuild contain
generated, byte-identical copies, checked by CI; none needs another plugin
installed at runtime. Edit only this primary version when maintaining it.

See the [skill's setup instructions](skills/mpremote/SKILL.md#one-time-linuxwsl-serial-permissions).
Preview is unprivileged. With approval, one `sudo -A` invocation installs
device-specific udev rules for all selected USB tty devices. Optional observed
numeric-group enrollment handles WSL reconnect overrides and requires explicit
approval of its broader group access. The helper requires Linux/WSL, Python
3.9+, and active udev 247+. It does not grant raw USB, probe, or container
access through its tty rules.

Setup is host-wide, not tied to mpremote: existing rules work for mpflash
and other serial tools too. Start a new login/agent session after enrollment.
Legacy `99-mpbuild-serial-*` rules and `mpbuild-serial-*` groups remain unchanged
to preserve existing installations. No setup runs during plugin installation.

## Package and validation

The root manifest targets Agent Plugins 1.0; the `.claude-plugin` manifest
supports Claude's plugin format. Both discover the **same** skill directory.
There are no hooks or MCP servers. The bundled Python setup helper runs only
when explicitly selected and approved; device operations still use mpremote.

Shared helper maintenance checks:

```sh
python3 scripts/validate.py --sync
python3 scripts/validate.py
python3 -B -m unittest discover -s test -p 'test_*.py' -v
```

The checks require Python 3.10+; on Windows use `python` instead of `python3`.
The serial-helper safety tests automatically skip outside Linux. None of these checks opens a device,
installs host rules, or invokes sudo.

Structural checks do not prove GUI activation or USB connectivity. See the
[compatibility table](../../README.md#compatibility) for validation scope.

## License

[MIT](../../LICENSE).
