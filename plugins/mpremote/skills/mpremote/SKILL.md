---
name: mpremote
description: Use mpremote to work with attached MicroPython boards over serial on Windows, Linux, WSL2, or Docker. Use for finding boards, forwarding USB with usbipd-win, running MicroPython scripts, copying or removing files and directories, listing device trees, installing packages with mip, or running code from a mounted workspace folder.
---

# Work with MicroPython boards using mpremote

## Choose the terminal and board

1. Use a terminal that can see both the board's serial port and the local files. In a WSL or container workspace, check inside that environment, not just on Windows. A hosted cloud session cannot see a USB board attached to the user's computer; use a session that runs on the machine with device access.
2. Try `mpremote --version` in that terminal. If `mpremote` is not on PATH (`Get-Command mpremote` in PowerShell, `command -v mpremote` in a POSIX shell), try `uvx mpremote --version` and replace `mpremote` with `uvx mpremote` in every example. Do not build `mpremote` from the checkout or install it globally. If neither is available, report that `uv` (which provides `uvx`) or an existing `mpremote` executable is needed in that environment.
3. Run `mpremote connect list`. Match the board by serial number, USB VID:PID, or a port the user has identified. A listed port is not proof that it runs MicroPython. If the board is ambiguous, ask before opening any port. Do not rely on auto-connect picking the first board.
4. Use `connect` with the selected port on every invocation. In the examples below, replace `COM7` with the actual Windows port or Linux path such as `/dev/ttyACM0` or `/dev/ttyUSB0`. On Linux, use a `/dev/serial/by-id/` path when available and unambiguous. Quote paths with spaces. Local paths use the terminal's syntax; MicroPython paths use `/` on all platforms.

Opening raw REPL can interrupt the application even for a filesystem read. Some versions or configurations also soft-reset on the first action. Use `resume` immediately after `connect` if a soft reset must be avoided; it does not prevent interruption. Do not reset or replace boot files as a routine connectivity check. If the port is busy, ask the user to close serial monitors or other sessions using that board. For permission errors on Linux, check the device node's owner/group and the current user's groups; use the site's serial group or per-device udev rule rather than broad permissions or running `mpremote` as root.

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

Use `fs --recursive cp` for directory copies. If `mpremote fs --help` does not list `tree`, or the tree command does not produce a listing, use `fs ls` to walk the requested directories. Confirm successful transfers by listing the destination on the relevant side; compare content when accuracy matters.

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
- `mount` exposes the local folder at `/remote` and makes it the board's working directory for that session. Keep `mount` and the action in the same invocation. `mount ... run ...` still takes a *local* script path relative to the terminal's current directory. The last example instead opens the script via the board's mounted filesystem.
- Mount only the intended project subdirectory. Code on the board can write to the mounted host directory if host permissions allow. Do not use `--unsafe-links`. The mount ends when `mpremote` exits normally; `mount` without an action opens an interactive REPL by default. Use finite scripts for unattended execution, capture output, and report exceptions or timeouts rather than assuming success.

## Install MicroPython packages

```text
mpremote connect COM7 mip install aioble
mpremote connect COM7 mip --no-mpy install aioble
mpremote connect COM7 mip --target /flash/lib install aioble
```

Install only requested packages from trusted sources. The terminal running `mpremote` downloads the package and transfers it to the board; the board does not need internet access. Normally let `mip` find the board's library directory. Use `--target` only when the intended device path is known; use `--no-mpy` to request source files when `.mpy` compatibility is a concern. Verify the install with a scoped device listing or, if running an import is appropriate, `mpremote connect COM7 exec "import aioble; print('import OK')"`.

When chaining commands after a variable-length `fs` or `mip` command, use `+` to end its arguments, for example `mpremote connect COM7 fs ls :/ + run "./app/demo.py"`.

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
