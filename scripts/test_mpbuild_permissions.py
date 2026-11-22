import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


script = Path(__file__).resolve().parents[1] / "plugins/mpbuild/skills/mpbuild/scripts/setup_serial_permissions.py"
spec = importlib.util.spec_from_file_location("setup_serial_permissions", script)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load serial permission helper")
helper = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helper
spec.loader.exec_module(helper)


class SerialPermissionsTests(unittest.TestCase):
    def test_scopes_rule_to_usb_identity_not_node_number(self):
        usb = helper.UsbSerial("303A", "1001", "test-unit-1")
        rule = usb.rule("dialout")
        self.assertIn('SUBSYSTEM=="tty"', rule)
        self.assertIn('ATTRS{idVendor}=="303a"', rule)
        self.assertIn('ATTRS{serial}=="test-unit-1"', rule)
        self.assertIn('GROUP:="dialout", MODE:="0660"', rule)
        self.assertNotIn("ttyACM", rule)
        self.assertNotEqual(usb.filename(), helper.UsbSerial("303a", "1001", "test-unit-2").filename())

    def test_rejects_rule_injection_and_missing_identity(self):
        for vendor, product, serial, group in [
            ("*", "1001", "unit", "dialout"),
            ("303a", "*", "unit", "dialout"),
            ("303a", "1001", "", "dialout"),
            ("303a", "1001", 'unit", MODE="0666', "dialout"),
            ("303a", "1001", "unit", 'dialout", RUN+="command'),
        ]:
            with self.subTest(serial=serial, group=group), self.assertRaises(ValueError):
                helper.UsbSerial(vendor, product, serial).rule(group)

    def test_reads_attributes_from_same_usb_parent_and_requires_serial(self):
        with tempfile.TemporaryDirectory() as directory:
            usb = Path(directory)
            device = usb / "interface" / "tty"
            device.mkdir(parents=True)
            (usb / "idVendor").write_text("303a\n")
            (usb / "idProduct").write_text("1001\n")
            with self.assertRaisesRegex(ValueError, "no unique serial"):
                helper.read_identity(device)
            (usb / "serial").write_text("test-unit\n")
            self.assertEqual(helper.read_identity(device), helper.UsbSerial("303a", "1001", "test-unit"))

    def test_install_is_idempotent_but_does_not_overwrite_other_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.rules"
            rule = helper.UsbSerial("303a", "1001", "test-unit").rule("dialout")
            helper.write_rule(path, rule)
            helper.write_rule(path, rule)
            with self.assertRaisesRegex(ValueError, "Existing rule differs"):
                helper.write_rule(path, "other rule\n")
            self.assertEqual(path.read_text(), rule)
            link = Path(directory) / "link.rules"
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "symlink"):
                helper.write_rule(link, rule)

    def test_observed_group_enrollment_requires_safe_group(self):
        with patch.object(helper.grp, "getgrgid", side_effect=KeyError), patch.object(helper.grp, "getgrnam", side_effect=KeyError):
            self.assertEqual(helper.observed_group(984), ("mpbuild-serial-984", True))
            with self.assertRaisesRegex(ValueError, "low/system"):
                helper.observed_group(0)
        with patch.object(helper.grp, "getgrgid", return_value=helper.grp.struct_group(("docker", "x", 984, []))):
            with self.assertRaisesRegex(ValueError, "privileged"):
                helper.observed_group(984)
        with patch.object(helper.grp, "getgrgid", side_effect=KeyError), patch.object(helper.grp, "getgrnam", return_value=helper.grp.struct_group(("mpbuild-serial-984", "x", 985, []))):
            with self.assertRaisesRegex(ValueError, "another ID"):
                helper.observed_group(984)


if __name__ == "__main__":
    unittest.main()
