---
name: mpbuild
description: Build custom MicroPython firmware in containers with mpbuild on Linux, macOS, or WSL2 without installing separate compiler toolchains. Use for board and variant builds, forks, frozen Python modules, native module configuration, Docker readiness, and firmware artifact verification; hand off approved device flashing to the mpflash skill.
---

# Build custom MicroPython firmware with mpbuild

## Establish the host, tool, and container runtime

1. Run on Linux, macOS, or WSL2. Native Windows mpbuild execution is not
   currently supported. On Windows, use `wsl --list --verbose` to confirm
   the selected distro is WSL2 and run all build commands inside it.
2. In WSL2, keep the MicroPython repository, custom modules, and build outputs
   on the distro's own storage, such as `~/src/micropython`. Resolve the path
   with `pwd -P` and inspect its filesystem if uncertain. Never build under
   `/mnt/c`, `/mnt/d`, or other Windows-mounted storage. Do not relocate or
   overwrite an existing checkout without permission.
3. Check `command -v mpbuild`, `mpbuild --version`, `mpbuild --help`,
   `mpbuild build --help`, and `mpbuild list --help`. If absent, use
   `uvx mpbuild --version` and substitute `uvx mpbuild` in the examples.
   With approval for a persistent user tool, `uv tool install mpbuild` is
   another option. Do not modify the project's Python environment or install
   host compiler toolchains as routine setup. Approve any needed downloads.
4. Check `docker --version`, the active Docker context, and `docker info`.
   The daemon must be reachable and run Linux containers compatible with
   the selected image. On macOS or Windows/WSL2, Docker Desktop is one option;
   on Linux, Docker Engine is another. A similar virtualization runtime must
   provide a verified compatible Docker CLI/API and checkout bind mounts.
   Do not silently replace `docker` with `podman` or promise untested support.
5. A remote daemon must see the checkout at the path mpbuild mounts. A working
   client command alone does not prove that. Confirm Docker Desktop's WSL
   integration or the daemon-host mount arrangement before building.
   Report daemon, permission, architecture, or mount failures explicitly.
   Do not start services, change groups, install OS packages, or invoke
   privileged containers as a workaround without separate approval.

The container supplies the board's compiler toolchain. Git, the source tree,
the container runtime, and mpbuild/uv are still host prerequisites. Missing
images and source dependencies may need network access and substantial disk
space. Review the selected source and image before executing build scripts.

## Confirm the source and build contract

- Establish the exact checkout/fork, revision, board ID, variant, desired
  custom features, and output location. Ask if the customization is unspecified.
  Prefer a confirmed stable revision unless the user requests a preview or
  development checkout; do not switch an existing checkout silently.
- Inspect `git status --short`, `git describe --tags --always`, and relevant
  board configuration and manifests. Preserve user changes, submodules, and
  existing artifacts. Do not stash, reset, or recursively update every
  submodule as routine setup. mpbuild initializes the selected port's
  dependencies as part of its build; ask first if dirty required submodules
  could be affected.
- If a new checkout is needed, obtain approval and clone to a new native
  filesystem path, for example:

  ```sh
  mkdir -p ~/src
  git clone https://github.com/micropython/micropython.git ~/src/micropython
  cd ~/src/micropython
  ```

- Run from the MicroPython repository root:

  ```sh
  mpbuild list
  mpbuild list esp32
  ```

  Select the exact board ID, its hardware port, and a listed variant from
  that checkout. Do not infer a board from a CPU name or substitute another
  vendor's board. `RPI_PICO2_W` belongs to `rp2`; `ESP32_GENERIC_C6` belongs
  to `esp32`. Those are examples, not defaults.
- Apply this workflow to **any MicroPython port**, but check the installed
  mpbuild's supported container mappings first. Discovery can include ports
  mpbuild cannot build. Unsupported ports need an upstream-supported mapping
  or an explicitly reviewed compatible image; do not claim universal container
  support, invent a build command, or install host toolchains as a fallback.
  `unix`, `windows`, and `webassembly` are special host/runtime targets rather
  than MCU boards; their variants and outputs differ and need no serial setup
  or firmware flashing.
