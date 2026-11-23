---
name: mpremote
description: Use mpremote to work with attached MicroPython boards over serial on Windows, Linux, WSL2, or Docker. Use for finding boards, forwarding USB with usbipd-win, running MicroPython scripts, copying or removing files and directories, listing device trees, installing packages with mip, mounting a workspace, or building, inspecting, and deploying ROMFS images.
---

# Work with MicroPython boards using mpremote

## Choose the terminal and board

1. Use a terminal that can see both the board's serial port and the local files. In a WSL or container workspace, check inside that environment, not just on Windows. A hosted cloud session cannot see a USB board attached to the user's computer; use a session that runs on the machine with device access.
2. Try `mpremote --version` in that terminal. If `mpremote` is not on PATH (`Get-Command mpremote` in PowerShell, `command -v mpremote` in a POSIX shell), try `uvx mpremote --version` and replace `mpremote` with `uvx mpremote` in every example. Do not build `mpremote` from the checkout or install it globally. If neither is available, report that `uv` (which provides `uvx`) or an existing `mpremote` executable is needed in that environment.
3. Run `mpremote connect list`. Match the board by serial number, USB VID:PID, or a port the user has identified. A listed port is not proof that it runs MicroPython. If the board is ambiguous, ask before opening any port. Do not rely on auto-connect picking the first board.
4. Use `connect` with the selected port on every invocation. In the examples below, replace `COM7` with the actual Windows port or Linux path such as `/dev/ttyACM0` or `/dev/ttyUSB0`. On Linux, use a `/dev/serial/by-id/` path when available and unambiguous. Quote paths with spaces. Local paths use the terminal's syntax; MicroPython paths use `/` on all platforms.

Opening raw REPL can interrupt the application even for a filesystem read. Some versions or configurations also soft-reset on the first action. Use `resume` immediately after `connect` if a soft reset must be avoided; it does not prevent interruption. Do not reset or replace boot files as a routine connectivity check. If the port is busy, ask the user to close serial monitors or other sessions using that board. For permission errors on Linux, check the device node's owner/group and the current user's groups; use the site's serial group or per-device udev rule rather than broad permissions or running `mpremote` as root.

## One-time Linux/WSL serial permissions

Skip setup when persistent access already works. Host permissions apply to
mpremote, mpflash, and other serial tools; changing tools does not require
installing the same rules again.

Use the bundled [setup helper](scripts/setup_serial_permissions.py) only for
identified, authorized USB tty devices on Linux/WSL with Python 3.9+ and an
active udev 247+ daemon. It does not open serial ports. Set `SKILL_DIR` to
this installed skill's directory and replace the example nodes/group:

```sh
python3 "$SKILL_DIR/scripts/setup_serial_permissions.py" --group dialout --device /dev/ttyACM0 --device /dev/ttyACM1
```

Preview first and obtain approval for the persistent rules. The selected group
must already contain the invoking user. Batch all approved devices into one
privileged installation:

```sh
sudo -A python3 "$SKILL_DIR/scripts/setup_serial_permissions.py" --install --group dialout --device /dev/ttyACM0 --device /dev/ttyACM1
```

The helper writes VID/PID/serial-scoped udev rules with mode `0660`, reloads
once, and triggers only the selected tty nodes. Identical existing rules are
reused; differing files and symlinks are refused. USB binding/forwarding,
UF2 mounts, raw USB, probes, and container access remain separate concerns.
Never use repeated per-reset `sudo chgrp`, root mpremote, world-writable modes,
sudo keepalives, or passwordless sudo as substitutes.

WSL can restore a foreign numeric group after reconnect. If the preview shows
this, obtain explicit approval and add `--enroll-observed-group` to the preview
and installation commands. The same sudo invocation can create a local group
for that observed ID and enroll the user. This grants access to **all** nodes
with that group ID, not only the listed boards; privileged/low system groups
are refused. Start a new login/agent session afterwards, or use a finite,
explicitly scoped `sg CONFIRMED_GROUP -c 'COMMAND'` test.

Reconnect only the approved devices, re-identify their returning nodes, and
verify normal-user read/write access before continuing. A changed USB identity
needs a newly reviewed rule. Unsupported devices or absent udev require the
site's approved alternative, not broader permissions. Removal of installed
rules or memberships also needs approval and must target only the known setup.

This plugin holds the canonical helper. mpflash and mpbuild bundle generated,
CI-checked identical copies, so each plugin works independently. Existing
`99-mpbuild-serial-*` rule filenames and `mpbuild-serial-*` group names are
intentionally retained for compatibility; do not recreate them under new names.

## List, transfer, and remove files

A leading `:` marks a device path for `fs cp`; the operand without it is local. Other `fs` subcommands operate on the device and also accept `:` for clarity. Check the destination before writing, create missing parent directories, and avoid overwriting existing host or device files unless requested. Copy important files to a new local path before replacing or removing them.

