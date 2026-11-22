#!/usr/bin/env python3
"""Install persistent, individually scoped USB serial permissions on Linux."""

import argparse
from dataclasses import dataclass
import grp
import hashlib
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys


@dataclass(frozen=True)
class UsbSerial:
    vendor: str
    product: str
    serial: str

    def rule(self, group: str) -> str:
        if not re.fullmatch(r"[0-9a-fA-F]{4}", self.vendor):
            raise ValueError("Invalid USB vendor ID")
        if not re.fullmatch(r"[0-9a-fA-F]{4}", self.product):
            raise ValueError("Invalid USB product ID")
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", self.serial):
            raise ValueError("Missing or unsafe USB serial; use a reviewed device-specific rule")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", group):
            raise ValueError("Invalid group name")
        return (
            '# Managed by mpbuild setup_serial_permissions.py\n'
            f'SUBSYSTEM=="tty", ATTRS{{idVendor}}=="{self.vendor.lower()}", '
            f'ATTRS{{idProduct}}=="{self.product.lower()}", '
            f'ATTRS{{serial}}=="{self.serial}", GROUP:="{group}", MODE:="0660"\n'
        )

    def filename(self) -> str:
        identity = f"{self.vendor.lower()}:{self.product.lower()}:{self.serial}"
        digest = hashlib.sha256(identity.encode("ascii")).hexdigest()[:16]
        return f"99-mpbuild-serial-{digest}.rules"


def read_identity(device: Path) -> UsbSerial:
    device = device.resolve(strict=True)
    for parent in (device, *device.parents):
        if (parent / "idVendor").is_file() and (parent / "idProduct").is_file():
            if not (parent / "serial").is_file():
                raise ValueError("USB device has no unique serial; refusing a family-wide rule")
            return UsbSerial(
                (parent / "idVendor").read_text().strip(),
                (parent / "idProduct").read_text().strip(),
                (parent / "serial").read_text().strip(),
            )
    raise ValueError("Not a USB serial device; use the host's device-specific permissions")


def discover_device(path: str) -> tuple[Path, UsbSerial]:
    node = Path(path).resolve(strict=True)
    if node.parent != Path("/dev") or not node.name.startswith("tty") or not node.is_char_device():
        raise ValueError(f"Expected a current /dev/tty device, got {node}")
    return node, read_identity(Path("/sys/class/tty") / node.name / "device")


def write_rule(path: Path, text: str) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing symlink rule file: {path}")
    if path.exists():
        if path.read_text() != text:
            raise ValueError(f"Existing rule differs; review it before replacing: {path}")
        return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w") as stream:
        os.fchmod(stream.fileno(), 0o644)
        stream.write(text)


def observed_group(gid: int) -> tuple[str, bool]:
    if gid < 100:
        raise ValueError(f"Refusing enrollment in low/system group ID {gid}")
    try:
        name = grp.getgrgid(gid).gr_name
    except KeyError:
        name = f"mpbuild-serial-{gid}"
        try:
            grp.getgrnam(name)
        except KeyError:
            return name, True
        raise ValueError(f"Group name {name} already exists with another ID")
    if name in {"root", "sudo", "wheel", "docker", "adm"}:
        raise ValueError(f"Refusing enrollment in privileged group {name}")
    return name, False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", action="append", required=True, help="Exact current USB tty node; repeat for each approved board")
    parser.add_argument("--group", default="dialout", help="Existing serial group the invoking user already belongs to")
    parser.add_argument("--enroll-observed-group", action="store_true", help="Explicitly approve enrollment in additional groups observed on selected USB tty nodes (WSL reconnect fallback)")
    parser.add_argument("--install", action="store_true", help="Install rules and apply them; run once using sudo -A")
    args = parser.parse_args()
    if sys.platform != "linux":
        raise ValueError("This helper requires Linux or WSL2 with an active udev daemon")
    user = os.environ.get("SUDO_USER") if os.geteuid() == 0 else pwd.getpwuid(os.getuid()).pw_name
    if not user:
        raise ValueError("Run as your normal user, or use sudo -A from that user")
    account = pwd.getpwnam(user)
    group = grp.getgrnam(args.group)
    if group.gr_gid not in os.getgrouplist(user, account.pw_gid):
        raise ValueError(f"{user} must already belong to {args.group}; approve group enrollment separately and start a new login session")
    devices = dict(discover_device(path) for path in args.device)
    rules = {usb.filename(): usb.rule(args.group) for usb in devices.values()}
    membership = os.getgrouplist(user, account.pw_gid)
    enrollments = {}
    allowed_groups = {group.gr_gid}
    for node in devices:
        gid = node.stat().st_gid
        if gid in membership:
            allowed_groups.add(gid)
        else:
            if args.enroll_observed_group:
                enrollments[gid] = observed_group(gid)
                allowed_groups.add(gid)
            else:
                print(f"Note: {node} currently uses group ID {gid}. If WSL restores it on reconnect, approve --enroll-observed-group during setup.")
    version = subprocess.check_output(["udevadm", "--version"], text=True).strip()
    if int(version) < 247:
        raise ValueError("udev 247+ is required for final GROUP/MODE assignments")
    for filename, rule in rules.items():
        print(f"/etc/udev/rules.d/{filename}\n{rule}", end="")
    for gid, (name, create) in enrollments.items():
        print(f"Enrollment plan: {user} -> {name} (gid={gid}, create={create}). This grants access to all nodes using that group.")
    if not args.install:
        print("Preview only. Review these rules, then run the same command once with sudo -A and --install.")
        return
    if os.geteuid() != 0:
        raise ValueError("--install requires one sudo -A invocation; preview does not")
    subprocess.run(["udevadm", "control", "--ping"], check=True)
    for gid, (name, create) in enrollments.items():
        if create:
            subprocess.run(["groupadd", "--gid", str(gid), name], check=True)
    if enrollments:
        names = ",".join(name for name, _ in enrollments.values())
        subprocess.run(["usermod", "--append", "--groups", names, user], check=True)
        print("Group enrollment completed. Start a new login/agent session; for a scoped immediate test use sg GROUP -c 'COMMAND'.")
    root = Path("/etc/udev/rules.d")
    root.mkdir(exist_ok=True)
    for filename, rule in rules.items():
        write_rule(root / filename, rule)
    subprocess.run(["udevadm", "control", "--reload-rules"], check=True)
    for node, identity in devices.items():
        if read_identity(Path("/sys/class/tty") / node.name / "device") != identity:
            raise ValueError(f"Device identity changed during setup: {node}")
        subprocess.run(["udevadm", "trigger", "--action=change", f"--sysname-match={node.name}", "--subsystem-match=tty"], check=True)
    subprocess.run(["udevadm", "settle"], check=True)
    for node in devices:
        info = node.stat()
        if info.st_gid not in allowed_groups or stat.S_IMODE(info.st_mode) != 0o660:
            raise ValueError(f"Rule did not apply to {node}; inspect udev logs rather than retrying chgrp")
        print(f"Verified {node}: accessible group ID={info.st_gid}, mode=0660")
    print("Setup installed. Verify access after reconnect; WSL may restore the observed numeric group. Run build/flash tools as your normal user, not root.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Serial permission setup failed: {error}", file=sys.stderr)
        sys.exit(1)
