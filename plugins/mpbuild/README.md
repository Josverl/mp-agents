# mpbuild

A skill plugin for building custom **MicroPython** firmware with
[mpbuild](https://github.com/josverl/mpbuild). Compiler toolchains run in
containers rather than being installed separately on the host.

## Capabilities

- Check the container runtime, source checkout, board, and variant.
- Run an installed mpbuild tool or use `uvx mpbuild`.
- Build a fork, board configuration, frozen Python modules, or approved native
  modules using the toolchain selected by mpbuild.
- Preserve existing source changes and builds; verify fresh firmware artifacts.
- Apply the same workflow to any MicroPython port, checking the installed
  mpbuild's container support and each port's configuration and artifact format.
- Prepare persistent Linux/WSL serial access for approved USB devices with
  a reviewed, one-time setup helper, rather than repeated per-reset sudo calls.
- Hand the exact image to the [mpflash skill](https://github.com/josverl/mp-agents/blob/main/plugins/mpflash/skills/mpflash/SKILL.md)
  for separately approved flashing and verification.

## Requirements and platforms

- Terminal access on **Linux, macOS, or WSL2**. Native Windows execution of
  mpbuild is not currently supported; use WSL2 for the build.
- Docker installed, on PATH, and running Linux containers. A similar runtime
  is suitable only if its Docker CLI/API compatibility, image architecture,
  and bind mounts have actually been verified with the installed mpbuild.
  Do not assume Podman or an arbitrary VM works unchanged.
- A MicroPython Git checkout or fork, Git, writable storage, and network access
  for missing images, source submodules, and frozen package dependencies.
- An existing mpbuild executable, or [uv](https://docs.astral.sh/uv/).
  With approval, install using `uv tool install mpbuild`, or run without a
  persistent installation using `uvx mpbuild`.

**Windows + WSL2:** clone and build inside the distro's own Linux filesystem,
for example `~/src/micropython`. Do not build on `/mnt/c`, `/mnt/d`, or another
Windows-mounted filesystem. Docker Desktop needs integration with that distro.
Copy completed artifacts to Windows only when needed for Windows flashing.

Building needs no MCU connection. Flash on the host that has scoped device
access; a working Docker build does not prove USB access in that container.

## Install and use

Follow the [marketplace instructions](../../README.md#use-the-marketplace):

```sh
copilot plugin marketplace add josverl/mp-agents
copilot plugin install mpbuild@mp-agents
```

```sh
claude plugin marketplace add josverl/mp-agents
claude plugin install mpbuild@mp-agents
```

In VS Code, review and install `mpbuild` in **Chat: Open Customizations**, or
use this [install link](https://vscode.dev/redirect?url=vscode%3A%2F%2Fchat-plugin%2Finstall%3Fsource%3Djosverl%252Fmp-agents%26plugin%3Dmpbuild).
For WSL installation errors, use the
[Copilot CLI workaround](../../README.md#work-around-plugin-installation-errors-in-wsl).
Other marketplace UIs can select `mpbuild` from the same catalog.

Start a new session and ask:

> Use the mpbuild skill to build RPI_PICO2_W with a frozen module in my
> MicroPython checkout using Docker. Preserve its normal networking features.
> Then use mpflash to prepare flashing the resulting UF2; ask before flashing.

With Claude Code, invoke `/mpbuild:mpbuild`.

```sh
copilot plugin update mpbuild@mp-agents
```

```sh
claude plugin marketplace update mp-agents
claude plugin update mpbuild@mp-agents
```

## Permissions and limitations

Installing the plugin installs instructions and an optional Python
[serial permission helper](skills/mpbuild/scripts/setup_serial_permissions.py),
not mpbuild, Docker, toolchains, drivers, or USB permissions. No hooks or
automatic builds, setup, or hardware operations are included. The skill's
optional Python example uses
mpbuild's command generator to run a build without automatic device mappings;
it executes only when explicitly selected and approved.

The permission helper runs on Linux/WSL with Python's standard library and
udev 247+. Preview is unprivileged; an approved installation uses one
`sudo -A python3 ... --install` invocation for all selected devices. It installs
VID/PID/serial-scoped udev rules, uses an existing user-accessible serial group,
and sets mode `0660`. It reloads once and triggers only the selected tty nodes.
No passwordless sudo, keepalive, root flashing, or world-writable access is used.
See [one-time setup](skills/mpbuild/SKILL.md#one-time-linuxwsl-serial-permissions)
for exact commands and separately approved group enrollment.

WSL can restore a foreign numeric group after reconnect even when udev rules
match. The explicit `--enroll-observed-group` option batches local group
creation/enrollment into the same setup invocation. It grants access to all
nodes with those observed group IDs, so the preview requires broader approval.
After enrollment, start a new login/agent session, or run a finite scoped test
using `sg GROUP -c 'COMMAND'`. Do not assume adding a group updates an already
running agent's effective groups.

This helper is a generated copy of mpremote's canonical source. CI rejects
missing or differing copies; each plugin remains independently installable.
Maintainers edit only mpremote's version and run
`python3 scripts/validate.py --sync` to regenerate the bundled copies. Existing
rule contents, filenames, and group names are intentionally unchanged.

Containers execute source build scripts and mount the checkout writable.
Review source and images first. Docker access is powerful; do not enable a
daemon, change groups, install system packages, or use privileged containers
without approval. mpbuild 1.0.0 auto-forwards USB and serial devices; the
[skill](skills/mpbuild/SKILL.md#usb-free-builds) documents how to avoid that for
build-only work, including Docker Desktop's separate device namespace.

Custom manifests should include the original board manifest unless removing
its features is intentional. Native modules, flash layouts, and variants need
board-specific validation. Building is not approval to reset or flash an MCU;
mpflash handles device identification, data-loss approval, and verification.
The original manifest can be port-wide, board-specific, or variant-specific;
the skill resolves it before customizing. It does not require every port to
accept rp2/ESP32 Make arguments or produce UF2. Host targets use host smoke
tests, and unsupported mpbuild ports or mpflash backends are reported explicitly.

## Validation

On 2026-11-22, the skill's workflow was exercised in Ubuntu WSL2 with Docker
Desktop Linux containers, mpbuild 1.0.0, mpflash 1.28.5, and mpremote 1.28.0.

- `python3 scripts/validate.py --sync`: passed.
- `python3 scripts/validate.py`: passed; three plugins, all catalog aliases, and generated helpers.
- `git diff --check`: passed.
- `python3 -B -m unittest discover -s test -p 'test_serial_permissions.py' -v`:
  passed; five tests cover identity scoping, unsafe rule rejection, missing
  USB serials, idempotency/conflicts, and safe observed-group enrollment.
  The Linux CI job runs these tests without devices or privileged operations.
- `mpbuild --version`, `mpbuild --help`, `mpbuild build --help`,
  `mpbuild list --help`, and `mpbuild list rp2`: passed.
- `uvx --from mpbuild python`: ran the
  [USB-free build example](skills/mpbuild/SKILL.md#usb-free-builds) successfully,
  with board `RPI_PICO2_W` and these exact extra arguments:

  ```text
  BUILD=build-RPI_PICO2_W-mpbuild-validation
  FROZEN_MANIFEST=/home/jos/micropython/custom/mpbuild-validation/manifest.py
  ```

The existing native-storage checkout at `/home/jos/micropython` was
`v1.30.0-preview-65-g52b5fbcb4b`, with pre-existing unrelated modifications
preserved. A new manifest included the original Pico 2 W manifest and froze
`mpbuild_validation.py` containing
`BUILD_MARKER = "mp-agents-mpbuild-pico2w-20261122"`.
No host compiler toolchains were installed. The generated command used
`micropython/build-micropython-arm:bookworm`, with automatic `--device` mappings
removed after approval. Compilation completed with `[100%] Built target firmware`.

The container image ID and repository digest were
`sha256:0d80e3aaa94bcc5d268d1ec92e3d19865e17d68d3bc9328f0051b5fb0dde007b`.
The new UF2 was 1,783,808 bytes, with SHA-256
`c4fab7958db4f19f149a2774a50f031317078567dd08ef851dcc5367afb9d577`.
The generated CMake cache and frozen content confirmed the custom manifest
and module, rather than an older build's artifact.

### Pico 2 W flashing and runtime verification

After separate approval, only the Pico's confirmed USB bus was forwarded
using usbipd-win. Its WSL serial node was `/dev/ttyACM0`. The firmware cache
was a dedicated session directory, abbreviated below as `$CACHE`:

```sh
mpflash --dir "$CACHE" --no-interactive add --path /home/jos/micropython/ports/rp2/build-RPI_PICO2_W-mpbuild-validation/firmware.uf2 --description 'mp-agents Pico 2 W frozen marker validation'
mpflash --dir "$CACHE" --no-interactive flash --serial /dev/ttyACM0 --board RPI_PICO2_W --port rp2 --version v1.30.0-preview --custom --method uf2 --bootloader mpy --no-erase --no-format
mpflash --dir "$CACHE" --no-interactive list --serial /dev/ttyACM0 --json --no-progress --no-reset
```

Registration passed: exactly one custom `rp2` record for `RPI_PICO2_W`,
version `v1.30.0-preview`, build 65; its copied UF2 hash matched the build.
mpflash entered the bootloader, mounted `/media/RP2350`, copied that image,
and unmounted the volume. **The flash command exited 1**: its post-copy
reconnection failed, and it reported no boards flashed. This is not recorded
as a clean mpflash CLI pass.

The returning device node again belonged to a group unavailable to the
current user. With explicit permission, only that Pico node's group was
changed to `dialout`; no root flashing or persistent permission rules were
used. Independent verification then passed: mpflash reported `RPI_PICO2_W`,
`rp2`, ARM, and `1.30.0-preview`, build `preview.65.g52b5fbcb4b.dirty`.
The following scoped mpremote check also passed:

```sh
mpremote connect /dev/ttyACM0 resume exec 'import sys, os; import mpbuild_validation; print(sys.implementation); print(os.uname()); print("BUILD_MARKER:", mpbuild_validation.BUILD_MARKER); assert mpbuild_validation.BUILD_MARKER == "mp-agents-mpbuild-pico2w-20261122"; assert sys.implementation._build == "RPI_PICO2_W"; assert os.uname().release == "1.30.0-preview"; assert os.listdir("/") == []; import network, bluetooth, aioble; print("FROZEN_IMPORT_AND_STANDARD_FEATURES_OK"); print("FILESYSTEM:", os.listdir("/")); print("SYS_PATH:", sys.path)'
```

The filesystem was empty both before and after flashing, and `sys.path` was
`['', '.frozen', '/lib']`, with no host mount. Thus the marker came from the
custom frozen firmware, not a copied Python file. Standard networking and
Bluetooth imports passed; actual radio communication was not tested.
No erase, format, or firmware download was performed.
The temporary USB auto-attach process was stopped, the UF2 volume was no
longer mounted, and the Pico was detached from WSL and verified present on
Windows again. Its existing USB sharing configuration was left unchanged.

These paths and serial ports are test observations, not user defaults.
The workflow was executed with terminal tools; client plugin installation
and model-driven skill activation were not tested. Native Linux, macOS,
alternative container runtimes, boards other than the two recorded here, and the RISC-V variant remain
untested. WSL serial permissions and USB reattachment must be checked after
every boot-mode transition.

### ESP32-C6 and persistent-permission validation

The generalized workflow also passed on the attached `ESP32_GENERIC_C6`
in Ubuntu WSL2 on 2026-11-22. A clean detached worktree at the same commit,
`52b5fbcb4b`, preserved the existing checkout's custom partition configuration
without using it for this flash. The validation build used the standard ESP32-C6
configuration and a manifest including `$(PORT_DIR)/boards/manifest.py`, with
the frozen marker `mp-agents-mpbuild-esp32c6-20261122`.

The port-neutral USB-free API example ran with:

```text
BOARD=ESP32_GENERIC_C6
VARIANT=
BUILD=build-ESP32_GENERIC_C6-mpbuild-validation
FROZEN_MANIFEST=/home/jos/micropython-mpbuild-validation/custom/mpbuild-validation/manifest.py
```

mpbuild selected `espressif/idf:v5.5.5`, repository digest
`sha256:a9231d0697ab8f7517cc072e93b7c83e04907bfbfba80b6440d7dbbf90665cf2`.
The generated command removed automatic USB/tty mappings while retaining the
worktree's common Git-directory mount. Container compilation passed and produced
the flash-ready merged `firmware.bin`: 2,007,472 bytes, SHA-256
`f8e75ee5a3d0770c44e52bf440689a0fb7f728cb311f7f1b7be9df3e0484ab11`.
Build warnings included the upstream `XTAL_FREQ_AUTO` Kconfig assignment and
Make jobserver availability; neither prevented the build. No host toolchain
installation was needed.

Permission setup was tested on both the Pico and ESP32-C6. A rule-only first
attempt applied successfully to existing nodes but **failed the reconnect
test**: WSL restored numeric group 984 on both nodes. The helper now previews
that case and supports explicit observed-group enrollment. The complete setup
was installed with this single combined invocation:

```sh
sudo -A python3 plugins/mpbuild/skills/mpbuild/scripts/setup_serial_permissions.py --install --group dialout --enroll-observed-group --device /dev/ttyACM0 --device /dev/ttyACM1
```

It reused the two individually scoped rules, created local group
`mpbuild-serial-984`, and enrolled the invoking user after separate approval.
Reattachment tests confirmed access to both returning nodes with group 984.
Because the agent's existing login did not pick up new memberships, finite
board commands ran with `sg mpbuild-serial-984 -c 'COMMAND'`. These commands
required no sudo or group password. New login/agent sessions inherit the
membership normally. No repeated per-node `chgrp` was needed.

After exact-image approval and the user's decision not to back up device files,
registration and device operations used these commands, with `$CACHE` referring
to a dedicated firmware directory. Flashing and device queries ran inside
the scoped `sg` process; registration required no device access:

```sh
mpflash --dir "$CACHE" --no-interactive add --path /home/jos/micropython-mpbuild-validation/ports/esp32/build-ESP32_GENERIC_C6-mpbuild-validation/firmware.bin --description 'mp-agents port-neutral ESP32-C6 frozen marker validation'
mpflash --dir "$CACHE" --no-interactive flash --serial /dev/ttyACM0 --board ESP32_GENERIC_C6 --port esp32 --version v1.30.0-preview --custom --method esptool --bootloader auto --no-erase --no-format
mpflash --dir "$CACHE" --no-interactive list --serial /dev/ttyACM0 --json --no-progress --no-reset
```

All three passed. Exactly one custom BIN record was eligible, and its cached
hash matched the build. esptool detected 16 MB physical flash, updated the
image's flash parameters, verified the written data hash, and reset the MCU.
mpflash reported **one flashed board**, `ESP32_GENERIC_C6`, MicroPython
`1.30.0-preview`, build `preview.65.g52b5fbcb4b`. Normal firmware-sector erasure
during programming occurred; no full-chip erase or filesystem format was
requested. No firmware download or root flashing was performed.

Independent scoped mpremote verification passed:

```sh
mpremote connect /dev/ttyACM0 resume exec 'import sys, os; import mpbuild_validation; print(sys.implementation); print(os.uname()); print("BUILD_MARKER:", mpbuild_validation.BUILD_MARKER); assert mpbuild_validation.BUILD_MARKER == "mp-agents-mpbuild-esp32c6-20261122"; assert sys.implementation._build == "ESP32_GENERIC_C6"; assert os.uname().release == "1.30.0-preview"; assert "g52b5fbcb4b" in os.uname().version; files = os.listdir("/"); print("FILESYSTEM:", files); assert "mpbuild_validation.py" not in files; assert "mpbuild_validation.mpy" not in files; assert "boot.py" in files and "issue19942.py" in files; assert "lib" not in files; import network, bluetooth, aioespnow, umqtt.simple; print("FROZEN_IMPORT_AND_STANDARD_FEATURES_OK"); print("SYS_PATH:", sys.path)'
```

The exact marker came from frozen firmware: no filesystem module or host mount
provided it. Existing device files remained present; mpflash also wrote its
normal `board_info.toml`. Networking/Bluetooth package imports passed; radio
communication was not tested. The Pico was not reflashed during this test.
The temporary ESP32-C6 auto-attach process was stopped, both USB devices were
detached from WSL, and Windows serial enumeration confirmed their return.
The approved udev rules and group enrollment remain installed for future use.

## License

[MIT](../../LICENSE).
