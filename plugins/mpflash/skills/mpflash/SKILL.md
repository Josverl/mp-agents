---
name: mpflash
description: Use mpflash to identify microcontrollers, download MicroPython firmware, and flash or update supported boards on Windows, Linux, macOS, WSL2, or compatible containers. Covers UF2 (rp2, samd, nrf), esptool (esp32, esp8266), STM32 DFU, optional pyOCD debug probes, and Infineon PSOC Edge OpenOCD, with explicit target selection, bootloader handling, backups, and verification.
---

# Flash MicroPython with mpflash

## Establish access and the tool

1. Use the terminal on the machine that can access the intended board. Check
   inside the actual WSL distro or container, not just its host. A remote agent
   cannot access USB attached to the user's computer without an explicitly
   configured device connection. Never access another user's devices.
2. Check `mpflash --version`, then `mpflash --help`, `mpflash list --help`,
   `mpflash download --help`, and `mpflash flash --help`. If it is not on PATH
   (`Get-Command mpflash` in PowerShell; `command -v mpflash` in a POSIX shell),
   try `uvx mpflash --version` and replace `mpflash` with `uvx mpflash` in every
   example. uvx may download the tool into an isolated environment; obtain any
   required approval for that download. Do not build the checkout, install
   globally, or change the project's Python environment as routine setup.
   If neither executable is available, report that mpflash or uv is needed.
3. Verify each required command and flag in that installed version. Older
   versions may lack `--volume`, `--method`, probe commands, or `--no-reset`.
   Report missing features and request an approved tool update or a supported
   alternative; never silently drop safety flags.
4. Use a writable firmware directory visible to that terminal. mpflash stores
   firmware and a database in the OS downloads area by default;
   `MPFLASH_FIRMWARE` overrides it, and global `--dir` takes precedence. Use a
   dedicated folder rather than an unrelated existing archive. Create and
   verify that directory before setting `MPFLASH_FIRMWARE`: some versions warn
   and silently use the default directory if the configured path does not exist.
   Treat that warning as a failed isolation check and correct the path before
   proceeding. mpflash may
   initialize its database even for help commands. Do not clear caches or
   overwrite existing custom firmware as troubleshooting.

Global options precede the subcommand:

```text
mpflash --dir "firmware-cache" --no-interactive download --board RPI_PICO_W --version stable
```

Use `--no-interactive` for agent-run commands only after all parameters and
permissions are resolved. It suppresses prompts; it is not a dry run or a
consent mechanism. Never use `--quiet` when errors or progress must be inspected.

## Identify exactly one authorized target

- First enumerate ports without opening them: `mpremote connect list` if
  available, or `python -m serial.tools.list_ports -v` using an existing Python
  environment with pyserial. Windows Device Manager, Linux device listings,
  and macOS System Information can also identify USB devices. Do not install
  another tool merely to enumerate ports.
- Match the physical board using the user-provided port, USB identity, and
  board model. If ambiguous, ask before opening any port. A listed port is not
  proof of MicroPython or of compatibility with a firmware image.
- Query firmware only after permission to interrupt that selected device:

  ```text
  mpflash --no-interactive list --serial COM7 --no-reset
  mpflash --no-interactive list --serial COM7 --json --no-progress --no-reset
  ```

  `list` opens the board to identify it and normally resets it afterwards.
  `--no-reset` suppresses that final reset, not raw-REPL interruption or
  possible resets during connection. Do not run unfiltered `mpflash list` in
  a shared environment.
- Replace `COM7` in every example with the exact current port: Windows `COM7`,
  Linux `/dev/ttyACM0` or `/dev/ttyUSB0`, macOS `/dev/cu.usbmodem...` or
  `/dev/cu.usbserial...`. Use paths reported by enumeration; verify a Linux
  `/dev/serial/by-id/` alias is accepted by mpflash before relying on it.
  Quote paths with spaces and use the host shell's path syntax.
- Record the MicroPython hardware port, exact board ID, variant, CPU, current
  version, and USB identity. An unknown or blank board cannot be guessed from
  its chip alone. For a blank board or bootloader-only device, ask for its exact
  model and hardware revision and confirm the official firmware page.

Close only the selected board's serial monitor or ask its owner to release it.
Do not kill processes by name, reset arbitrary boards, or remove a boot file to
make discovery work. Re-enumerate after reset, bootloader entry, unplugging, or
USB forwarding; ports, bus IDs, and mount points can change.

## Select and download firmware

