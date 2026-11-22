# Changelog

## 0.1.0

- Generalize board discovery, effective manifests, configuration, USB-free
  builds, artifact selection, and flashing handoff across MicroPython ports,
  including non-MCU host targets and explicit unsupported-port limitations.
- Add a reviewed, opt-in Python helper for persistent, device-scoped Linux/WSL
  udev permissions; batch setup and approved numeric-group enrollment into
  one sudo invocation, with safe-rule tests in Linux CI.
- Validate the same build workflow on ESP32-C6 with ESP-IDF containers,
  successful esptool programming, frozen-module verification, and non-root
  serial access after reconnect; document WSL's numeric-group override.
- Initial portable and Claude-compatible mpbuild plugin with one shared skill.
- Container prerequisites, uv tool installation and uvx execution, board and
  variant selection, custom frozen manifests, and firmware artifact checks.
- Linux, macOS, and WSL2 guidance; require native WSL storage on Windows.
- USB-free build guidance for mpbuild versions that auto-forward devices.
- Cross-reference mpflash for approved custom firmware flashing and mpremote
  for device backups and runtime verification.
- Validate a custom frozen-module Pico 2 W build in Docker/WSL2 and its running
  firmware after UF2 programming; document the post-copy reconnect failure
  and scoped serial-permission recovery.