```text
mpremote connect COM7 fs ls :/
mpremote connect COM7 fs --human tree :/
mpremote connect COM7 fs mkdir :/demo
mpremote connect COM7 fs cp "my scripts/demo.py" :/demo/demo.py
mpremote connect COM7 fs cp :/demo/demo.py "demo-from-board.py"
mpremote connect COM7 fs ls :/demo
```

Use `fs --recursive cp` for directory copies. For uploads, create the destination parent on the device first and copy the local directory into that existing parent, for example `mpremote connect COM7 fs --recursive cp "./app" :/demo` creates `/demo/app`. Some mpremote versions fail when copying a flat source directory to a non-existent destination. If `mpremote fs --help` does not list `tree`, or the tree command does not produce a listing, use `fs ls` to walk the requested directories. Confirm successful transfers by listing the destination on the relevant side; compare content when accuracy matters.

Delete only a named path the user intends to remove. Use `rmdir` for empty directories. Before recursive deletion, list the exact subtree and confirm its contents and scope; never remove a filesystem root, the current working directory, or an entire mount. These are separate examples, not a sequence:

```text
mpremote connect COM7 fs rm :/demo/demo.py
mpremote connect COM7 fs rmdir :/empty-demo
mpremote connect COM7 fs --recursive rm :/obsolete-demo
```

## Run MicroPython code

```text
mpremote connect COM7 run "my scripts/demo.py"
mpremote connect COM7 exec "exec(open('/demo/demo.py').read(), {'__name__': '__main__', '__file__': '/demo/demo.py'})"
mpremote connect COM7 mount "./app" run "./app/demo.py"
mpremote connect COM7 mount "./app" exec "exec(open('/remote/demo.py').read(), {'__name__': '__main__', '__file__': '/remote/demo.py'})"
```

- `run` reads a script on the machine running `mpremote`, sends it for execution on the board, and does not install the script. `exec` runs code on the board; in the second example it reads a file already stored there.
- For the two mount examples, the terminal's working directory is the parent of the local `app` folder. `mount "./app"` exposes that folder on the board as `/remote` and sets the board's working directory to `/remote`. Thus the host file `./app/demo.py` appears to the board as `/remote/demo.py`.
- Keep `mount` and the action in the same invocation. `run "./app/demo.py"` reads the **host** path relative to the terminal's working directory, then sends its contents to the board; it does not open `/remote/demo.py`. The `exec` example instead opens the **device** path `/remote/demo.py` through the mounted filesystem. Do not pass `/remote/demo.py` to `run` unless that is also a real path on the host.
- Mount only the intended project subdirectory. Code on the board can write to the mounted host directory if host permissions allow. Do not use `--unsafe-links`. The mount ends when `mpremote` exits normally; `mount` without an action opens an interactive REPL by default. Use finite scripts for unattended execution, capture output, and report exceptions or timeouts rather than assuming success.

## Install MicroPython packages

```text
mpremote connect COM7 mip install aioble
mpremote connect COM7 mip --no-mpy install aioble
mpremote connect COM7 mip --target /flash/lib install aioble
```

Install only requested packages from trusted sources. The terminal running `mpremote` downloads the package and transfers it to the board; the board does not need internet access. Normally let `mip` find the board's library directory. Use `--target` only when the intended device path is known; use `--no-mpy` to request source files when `.mpy` compatibility is a concern. Verify the install with a scoped device listing or, if running an import is appropriate, `mpremote connect COM7 exec "import aioble; print('import OK')"`.

When chaining commands after a variable-length `fs` or `mip` command, use `+` to end its arguments, for example `mpremote connect COM7 fs ls :/ + run "./app/demo.py"`.

## Work with ROMFS

ROMFS is a read-only filesystem stored in a device ROM partition, not the writable device filesystem or the temporary host mount at `/remote`. On supported firmware the first valid ROMFS partition is normally mounted at `/rom` at boot, with `/rom` and `/rom/lib` added to `sys.path`. Supported memory-mapped `.mpy` files can execute directly from flash. ROMFS support and partition configuration vary by board and firmware.

1. Check `mpremote romfs --help` first; if the installed client lacks `romfs`, report that a version supporting it is needed. Do not build mpremote. For an identified board, `mpremote connect COM7 resume romfs query` lists partition indices, sizes, and the first bytes. It can interrupt running code. A report that ROMFS is disabled or no partitions are available means **stop**; do not infer support from the board model or automatically reflash firmware, repartition, or format anything. Some clients report these conditions with exit status zero, so inspect the output, not just the exit code. The header check is not a full integrity check.
2. Build an image on the host without connecting to a board:

   ```text
   mpremote romfs --no-mpy --output "./myapp.romfs" build "./myapp"
   ```

   Choose an output path outside the source directory and check it does not overwrite an existing file. `--no-mpy` leaves source `.py` files uncompiled. Without it, mpremote attempts compilation using the **`mpy_cross` Python package in mpremote's own environment**; if unavailable it warns and retains `.py` files. If bytecode is required, verify the output and use an `mpy_cross` version compatible with the target firmware and native architecture; do not silently install or build tools. Existing `.mpy` files also require compatibility.