Confirm the board ID against [official MicroPython downloads](https://micropython.org/download/).
Select the correct variant for features such as PSRAM and flash size. Do not
substitute a generic board for a vendor board without confirming compatibility.
Use `stable` unless the user requests a preview or exact release; report the
resolved release, not merely the alias.

With an explicit known board, downloading does not need a connected device:

```text
mpflash --no-interactive download --board RPI_PICO_W --version stable
mpflash --no-interactive download --board ESP32_GENERIC --version 1.25.0
```

The second command is an example of a pinned version, not a recommendation.
`download --board` may fetch multiple variants; it has no `--variant` option
in the current CLI. Select the desired variant during flashing. Keep the same
firmware directory for download and flash. Inspect download errors and the
actual files; a command's exit status alone may not establish success.
`--force` forces a firmware download, not device approval or board compatibility.

If GitHub release lookup fails and mpflash uses cached versions, do not assume
`stable` is current. Check the latest release on the official board download
page, then pin that verified version for flashing. Report the lookup failure;
do not inspect, print, or change credentials as part of a firmware test.

For custom images, inspect `mpflash add --help` and the installed version's
custom-firmware workflow first. Confirm provenance, board/variant metadata,
format, and the exact image selected from the database. Do not pass a filename
to `flash` as though it accepted a positional image. `--build` is optional
mpbuild/Docker functionality, not routine flashing; only use it when the user
requests a local build and approves its prerequisites.

## Approve and flash

Before executing, summarize the exact device and firmware, selected backend,
bootloader/reset actions, expected data loss, and any downloads. Ask for explicit
approval for that plan. Back up required device files to a new user-approved
local destination first, using the mpremote skill if available. A firmware
update can invalidate the filesystem or partition layout even with
`--no-erase --no-format`; never guarantee preservation.

These are independent examples for **identified, compatible boards**, not a
sequence and not permission to flash:

```text
mpflash --no-interactive flash --serial COM7 --board RPI_PICO_W --version stable --no-erase --no-format
mpflash --no-interactive flash --serial COM7 --board ESP32_GENERIC --version stable --method esptool --no-erase --no-format
mpflash --no-interactive flash --serial COM7 --board PYBV11 --version stable --method dfu --no-erase --no-format
```

- Never run bare `mpflash flash`, omit `--serial` for a serial workflow, or use
  `*`, `COM*`, or another glob. The default targets all connected serial boards.
  A `--board` flag alone does not scope the physical device.
- Add `--variant CONFIRMED_VARIANT` only for the confirmed firmware variant.
  For the base variant, use its explicit base board ID and omit `--variant`.
  Do not assume `--variant -` works merely because help mentions it: explicit
  board workflows in some versions construct an invalid board ID from it.
  Do not reuse a variant from a different connected board.
- Let `--method auto` choose a compatible backend unless the plan needs an
  explicit method. `--bootloader auto` attempts entry where possible.
  `mpy` uses MicroPython, `touch1200` opens at 1200 baud, `manual` needs the
  user's button/reset action, and `none` assumes the device is ready.
  Manual mode is not suitable for an unattended command waiting for input:
  have the user put the board in the documented mode first, then use `none`
  only when that backend and the installed version support the ready device.
- Use the board manufacturer's procedure: BOOTSEL while connecting many RP2
  boards, BOOT/RESET on many ESP boards, BOOT0/RESET on many STM32 boards, or
  double-reset on some SAMD/nRF boards. These are not universal instructions.
  Do not install or replace a bootloader just to obtain a UF2 drive.
- `--erase` and `--format` are destructive and mutually exclusive in the
  current CLI. Erase behavior varies by backend; format recreates an empty
  filesystem after flashing. Obtain separate approval before either operation.
  Do not invoke the standalone `erase` or `format` commands as recovery checks.

## Backend-specific requirements

| Hardware port / method | Firmware and requirements |
| --- | --- |
| `rp2`, `samd`, supported `nrf` / `uf2` | `.uf2`, compatible existing UF2 bootloader, and a writable boot volume visible to the flashing terminal. Not every nRF board ships with that bootloader. |
| `esp32`, `esp8266` / `esptool` | Board-matched `.bin`, accessible serial port, and ROM download mode. mpflash manages esptool; do not invent chip offsets or use raw erase commands. |
| `stm32` / `dfu` | Compatible `.dfu` or supported `.bin`, USB DFU mode, libusb access, and the correct driver. A serial mapping alone is insufficient. |
| Supported targets / `pyocd` | Optional `mpflash[pyocd]`, SWD/JTAG probe, exact target mapping, and a supported `.bin`, `.hex`, `.elf`, or `.axf`. Typical ports are `stm32`, `rp2`, and `samd`; a probe does not make all chips supported. |
| `psoc-edge` / `openocd` | Official `.zip` release package and an accessible KitProg3 probe, using the Infineon build of OpenOCD, not stock OpenOCD. Upstream reports board testing on `KIT_PSE84_AI`. |

Do not claim flashing support for `alif`, `mimxrt`, `renesas-ra`, or `zephyr`
from download availability. Upstream currently lists those as unimplemented,
and `cc3200` and `pic16bit` as not planned. Check `mpflash plugins` when
available for installed backend capabilities; third-party plugins are not
automatically trusted or approved.

### UF2 volumes and STM32 DFU isolation

For a board already in UF2 mode, check the exact volume and read `INFO_UF2.TXT`.
Confirm its identity before using a version with `--volume`:

```text
mpflash --no-interactive flash --board RPI_PICO_W --version stable --method uf2 --bootloader none --volume "E:\" --no-erase --no-format
```

Replace `E:\` with the actual Windows drive, macOS `/Volumes/RPI-RP2`, or Linux
mount such as `/media/USER/RPI-RP2`. The volume overrides serial task selection.
Never write to an ordinary host drive or an unverified mount.

UF2 auto-discovery may select by hardware family, and an unavailable explicit
volume may fall back to scanning other drives. Reconnection after a volume
flash may also auto-select a serial device. Require the intended board to be
the only eligible visible target throughout this operation; ask the user to
isolate their devices if necessary. Do not rely on `--volume` or `--serial`
alone to exclude every other board.

STM32 DFU uses USB discovery and can select the first DFU device, independent
of the selected pre-reset serial port. Require exactly one eligible DFU device
visible in that execution environment. If a bootloader-only board has no
serial port and the installed mpflash cannot create a scoped task for it,
report that limitation rather than broadening the selection.

### Debug probes

If pyOCD is missing and the user approves the optional dependency, use an
isolated runner such as `uvx --from "mpflash[pyocd]" mpflash` for every pyOCD
command rather than modifying the project environment.
Inspect `list-probes --help`; `list-probes --no-detect-targets` avoids requesting
target detection when supported, but probe access still needs permission.
Use `pyocd-targets` to check board mappings. Select a unique probe ID, not an
ambiguous prefix. Target detection and programming may halt or reset the MCU.

```text
mpflash --no-interactive flash --serial COM7 --board RPI_PICO --version stable --method pyocd --probe CONFIRMED_PROBE_ID --no-auto-install-packs --no-erase --no-format
mpflash --no-interactive flash --serial COM7 --board KIT_PSE84_AI --version stable --method openocd --probe CONFIRMED_KITPROG3_SERIAL --no-erase --no-format
```

These examples still require a valid serial task in the installed mpflash CLI;
do not omit its selection merely because programming uses a probe.
Only set `--target` for a verified pyOCD target override. CMSIS packs normally
auto-install; use `--no-auto-install-packs` unless their download is approved.
If that prevents programming, report the missing pack and obtain approval.

Infineon OpenOCD may auto-download into mpflash's user cache even with
`--no-interactive` and without `--yes`. Approve that download before running
the command, or provide an existing suitable executable via `MPFLASH_OPENOCD`.
Current bundled downloads cover Windows x64, Linux x64, and macOS ARM64.
On another architecture, report the missing compatible native tool.
Linux KitProg3 udev-rule installation can require a separate interactive
administrator action; `--yes` does not grant permission for it.

## Host platforms and device access

### One-time Linux/WSL serial setup

For identified USB tty devices without persistent access, use the bundled
[permission helper](scripts/setup_serial_permissions.py) before resets or
flashing. It is generated from mpremote's canonical source and checked for
byte equality in CI; installing mpremote separately is not required.
Existing host permissions are shared by all serial tools, so skip setup if
it already works.

Set `SKILL_DIR` to this installed skill's directory, select a group the user
already belongs to, and replace the example nodes with approved targets:

```sh
python3 "$SKILL_DIR/scripts/setup_serial_permissions.py" --group dialout --device /dev/ttyACM0
sudo -A python3 "$SKILL_DIR/scripts/setup_serial_permissions.py" --install --group dialout --device /dev/ttyACM0
```

Run preview first; execute the installation only after approval of persistent
VID/PID/serial-scoped rules. Repeat `--device` within the same invocation for
additional approved devices, not one sudo call per device. The helper requires
Linux/WSL, Python 3.9+, and active udev 247+, uses mode `0660`, and reloads once.
If WSL restores an inaccessible numeric group, explicitly approve the preview's
broader group access and append `--enroll-observed-group` to both commands.
It can create/enroll that group in the same setup invocation; membership grants
access to all nodes with that group ID. Start a new login/agent session, or use
a finite approved `sg GROUP -c 'COMMAND'` test.

Verify access after reconnect. Keep flashing non-root; no per-reset sudo,
world-writable modes, or passwordless sudo. Preserve existing legacy
`mpbuild-serial-*` names. This handles tty permissions only: raw USB/DFU,
probes, UF2 mounts, Windows binding, and container mappings need their own
backend-specific access and approval.

### Platform-specific access

- **Windows:** use the actual COM port or drive letter. For STM32 DFU, verify
  the bootloader device and its WinUSB/libusb-compatible driver. If a driver
  change is needed, ask the user to install it for that exact USB interface
  using trusted board instructions; never change an unrelated device driver.
- **Linux:** inspect the selected serial/USB node's ownership and the user's
  groups. Use the distro's serial group or a scoped udev rule, not world-writable
  nodes or root flashing. UF2 needs a writable mounted volume; headless setups
  may need `pmount`/`pumount` or an approved host mount. Install missing OS tools
  only after a demonstrated need and approval.
- **macOS:** select the enumerated `/dev/cu.*` device and verify UF2 volumes
  under `/Volumes`. Confirm native libusb/probe dependencies for DFU or debug
  programming. Do not assume Linux udev instructions apply.
- **WSL2:** choose either Windows flashing or WSL flashing, not simultaneous
  access. On Windows, run `wsl --list --verbose` and `usbipd list`, identify
  the intended bus ID, and ask the user to close its Windows serial monitor.
  If not shared, the user can run `usbipd bind --busid CONFIRMED_BUS_ID` in
  administrator PowerShell. With approval, normal PowerShell can run
  `usbipd attach --wsl --busid CONFIRMED_BUS_ID`; check `usbipd list` and
  enumerate inside the target distro. Use its Linux node, not the COM port.
  Bootloader entry may disconnect/re-enumerate USB, so recheck both sides.
  After operations stop, return it with
  `usbipd detach --busid CONFIRMED_BUS_ID` and verify the result.
  Binding persists; administrator `usbipd unbind` revokes sharing only when
  requested. For UF2, the boot volume must actually be mounted and accessible
  in WSL. A Windows drive visible under `/mnt/LETTER` is not proof that the
  installed UF2 backend can use it; verify that version's behavior or flash
  from Windows instead. Do not promise automatic WSL mass-storage mounting.
- **Linux containers/dev containers:** verify access on the Docker daemon's
  host and again inside the container. `--device=/dev/ttyACM0:/dev/ttyACM0`
  permits only that serial node; a non-root user may need its numeric group.
  UF2 also needs its specific writable boot-volume mount; DFU and probes need
  their selected raw USB devices, not just serial. Resets can invalidate
  mappings; recreate the container with confirmed new mappings when needed.
  Do not use `--privileged` or expose all USB devices as a shortcut. Docker
  Desktop and remote daemons may not see a WSL device. Prefer native host
  flashing when scoped USB access or re-enumeration cannot be maintained.

Use the existing [mpremote USB forwarding and container guidance](https://github.com/josverl/mp-agents/blob/main/plugins/mpremote/skills/mpremote/SKILL.md)
for more detail. Any host configuration change still needs approval.

## Verify and report

1. Inspect the complete flash output for backend errors, skipped tasks, erase
   warnings, and the actual flashed count. Partial success or a zero exit code
   is not proof that every approved target was flashed or erased.
2. Re-enumerate and match the returning board by identity, not the first port.
   Query only that confirmed port with
   `mpflash --no-interactive list --serial COM7 --json --no-progress --no-reset`,
   respecting the approved interruption plan.
3. Compare the reported board ID, variant, and resolved firmware version to
   the plan. If metadata is insufficient, use an approved, scoped mpremote
   REPL query of `sys.implementation` and `os.uname()`. Verify required backed-up
   files separately; do not restore incompatible boot files automatically.
4. Report the device, image/version, backend, observed verification, and any
   remaining issue. A UF2 drive disappearing is expected but is not proof of
   success. If a board fails to reconnect, stop and inspect boot mode, power,
   drivers, permissions, and the selected image; do not retry with erase,
   a broader target set, or another board's firmware.

## Plugin portability

This standard [Agent Skill](https://agentskills.io/) is shared by the portable
and Claude-compatible `mpflash` plugin manifests. Use the agent's available
terminal tool; no provider-specific API is required. Installing or loading the
skill grants no terminal, USB, administrator, or flashing permissions.

[Plugin installation and limitations](../../README.md) |
[mpflash reference](https://github.com/josverl/mpflash/blob/main/README.md) |
[STM32 Linux permissions](https://github.com/josverl/mpflash/blob/main/docs/stm32_udev_rules.md) |
[KitProg3 Linux permissions](https://github.com/josverl/mpflash/blob/main/docs/psoc_edge_udev_rules.md)