- Explain what will run and download before executing. Building does not need
  a connected board. Review the installed version's device-forwarding behavior;
  use the USB-free workflow below when it would expose unrelated devices or
  device paths that the Docker daemon cannot access.

## Configure custom firmware without dropping existing features

Use the selected port's documented configuration mechanism. Reuse existing
board configuration and manifest patterns. Do not invent compiler flags or
assume Make/CMake arguments are portable across MicroPython ports.

First resolve the **effective original manifest** from the selected port's
Makefile/CMake/configuration, including board and variant overrides. Do not
assume every board has its own manifest or uses the same variable names.
Create a new `custom/my-firmware/` directory **inside the checkout** containing
the requested modules and a manifest that includes that effective original.
For example, when the confirmed original is `ports/<port>/boards/manifest.py`:

```python
include("$(PORT_DIR)/boards/manifest.py")
freeze(".", "my_firmware.py")
```

If the original is board-specific, include its board-specific path instead.
The tested Pico 2 W uses `boards/RPI_PICO2_W/manifest.py`, whereas the tested
ESP32-C6 uses the port-wide `boards/manifest.py`. Other boards and variants
can override either. A port without frozen-manifest support needs its own
documented customization mechanism, not this example.

The include retains the board's standard frozen packages; freezing a manifest
containing only the custom module can silently remove those packages.
Do not bake credentials or sensitive configuration into firmware.

Verify in the **selected port's** build files how to supply the custom
manifest, native modules, output directory, and any feature flags. Both tested
`rp2` and `esp32` Makefile wrappers forward `FROZEN_MANIFEST` to
`MICROPY_FROZEN_MANIFEST` and accept `BUILD`, but this is not a contract for
every port. In mpbuild 1.0.0 an empty positional variant reserves the slot
before extra Make arguments for a base board:

```sh
mpbuild build "$BOARD" "" "BUILD=build-$BOARD-custom" "FROZEN_MANIFEST=$PWD/custom/my-firmware/manifest.py"
```

Set `BOARD` to the exact confirmed ID and use only verified Make assignments.
For a nonempty variant, pass that variant instead of `""` and use a distinct
board-and-variant output directory.
Confirm empty-variant handling in the installed version; do not pass the
first Make assignment where mpbuild expects a variant.

For native C/C++ modules, inspect the port's `USER_C_MODULES` support and
module integration instructions; CMake ports generally need the module's
CMake entry point rather than a guessed directory. Keep custom inputs within
the checkout bind mount, or explicitly verify additional mounts. Host paths
outside that mount are not automatically accessible in the container.

Use a new board-and-variant-specific build directory for changed configurations:
CMake/ESP-IDF caches can retain an old frozen manifest or SDK configuration. Do not assume
passing a new manifest updates a previously configured directory. If cleaning
is needed instead, first inspect `mpbuild clean --help` or `rebuild --help`
and approve removal of only that board/variant's artifacts. mpbuild cleaning
may run as container root; never clean unrelated outputs.

## Build and inspect artifacts

For an approved ordinary build in an environment with suitable device isolation:

```sh
mpbuild build "$BOARD"
```

For an explicitly requested, listed variant:

```sh
mpbuild build "$BOARD" "$VARIANT"
```

Let mpbuild choose the board/variant's container. ARM, RISC-V, ESP-IDF,
ESP8266, and host targets need different toolchains. For `esp32`, mpbuild can
derive the ESP-IDF version from the selected checkout's lockfiles/CI metadata;
do not hard-code an IDF version from another checkout. Use `--build-container` only after checking installed
help and confirming the override has the required toolchain. Record its tag
and image digest/ID; a mutable tag is not a reproducibility guarantee.

