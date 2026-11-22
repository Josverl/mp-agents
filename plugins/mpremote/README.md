# mpremote

A skills-only plugin for **MicroPython** device workflows on Windows, Linux,
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

## Install

Follow the [marketplace installation instructions](../../README.md#use-the-marketplace).
For example:

```sh
copilot plugin marketplace add josverl/mp-agents
copilot plugin install mpremote@mp-agents
```

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

## Package and validation

The root manifest targets Agent Plugins 1.0; the `.claude-plugin` manifest
supports Claude's plugin format. Both discover the **same** skill directory.
There are no hooks, bundled executable tools, or MCP servers.

Structural checks do not prove GUI activation or USB connectivity. See the
[compatibility table](../../README.md#compatibility) for validation scope.

## License

[MIT](../../LICENSE).
