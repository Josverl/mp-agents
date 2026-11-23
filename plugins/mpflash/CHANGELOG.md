# Changelog

## 0.1.1

- Generate and validate bundled helpers with Python rather than Node tooling.
- Bundle the serial-permission helper generated from mpremote and document
  approved one-time Linux/WSL setup before reset or flashing.
- Validate bundled helper equality in CI without requiring another plugin
  installation or changing existing host permission rules.

## 0.1.0

- Initial mpflash skill with portable and Claude-compatible plugin manifests.
- Board identification, firmware selection and download, scoped flashing,
  bootloader guidance, and post-flash verification.
- UF2, Espressif, STM32 DFU, optional pyOCD, and PSOC Edge OpenOCD workflows.
- Windows, Linux, macOS, WSL2 USB forwarding, and container access guidance,
  with explicit approval for disruptive operations and tool downloads.
- Verify Windows Pico 2 W UF2 and ESP32-C6 esptool flashing and REPL access.
- Document firmware-directory fallback, cached release lookup, and the
  explicit-board base-variant sentinel limitation found during hardware tests.