Capture full output and propagate failures when teeing logs (`set -o pipefail`
in Bash). Invalid boards or unsupported ports can exit without producing
firmware in some versions. Inspect errors, the actual selected image, build
directory, compilation completion, and new artifact timestamps; an exit code
or an old artifact is not sufficient evidence.

Resolve the artifact from the selected port's deployment instructions and
build output, not a universal filename or extension:

| Target | Artifact/deployment checks |
| --- | --- |
| `rp2`, supported UF2 boards | Board-matched UF2 and its matching bootloader; ELF is useful for debugging. |
| `esp32`, `esp8266` | The board's flash-ready BIN for esptool. For ESP32, use the merged `firmware.bin`, not an arbitrary app/bootloader BIN. Check generated partition/flash-size settings; do not invent offsets. |
| `stm32` | Board-specific DFU/BIN/HEX/ELF as documented for the chosen DFU or debug-probe workflow. |
| Other MCU ports (`samd`, `nrf`, `mimxrt`, etc.) | Follow that board's deployment documentation. Build availability does not establish an mpflash backend. |
| `unix`, `windows`, `webassembly` | Host executable/runtime artifacts and an appropriate host smoke test, not MCU flashing. |

Check that the output is nonempty, newly built, and compatible with the
selected board and backend. Check the requested modules/configuration in generated build
outputs, record `git describe`, dirty status, tool version, image identity,
artifact size and SHA-256, and retain the exact source manifest. Do not claim
that successful compilation proves runtime behavior; test the requested
custom feature on the board after separately approved flashing.

### USB-free builds

mpbuild 1.0.0's command generator adds `/dev/bus/usb/` and all visible
`ttyACM*`/`ttyUSB*` nodes to Docker automatically, even for build-only work.
Do not expose unrelated devices or use `--privileged`. Docker Desktop may
also lack nodes that exist in WSL. Separate building from device operations.

Prefer an installed version with a verified way to disable forwarding.
Otherwise, with explicit approval, the following mpbuild 1.0.0 API workflow
preserves its selected image, source mounts, user, and build commands while
removing only `--device` pairs. Run it from the checkout root after checking
the installed `board_database` and `docker_build_cmd` signatures. The API is
upstream work-in-progress; stop if its command shape or signatures differ.
`uvx --from mpbuild python` was verified to supply mpbuild in its environment.

```sh
uvx --from mpbuild python - "$BOARD" "$VARIANT" "BUILD=$BUILD_DIR" "FROZEN_MANIFEST=$PWD/custom/my-firmware/manifest.py" <<'PY'
from pathlib import Path
import shlex
import subprocess
import sys
from mpbuild import board_database
from mpbuild.build import BUILD_CONTAINERS, docker_build_cmd

board_id, variant, *make_args = sys.argv[1:]
board = board_database(Path.cwd()).boards[board_id]
if board.port.name not in BUILD_CONTAINERS:
    raise RuntimeError(f"mpbuild does not support port {board.port.name}")
command = docker_build_cmd(
    board,
    variant=variant or None,
    extra_args=make_args,
    docker_interactive=False,
)
args = shlex.split(command)
if args[:3] != ["docker", "run", "--rm"]:
    raise RuntimeError("Unexpected mpbuild command; inspect before executing")
filtered = []
i = 0
while i < len(args):
    if args[i] == "--device":
        print("Removing build-only device mapping:", args[i + 1], flush=True)
        i += 2
    else:
        filtered.append(args[i])
        i += 1
if any(arg == "--privileged" or arg.startswith("--device") for arg in filtered):
    raise RuntimeError("Unexpected device access in build command")
print(shlex.join(filtered), flush=True)
subprocess.run(filtered, check=True)
PY
```

Set `BOARD`, `VARIANT` (empty for base), and `BUILD_DIR` to the confirmed
values; this script contains no hard-coded hardware port. Include only Make
arguments supported by that port: omit the example manifest/build assignments
for targets that do not accept them. The same API path was tested for `rp2`
and `esp32`; other targets still require their own configuration checks.
Adapt only the confirmed board, variant, build directory and custom arguments.
Inspect the emitted command before approving the workflow. mpbuild assembles
a shell command internally: avoid source paths with spaces or shell
metacharacters unless that version's quoting has been verified. Do not
interpolate untrusted arguments. This is a build-only adaptation, not an
alternative flashing backend or permission bypass.