3. Before deployment, confirm the board, partition index, image contents and size against `romfs query`, and whether existing ROMFS content needs backing up. Deployment erases/replaces data in the selected partition and may unmount `/rom`; it is not an ordinary file copy. Obtain explicit approval for that overwrite and any reset, and do not deploy if the partition is unknown, the image is too large, or required data cannot be recovered.

   ```text
   mpremote connect COM7 resume romfs --partition 0 deploy "./myapp.romfs"
   ```

   The source can instead be a host directory, built during deployment. Partition `0` is the default; do not assume another partition mounts at `/rom`. After an approved soft reset or reboot, query again and inspect `/rom` with `fs --human tree :/rom` or `fs ls :/rom`. Confirm expected files and `sys.path`; only import modules when executing them is appropriate. A query's valid header alone does not prove that the correct contents were deployed. Report errors and unexpected results.

[MicroPython ROMFS reference](https://docs.micropython.org/en/latest/reference/romfs.html)

## Forward a Windows USB board to WSL2

Use [usbipd-win](https://github.com/dorssel/usbipd-win/wiki/WSL-support) on the Windows host. The examples use the current `attach --wsl` syntax. Keep a WSL2 shell open. Close the Windows program using the selected board before transferring it. An attached board is unavailable to Windows until detached.

From Windows PowerShell:

```powershell
wsl --list --verbose
usbipd list
```

Identify the current bus ID for the intended board. `4-4` is an example, not a default. If `Not shared`, have the user run the following from an **administrator** PowerShell (binding persists across reboots):

```powershell
usbipd bind --busid 4-4
```

From normal Windows PowerShell, attach a `Shared` board and verify it is `Attached`:

```powershell
usbipd attach --wsl --busid 4-4
usbipd list
```

From the target WSL2 terminal, run `lsusb` if available, then `mpremote connect list` (or its `uvx` equivalent). Use the enumerated Linux serial node, not the original COM port or the USB bus ID. If USB is visible but no serial port is listed, check whether the board is in bootloader mode and whether WSL has the appropriate serial driver. Re-list after reconnecting or switching modes; identifiers may change.

After serial operations have stopped, return the board to Windows from normal PowerShell:

```powershell
usbipd detach --busid 4-4
usbipd list
```

Detaching leaves the device shared. If the user asks to revoke sharing too, use `usbipd unbind --busid 4-4` from administrator PowerShell after detaching.

## Use a Linux container

First verify the serial node exists **on the Docker daemon's Linux host**. With Docker Engine running inside the WSL2 distro, attach the board to WSL as above, then pass the node to the container. With native Docker Engine on Linux, use the host's serial node directly. For example, from the project folder on the engine host, with a local engine:

```sh
docker run --rm -it --device=/dev/ttyACM0:/dev/ttyACM0 --mount "type=bind,source=$PWD,target=/workspace,readonly" -w /workspace YOUR_IMAGE sh
```

Replace `YOUR_IMAGE` with an image that has `mpremote` or `uvx`. Run discovery inside the container before using the board. For a non-root container user, add the node's numeric group with `--group-add` if group access is needed. For a dev container, add the same mapping to `runArgs` (or `devices` for Compose) and recreate the container; `docker exec` cannot add a device to an existing container. If unplugging or resetting changes the node, recheck it and recreate the container with the correct mapping. Avoid `--privileged` for routine serial access.

Docker Desktop or a remote Docker context may use a separate daemon environment. A node visible in your WSL distro is not proof that the daemon can map it. If Docker Desktop cannot see it, use [Docker Desktop's USB/IP setup](https://docs.docker.com/desktop/features/usbip/) if supported for that board, or run `mpremote` directly in WSL or Windows instead. `mpremote mount` uses a directory visible **inside the terminal running `mpremote`**; it is separate from Docker's bind mount. The example makes `/workspace` read-only to the container. To copy files from the board and keep them after the container exits, provide a separate writable bind mount for downloads.

## Plugin and skill portability

This is a standard [Agent Skill](https://agentskills.io/) distributed by the `mpremote` plugin in [josverl/mp-agents](https://github.com/josverl/mp-agents). It is not a VS Code extension or MCP server. The instructions work with any compatible agent that has terminal access, including GitHub Copilot and Claude Code; use the available terminal tool rather than assuming a provider-specific tool name. Installation and updates are described in the [plugin README](../../README.md).

Skill discovery does not grant terminal or USB access. Start a session that can reach the board, then ask it to use the `mpremote` skill to list available serial ports. Loading this skill is not permission to run disruptive operations, change USB ownership, or access devices belonging to another user.

[mpremote reference](https://docs.micropython.org/en/latest/reference/mpremote.html) | [Copilot skill setup](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills)
