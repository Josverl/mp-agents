import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mp-agents-validation-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / "plugins", self.root / "plugins")
        for relative in (
            "scripts/validate.py",
            "marketplace.json",
            ".github/plugin/marketplace.json",
            ".claude-plugin/marketplace.json",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)

    def validate(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(self.root / "scripts/validate.py"), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def passed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_generates_copies_and_rejects_drift_without_repairing_files(self):
        primary = self.root / "plugins/mpremote/skills/mpremote/scripts/setup_serial_permissions.py"
        copies = [
            self.root / f"plugins/{name}/skills/{name}/scripts/setup_serial_permissions.py"
            for name in ("mpflash", "mpbuild")
        ]
        with primary.open("ab") as stream:
            stream.write(b"\n# Canonical update for generation test.\n")
        canonical = primary.read_bytes()
        stale = [path.read_bytes() for path in copies]
        self.assertNotEqual(self.validate().returncode, 0)
        self.assertEqual([path.read_bytes() for path in copies], stale)
        self.passed(self.validate("--sync"))
        for path in copies:
            self.assertEqual(path.read_bytes(), canonical)
        self.passed(self.validate())

        for path in copies:
            with self.subTest(copy=path):
                with path.open("ab") as stream:
                    stream.write(b"\n# Unapproved replica edit.\n")
                drifted = path.read_bytes()
                failure = self.validate()
                self.assertNotEqual(failure.returncode, 0)
                self.assertIn("Generated serial helper differs", failure.stderr)
                self.assertEqual(path.read_bytes(), drifted)
                self.passed(self.validate("--sync"))
                self.assertEqual(primary.read_bytes(), canonical)
                self.assertEqual(path.read_bytes(), canonical)
                path.unlink()
                missing = self.validate()
                self.assertNotEqual(missing.returncode, 0)
                self.assertIn("Missing generated serial helper", missing.stderr)
                self.passed(self.validate("--sync"))
        self.passed(self.validate())

    def test_catalog_aliases_require_matching_json_types(self):
        catalog_path = self.root / "marketplace.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["metadata"]["strict_value"] = 1
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.passed(self.validate("--sync"))
        alias = self.root / ".github/plugin/marketplace.json"
        altered = json.loads(alias.read_text(encoding="utf-8"))
        altered["metadata"]["strict_value"] = True
        alias.write_text(json.dumps(altered), encoding="utf-8")
        failure = self.validate()
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("differs from the root catalog", failure.stderr)
        self.passed(self.validate("--sync"))

    def test_rejects_mismatched_manifests(self):
        path = self.root / "plugins/mpremote/.claude-plugin/plugin.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["version"] = "99.0.0"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        failure = self.validate()
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("plugin manifests differ", failure.stderr)

    def test_rejects_invalid_skill_frontmatter_fences_and_resource_links(self):
        path = self.root / "plugins/mpremote/skills/mpremote/SKILL.md"
        original = path.read_text(encoding="utf-8")
        cases = (
            (original.replace("name: mpremote\n", "name: other\n", 1), "Invalid skill"),
            (original + "\n```\n", "unbalanced fences"),
            (original + "\n[missing](missing.py)\n", "missing resource"),
            (original + "\n[escape](../../../README.md)\n", "resource escapes plugin"),
            (original + "\n[absolute](C:/outside.py)\n", "absolute resource link"),
        )
        for text, message in cases:
            with self.subTest(message=message):
                path.write_text(text, encoding="utf-8")
                failure = self.validate()
                self.assertNotEqual(failure.returncode, 0)
                self.assertIn(message, failure.stderr)
        path.write_text(original, encoding="utf-8")
        self.passed(self.validate())

    def test_rejects_invalid_metadata_and_cli_arguments(self):
        path = self.root / "marketplace.json"
        original = path.read_text(encoding="utf-8")
        for key, value, message in (
            ("version", "invalid", "invalid version"),
            ("source", "./plugins/../outside", "must not escape"),
        ):
            with self.subTest(key=key):
                catalog = json.loads(original)
                catalog["plugins"][0][key] = value
                if key == "version":
                    for relative in ("plugin.json", ".claude-plugin/plugin.json"):
                        manifest_path = self.root / "plugins/mpremote" / relative
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifest["version"] = value
                        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                path.write_text(json.dumps(catalog), encoding="utf-8")
                failure = self.validate("--sync")
                self.assertNotEqual(failure.returncode, 0)
                self.assertIn(message, failure.stderr)
        failure = self.validate("--unknown")
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("unrecognized arguments", failure.stderr)

    def test_rejects_nonstandard_json_constants(self):
        path = self.root / "marketplace.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        catalog["metadata"]["invalid_number"] = float("inf")
        path.write_text(json.dumps(catalog), encoding="utf-8")
        failure = self.validate("--sync")
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("Non-standard JSON constant", failure.stderr)


if __name__ == "__main__":
    unittest.main()