## One-time Linux/WSL serial permissions

The bundled helper is generated from mpremote's canonical source and compared
byte-for-byte in CI. Each plugin includes its own standalone copy; no sibling
plugin installation or path is required. Preserve the existing legacy
`mpbuild-serial-*` rule/group names to reuse previously installed permissions.

Skip this section for builds alone, host targets, macOS, Windows flashing,
or when the execution environment already provides persistent device access.
On Linux/WSL, prepare permissions **before** any reset/flash so a returning
serial node does not force another password prompt.

1. Identify only the authorized USB tty nodes without opening them. Inspect
   `id`, node ownership, and `udevadm info`. Confirm an active udev daemon.
   Forwarding into WSL and Windows-side USB binding are separate permissions.
2. Use the existing serial-access group the user belongs to, often `dialout`.
   The bundled [setup helper](scripts/setup_serial_permissions.py) accepts
   multiple exact `--device` nodes and previews the proposed rules without
   sudo or opening a serial port:

   ```sh
   python3 "$SKILL_DIR/scripts/setup_serial_permissions.py" --group dialout --device /dev/ttyACM0 --device /dev/ttyACM1
   ```

   Set `SKILL_DIR` to this installed skill's directory and replace the example
   nodes/group with confirmed values. The helper needs Linux/WSL, Python's
   standard library, and udev 247+; it refuses non-USB tty nodes, absent unique
   serial identities, and unsafe rule values rather than granting broad access.
   If WSL has assigned an otherwise inaccessible numeric group, the preview
   reports it. Other WSL device managers can restore that group after udev
   runs; a successful current-node check does not prove reconnect persistence.
3. After approval of **persistent** device access, install all reviewed rules
   in **one** privileged invocation:

   ```sh
   sudo -A python3 "$SKILL_DIR/scripts/setup_serial_permissions.py" --install --group dialout --device /dev/ttyACM0 --device /dev/ttyACM1
   ```

   It writes separate `/etc/udev/rules.d/99-mpbuild-serial-<identity-hash>.rules`
   files, matches each device's VID/PID/serial regardless of tty numbering,
   sets final group ownership and mode `0660`, reloads rules once, and triggers
   only the selected current tty nodes. Identical existing rules are reused;
   different contents/symlinks are refused, not overwritten silently.
   It grants no raw USB, disk, probe, container, or sudo access.
   For the WSL numeric-group case, explicitly approve the broader group
   access shown by the preview and append `--enroll-observed-group` to both
   preview and installation. In that same sudo invocation the helper creates
   a local group for an unmapped observed ID, if needed, and adds the user to
   it. This grants access to **all** nodes with that group ID, not just the
   matched boards; known privileged and low/system groups are refused.
   It does not make nodes world-writable or try to race another device manager.
4. Reattach/reset only the approved devices and verify the new nodes are
   readable/writable by the normal user. Build and flash without sudo; do not
   perform repeated `sudo chgrp`, run a sudo keepalive, weaken modes to `0666`,
   or create passwordless sudo rules. A firmware changing its VID/PID/serial
   requires a separately reviewed rule for the new identity.
   After group enrollment, use a fresh login/agent session to pick up the
   membership. A finite approved command can instead run immediately with
   `sg CONFIRMED_GROUP -c 'COMMAND'`; this changes only that command's process
   group and must not select a device implicitly.
5. If group enrollment is needed, ask before an administrator adds the user
   to the site's existing serial group, batch it with other approved setup,
   then require a new login session and verify effective group membership.
   The helper does not silently enroll users or grant every serial port.
   If udev is unavailable, explain the limitation and obtain approval for
   the site's supported persistent setup or Windows flashing; do not promise
   one-time setup can work without a running device manager.

