# mpflash

A skills-only plugin for flashing **MicroPython** firmware with
[mpflash](https://github.com/josverl/mpflash). It provides instructions, not a
flashing executable, VS Code extension, or MCP server.

## Capabilities

- Identify an authorized board and its MicroPython board ID and variant.
- Download stable, preview, or explicitly versioned firmware.
- Flash one confirmed board using its exact serial port or UF2 boot volume.
- Use UF2 for `rp2`, `samd`, and supported `nrf` boards; esptool for `esp32`
  and `esp8266`; and USB DFU for `stm32`.
- Use optional pyOCD debug probes or Infineon OpenOCD for supported PSOC Edge
  boards, with explicit probe selection.
- Handle bootloader entry, permissions, re-enumeration, and verification.
- Explain WSL2 USB forwarding and the limits of container device access.

Support depends on the installed mpflash version, board, bootloader, firmware,
and host drivers. Download availability alone does not prove flashing support.
See the [skill](skills/mpflash/SKILL.md) for backend-specific limits.

## Requirements and platforms

- A compatible agent with terminal access on the machine that can reach the
  selected device. A hosted cloud session cannot access local USB hardware.
- An existing `mpflash` executable or [uv](https://docs.astral.sh/uv/) for
  `uvx mpflash`. mpflash requires Python 3.10 or newer; optional extras and
  native dependencies may impose additional constraints.
- Network access for firmware or missing tools, and space for mpflash's
  firmware cache and database.
- Access to the required serial port, USB DFU device, debug probe, or mounted
  UF2 volume. Serial access alone does not enable every flashing method.

Upstream documents Windows x64, Linux x64, and macOS testing. The skill also
covers WSL2 and compatible Linux containers, without promising that every
backend works on every OS or CPU architecture. Infineon OpenOCD's bundled
downloads currently cover Windows x64, Linux x64, and macOS ARM64.

## Install

Follow the [marketplace instructions](../../README.md#use-the-marketplace):

```sh
copilot plugin marketplace add josverl/mp-agents
copilot plugin install mpflash@mp-agents
```

```sh
claude plugin marketplace add josverl/mp-agents
claude plugin install mpflash@mp-agents
```

In VS Code, add `josverl/mp-agents` in **Chat: Open Customizations**, then
review and install `mpflash`. Supported versions can use this
[install link](https://vscode.dev/redirect?url=vscode%3A%2F%2Fchat-plugin%2Finstall%3Fsource%3Djosverl%252Fmp-agents%26plugin%3Dmpflash).
Other supported marketplace UIs can select `mpflash` from the same catalog.
Installing the plugin does not install the Python tool or drivers.

## Use and update

Start a new session with device access and ask:

> Use the mpflash skill to identify my board and prepare a stable MicroPython
> firmware update. Ask before opening a port, resetting, or flashing.

> Download MicroPython firmware for RPI_PICO_W without touching any boards.

With Claude Code, invoke `/mpflash:mpflash`.

```sh
copilot plugin update mpflash@mp-agents
```

```sh
claude plugin marketplace update mp-agents
claude plugin update mpflash@mp-agents
```

## Permissions and limitations

Identification can interrupt running firmware. Flashing resets the device and
may destroy files or change its partition layout even without an erase flag.
Back up required data first. Erase and format need separate approval; the skill
never treats installation as approval to operate hardware.

The skill avoids wildcard flashing, ambiguous probes, unrestricted containers,
and automatic driver or system-permission changes. UF2 and DFU workflows may
need the intended board isolated from other devices because backend discovery
can select a different board after a reset. Missing native dependencies or
unsupported boards are reported rather than bypassed.

Both manifests discover the same skill. There are no hooks, bundled executable
helpers, or automatic hardware operations. Instructions were checked against
the local mpflash CLI and backend sources.

Validation:

- `node scripts/validate.mjs --sync`: passed; all three catalogs synchronized.
- `node scripts/validate.mjs`: passed; both marketplace plugins validated.
- Installed mpflash 1.28.5: `--version` and help for the root command, `list`,
  `download`, `flash`, `list-probes`, and `pyocd-targets` passed using an isolated
  firmware directory, without opening devices. Newer backend guidance comes
  from upstream source; the skill requires checking installed capabilities.

### Windows hardware validation

On 2026-11-22, using mpflash 1.28.5 and separate existing firmware directories,
the following commands passed on a Pico 2 W (UF2) and ESP32-C6 (esptool):

```powershell
mpflash --no-interactive download --board RPI_PICO2_W --version stable
mpflash --no-interactive download --board ESP32_GENERIC_C6 --version stable
mpflash --no-interactive flash --serial COM28 --board RPI_PICO2_W --version 1.29.0 --method uf2 --no-erase --no-format
mpflash --no-interactive flash --serial COM35 --board ESP32_GENERIC_C6 --version 1.29.0 --method esptool --no-erase --no-format
mpflash --no-interactive list --serial COM28 --json --no-progress --no-reset
mpflash --no-interactive list --serial COM35 --json --no-progress --no-reset
```

Each flash reported exactly one updated board. esptool verified the written
data hash. Both boards returned with the expected board ID and MicroPython
1.29.0; independent scoped mpremote queries of `sys.implementation` and
`os.uname()` also passed, followed by an execution marker. This tested
reinstallation of the existing stable version, not a version upgrade.
The COM ports are recorded test observations, not defaults.

Release lookup reported a GitHub authentication failure and used cached
versions. Firmware downloads succeeded from micropython.org, and the current
stable release was independently confirmed on both official board pages before
flashing the pinned version. No credentials were inspected or changed.

An initial Pico command with `--variant -` failed before programming because
mpflash constructed an invalid board ID. Omitting that argument for the
confirmed base board succeeded. The skill now documents this limitation and
the requirement to create environment-configured firmware directories first.

Client activation, other operating systems, UF2 volume-only selection, DFU,
debug probes, and explicit erase/format behavior remain untested for this
plugin. Windows serial-to-UF2 and esptool results do not establish those
capabilities.

## License

[MIT](../../LICENSE).
