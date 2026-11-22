# mp-agents

**Portable agent plugins for MicroPython.** Use the same workflows across projects
and machines, with managed installation and updates instead of copying skill
files into each project.

This community marketplace focuses on developing with MicroPython and working
with MicroPython devices. It is independent of the MicroPython project and is
not limited to one AI provider.

The marketplace and plugins targets:
- GitHub Copilot (CLI, VS Code,and the Copilot app), 
- Claude Code, and Claude's plugin interfaces. 

Other clients that support the included formats are welcome.





## What's included

| Plugin | What it does |
| --- | --- |
| [mpremote](plugins/mpremote/README.md) | Find boards, transfer files, run scripts, mount local code, install MicroPython packages, work with ROMFS. Includes Windows-to-WSL USB forwarding and Linux container guidance. |


## Background

MicroPython workflows span different boards, operating systems, development
environments, and agent clients. This marketplace packages reusable instructions
without hard-coding a user's device, or requiring multiple copies of project-specific skills.

## Generic Requirements

- A client with plugin/marketplace support, with that feature enabled.
- An execution environment that can access the board's serial port.
- An installed `mpremote`, or `uvx` from [uv](https://docs.astral.sh/uv/) so the
  skill can use `uvx mpremote`.
- For Windows USB devices used in WSL2:
  [usbipd-win](https://github.com/dorssel/usbipd-win).

Installing instructions does not grant USB access, install drivers, or bypass
permissions. A cloud chat or sandbox cannot automatically access a board plugged
into your computer.


# Use the marketplace

Before installing any plugin, review its documentation and understand the operations it performs. The marketplace only provides instructions; it does not include bundled installers or automatic hardware access.

| Client | Add marketplace | Install plugin |
| --- | --- | --- |
| GitHub Copilot CLI | `copilot plugin marketplace add josverl/mp-agents` ([details](#github-copilot-cli)) | `copilot plugin install mpremote@mp-agents` ([details](#github-copilot-cli)) |
| VS Code with GitHub Copilot | Add `josverl/mp-agents` in Customizations ([details](#vs-code-with-github-copilot)) | [Install the mpremote agent plugin in VS Code](https://vscode.dev/redirect?url=vscode%3A%2F%2Fchat-plugin%2Finstall%3Fsource%3Djosverl%252Fmp-agents%26plugin%3Dmpremote) ([details](#vs-code-with-github-copilot)) |
| GitHub Copilot app | **Customize > Installed > Add plugin > Manage marketplaces…** ([details](#github-copilot-app)) | **Add plugin > Browse plugins**, then install `mpremote` ([details](#github-copilot-app)) |
| Claude Code | `claude plugin marketplace add josverl/mp-agents` ([details](#claude-code)) | `claude plugin install mpremote@mp-agents` ([details](#claude-code)) |
| Claude web/desktop and Cowork | Add `josverl/mp-agents` in Customize ([details](#claude-webdesktop-and-cowork)) | Find and install `mpremote` in Customize ([details](#claude-webdesktop-and-cowork)) |


The GitHub CLI example installs the skill directly, not the plugin. GUI entries
show values to enter or actions to select; they are not shell commands.

### GitHub Copilot CLI

```sh
copilot plugin marketplace add josverl/mp-agents
copilot plugin marketplace browse mp-agents
copilot plugin install mpremote@mp-agents
```

Start a new session and ask:

> Use the mpremote skill to list the available MicroPython serial ports.
> Do not open a port until we have identified the board.

### VS Code with GitHub Copilot

Enable agent plugins (`chat.plugins.enabled`), then run **Chat: Open Customizations**.
Add `josverl/mp-agents` as a marketplace, review the `mpremote` plugin, and install
it at user scope for use across projects.

Supported VS Code versions can also use this
[install link](https://vscode.dev/redirect?url=vscode%3A%2F%2Fchat-plugin%2Finstall%3Fsource%3Djosverl%252Fmp-agents%26plugin%3Dmpremote).
It asks for confirmation and installs the agent plugin, not the `mpremote` Python
tool. VS Code also discovers plugins installed by Copilot CLI in the same user's
environment.

### GitHub Copilot app

To add the marketplace in the app:

1. Open **Customize** and select **Installed**.
2. Open the **Add plugin** dropdown and select **Manage marketplaces…**.
3. Add `josverl/mp-agents` as the marketplace.
4. Return to **Installed**, open **Add plugin**, and select **Browse plugins**.
5. Find `mpremote` and install it.

The menu labels above match the Copilot app UI. If the marketplace dialog differs
in your app version, consult
[GitHub's Copilot app instructions](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app#adding-a-plugin-marketplace).

Alternatively, open **PowerShell** on the same machine and use Copilot CLI to
add the marketplace and install the plugin (these are terminal commands, not
chat messages):

```powershell
copilot plugin marketplace add josverl/mp-agents
copilot plugin install mpremote@mp-agents
copilot plugin list
```

Look for `mpremote@mp-agents` in the output, then start a new app session and
check **Customize > Installed**. The CLI installation has been tested; app
discovery of that installation has not been verified. GitHub documents that
CLI-configured skills are available in the Copilot app, but plugin display and
refresh behavior can vary. An existing personal `mpremote` skill may appear
even without the plugin and can take precedence over the plugin's copy.

### Claude Code

```sh
claude plugin marketplace add josverl/mp-agents
claude plugin install mpremote@mp-agents
```

Start a new session and invoke `/mpremote:mpremote`, or describe the MicroPython
task. Claude's plugin name prefix does not change the skill's own `name` field.

### Claude web/desktop and Cowork

Where your client and plan support it, open **Customize > Plugins > Add >
Add marketplace**, add `josverl/mp-agents`, and install `mpremote`.
Claude documents account-backed plugin installation through this interface;
CLI-only installs remain local. Loading the skill in chat does not give chat
direct access to USB hardware. Use a local execution environment that actually
exposes the serial device.

### Other tools

The plugin contains a standard [Agent Skill](https://agentskills.io/) and an
[Agent Plugins 1.0](https://agent-plugins.org/) manifest, plus a Claude-compatible
manifest. A compatible client can consume the format it supports. Skill-only
clients can install the skill from this repository with their own skill manager.
For example, GitHub CLI 2.90.0+ supports:

```sh
gh skill install josverl/mp-agents mpremote --scope user
```

Use that command as an alternative to the plugin, not a second installation of
the same skill. A pre-existing personal `mpremote` skill can shadow the plugin
version; review and remove or rename the old copy when migrating.

## Updates and multiple machines

One published repository is the source for everyone. Install the plugin in each
execution environment that needs it; Windows, WSL, and a dev container can have
different plugin locations.

```sh
copilot plugin update mpremote@mp-agents
```

```sh
claude plugin marketplace update mp-agents
claude plugin update mpremote@mp-agents
```

VS Code provides **Chat: Update Plugins**; supported versions can automatically
update Git-sourced plugins. Claude's account-backed UI has source-sync controls.
Do not assume automatic synchronization between different providers or machines.
Machine setup scripts can repeat the install commands, and organization-managed
settings can distribute approved marketplaces. Always review new versions.

## Compatibility

| Interface | Package support | Validation |
| --- | --- | --- |
| GitHub Copilot CLI | Root catalog and Agent Plugins manifest; legacy Claude manifest also provided | Local and published GitHub marketplace registration and installation passed in isolated configuration; one skill discovered. |
| VS Code / GitHub Copilot app | Copilot catalog alias and portable plugin layout | Documented supported format; GUI discovery and activation need a client smoke test. |
| Claude Code | `.claude-plugin` catalog and plugin manifest; shared `skills/` directory | Claude validation, local and GitHub registration, and user-scope installation passed in isolated configuration; one skill discovered. |
| Claude web/desktop / Cowork | Claude marketplace format | Account installation and device-access capabilities depend on the client; smoke test needed. |
| Other compatible clients | Standard skill and portable plugin manifest | Not excluded; not yet integration-tested. |

Hardware tests on a Raspberry Pi Pico 2 W and ESP32-C6 verified Windows file
round-trips, script execution, mounts, `mip`, directory trees, and scoped
deletion. The Pico also ran mounted scripts in Ubuntu WSL2 and a non-root
Docker Desktop Linux container using `uvx mpremote`. Other boards and Linux
installations may behave differently. The automated marketplace checks do not
open serial ports or change USB ownership.

## Add a plugin

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep the focus on MicroPython and make
shared capabilities portable. Client-specific additions are welcome when clearly
separated from shared instructions.

## Checks

With Node.js 22 or later, run:

```sh
node scripts/validate.mjs
```

The dependency-free check compares catalog aliases, verifies plugin metadata and
versions, checks local source paths, and validates skill frontmatter and links.
[CI](.github/workflows/validate.yml) runs it on Windows and Linux. It makes no
model calls, spends no AI credits, and accesses no devices.

Initial local checks:

- `node scripts/validate.mjs`: passed.
- Portable manifest validation against the official Agent Plugins 1.0 JSON
  schema with PowerShell `Test-Json`: passed.
- `copilot plugin marketplace add C:\dev\mp-agents` and
  `copilot plugin install mpremote@mp-agents`: passed with an isolated
  `COPILOT_HOME`; Copilot CLI 1.0.67 reported one installed skill.
- `npx --yes --package @anthropic-ai/claude-code claude plugin validate C:\dev\mp-agents`
  and validation of `C:\dev\mp-agents\plugins\mpremote`: passed. The plugin
  validator (Claude Code 2.1.330) noted a missing optional directory-listing icon.
- `npx --yes --package @anthropic-ai/claude-code claude plugin marketplace add C:\dev\mp-agents`
  and `claude plugin install mpremote@mp-agents` through the same npx package:
  passed with an isolated `CLAUDE_CONFIG_DIR`. `claude plugin details mpremote`
  reported one skill, with no agents, hooks, MCP servers, or LSP servers.

These paths record the initial Windows checks, not installation prerequisites.
Both clients also passed registration and installation from the published
`josverl/mp-agents` GitHub repository using the commands in
[Use the marketplace](#use-the-marketplace). The first
[validation run](https://github.com/josverl/mp-agents/actions/runs/45046542898)
passed on both Windows and Linux.
No model-driven skill execution, GUI activation, or hardware changes were tested.

## License

[MIT](LICENSE). Retain applicable upstream notices. This repository's structure
and documentation are adapted from the
[GitHub plugin marketplace starter](https://github.com/github/plugin-marketplace-starter).
Its example maintenance plugins and model-based evaluation infrastructure are
not included.

## Maintainers and support

Maintained by [@Josverl](https://github.com/josverl). Contributions from the
MicroPython community are welcome. Use
[issues](https://github.com/josverl/mp-agents/issues) for bugs and questions.
Include the client, operating system, `mpremote` version, and a minimal
reproduction; do not include credentials or sensitive device contents.

For sensitive security reports, use GitHub's private vulnerability reporting
when enabled. Do not publish exploit details or secrets in public issues.

## References

- [Copilot plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)
- [VS Code agent plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
- [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [MicroPython mpremote documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)