Removal is a separate approved operation: remove only the exact managed rule
files, reload udev, and reconnect the affected devices. Do not delete other
rules or revoke unrelated group memberships.

## Hand the exact image to mpflash

Use the [mpflash skill](https://github.com/josverl/mp-agents/blob/main/plugins/mpflash/skills/mpflash/SKILL.md)
for identification, custom firmware registration, approval, flashing, and
post-flash verification. Install/load that plugin separately if it is not
available; this plugin does not bundle it. Use the
[mpremote skill](https://github.com/josverl/mp-agents/blob/main/plugins/mpremote/skills/mpremote/SKILL.md)
for approved backups and scoped runtime queries.

Skip the MCU handoff for host/runtime targets. If mpflash does not implement
the selected board/port/backend, retain the verified build and report that
limitation rather than treating successful compilation as flashing support.

1. Identify exactly one authorized MCU, its current serial/USB identity,
   board ID, variant, and firmware. Ask before interrupting it.
2. Inspect `mpflash add --help` and `flash --help`. Use a dedicated firmware
   directory, then register the actual flash-ready image from its original
   build path. For example, after verifying ESP32-C6 BIN provenance:

   ```sh
   mpflash --dir /path/to/firmware-cache --no-interactive add --path /path/to/micropython/ports/esp32/build-ESP32_GENERIC_C6-custom/firmware.bin --description "Approved custom ESP32-C6 build"
   ```

   Check the resulting database record, custom flag, board/port/version,
   selected filename, and copied file hash. mpflash can infer metadata from
   Git and directory names, not necessarily the image contents. Build-directory
   suffixes and variants can be misparsed. Correctness requires inspecting
   the record rather than assuming inference is accurate.
3. Ensure only one matching custom image is eligible for the chosen board and
   version. Check whether the installed CLI supports `--custom`; never
   substitute `stable`/`preview` and accidentally flash downloaded firmware,
   pass a positional filename to `flash`, or silently rebuild using `--build`.
4. Ask for approval of the exact image/hash, physical device, host/backend,
   bootloader/reset actions, backups, possible data loss, and downloads.
   No erase/format without separate permission; preservation is not guaranteed.
5. Flash only that confirmed target using mpflash's scoped workflow, then
   re-enumerate after bootloader entry/reconnection. For WSL UF2 flashing,
   USB forwarding, bootloader reattachment and a writable mounted UF2 volume
   must all work in that distro; serial forwarding alone is insufficient.
   Use Windows flashing instead only with approval if WSL access cannot
   be maintained. No broad USB mappings, root flashing, or arbitrary mounts.
6. Confirm exactly one flashed board and the returning board's identity.
   Verify `sys.implementation`, `os.uname()`, and the actual custom feature.
   For a frozen module, check its expected marker and that no filesystem copy
   or host mount is supplying the import. Report any mismatch explicitly.

In WSL, a returning serial node can have different ownership/group permissions.
If mpflash wrote the image but reports a reconnection failure, do not immediately
reflash or erase. Re-enumerate the same USB identity, inspect the exact node's
permissions, obtain approval for any scoped correction, and independently
verify its running firmware. Report the failed CLI result separately from a
successful runtime check.

Return any temporarily forwarded USB device to Windows after operations
stop, as described by mpflash/mpremote. Do not claim flashing success from
a disappearing UF2 volume or compilation alone.

## Plugin portability

This standard [Agent Skill](https://agentskills.io/) is shared by portable
and Claude-compatible manifests. Use the available terminal tool; no
provider-specific API is required. Loading instructions grants no terminal,
container, administrator, or device permissions.

[Plugin installation and limitations](../../README.md) |
[mpbuild reference](https://github.com/josverl/mpbuild/blob/main/README.md) |
[MicroPython manifests](https://docs.micropython.org/en/latest/reference/manifest.html) |
[MicroPython native modules](https://docs.micropython.org/en/latest/develop/cmodules.html)
