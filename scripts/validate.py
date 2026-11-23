#!/usr/bin/env python3
"""Validate marketplace metadata, skills, and generated serial helpers."""

import argparse
import json
from pathlib import Path, PureWindowsPath
import re
import sys


ALIASES = (".github/plugin/marketplace.json", ".claude-plugin/marketplace.json")
PRIMARY_SERIAL_HELPER = "plugins/mpremote/skills/mpremote/scripts/setup_serial_permissions.py"
GENERATED_SERIAL_HELPERS = (
    "plugins/mpflash/skills/mpflash/scripts/setup_serial_permissions.py",
    "plugins/mpbuild/skills/mpbuild/scripts/setup_serial_permissions.py",
)
NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fields(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected a JSON object")
    return value


def string_field(value: dict[str, object], key: str, label: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"{label}: missing {key}")
    return result


def load_json(path: Path) -> dict[str, object]:
    return fields(json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_json_constant), str(path))


def reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def equal_json(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal_json(value, right[key]) for key, value in left.items())
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equal_json(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def validate(root: Path, sync: bool = False) -> None:
    catalog = load_json(root / "marketplace.json")
    primary = root / PRIMARY_SERIAL_HELPER
    require(primary.exists(), f"Missing canonical serial helper: {PRIMARY_SERIAL_HELPER}")
    serial_helper = primary.read_bytes()

    if sync:
        for alias in ALIASES:
            path = root / alias
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        for relative in GENERATED_SERIAL_HELPERS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(serial_helper)

    for relative in GENERATED_SERIAL_HELPERS:
        path = root / relative
        hint = f"{relative}; run python3 scripts/validate.py --sync"
        require(path.exists(), f"Missing generated serial helper: {hint}")
        require(path.read_bytes() == serial_helper, f"Generated serial helper differs: {hint}")
    for alias in ALIASES:
        require(equal_json(load_json(root / alias), catalog), f"{alias} differs from the root catalog")

    name = string_field(catalog, "name", "Marketplace")
    require(NAME_PATTERN.fullmatch(name) is not None, "Invalid marketplace name")
    string_field(fields(catalog.get("owner"), "Marketplace owner"), "name", "Marketplace owner")
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValueError("Missing plugins")
    names: set[str] = set()

    for item in plugins:
        entry = fields(item, "Plugin entry")
        name = string_field(entry, "name", "Plugin entry")
        require(NAME_PATTERN.fullmatch(name) is not None and name not in names, f"Invalid/duplicate plugin: {name}")
        names.add(name)
        source = string_field(entry, "source", name)
        require(source.startswith("./plugins/"), "Expected a local plugin source")
        require(".." not in re.split(r"[\\/]", source), "Plugin source must not escape the repository")
        plugin_root = (root / source).resolve()
        require(plugin_root.exists(), f"Missing source: {source}")
        portable = load_json(plugin_root / "plugin.json")
        claude = load_json(plugin_root / ".claude-plugin/plugin.json")
        require(portable.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", f"{name}: invalid schema")
        shared = {key: value for key, value in portable.items() if key != "$schema"}
        require(equal_json(claude, shared), f"{name}: plugin manifests differ")
        for key in ("name", "version", "description"):
            require(portable.get(key) == string_field(entry, key, name), f"{name}: mismatched {key}")
        version = string_field(entry, "version", name)
        require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is not None, f"{name}: invalid version")
        require(portable.get("repository") == "https://github.com/josverl/mp-agents", f"{name}: invalid repository")
        require(portable.get("license") == "MIT", f"{name}: invalid license")
        for filename in ("README.md", "CHANGELOG.md"):
            require((plugin_root / filename).exists(), f"{name}: missing {filename}")
        require(f"## {version}" in (plugin_root / "CHANGELOG.md").read_text(encoding="utf-8"), f"{name}: missing changelog version")
        skills_root = plugin_root / "skills"
        skills = [path for path in skills_root.iterdir() if path.is_dir()]
        require(bool(skills), f"{name}: missing skills")
        for skill in skills:
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            frontmatter = re.match(r"^---\r?\nname: ([a-z0-9-]+)\r?\ndescription: ([^\r\n]+)\r?\n---\r?\n", text)
            if frontmatter is None or frontmatter[1] != skill.name or NAME_PATTERN.fullmatch(skill.name) is None:
                raise ValueError(f"Invalid skill: {skill.name}")
            require(len(frontmatter[2].strip()) <= 1024, f"{skill.name}: description too long")
            require(len(re.findall(r"^```", text, re.MULTILINE)) % 2 == 0, f"{skill.name}: unbalanced fences")
            for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
                target = match[1]
                if re.match(r"^https?://", target) or target.startswith("#"):
                    continue
                relative = target.split("#")[0]
                require(not Path(relative).is_absolute() and not PureWindowsPath(relative).is_absolute(), f"{skill.name}: absolute resource link")
                resolved = (skill / relative).resolve()
                require(resolved.is_relative_to(plugin_root), f"{skill.name}: resource escapes plugin")
                require(resolved.exists(), f"{skill.name}: missing resource {relative}")

    print(f"Validated {len(plugins)} plugin(s), three catalogs, manifests, skills, and generated serial helpers.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="Regenerate catalog aliases and bundled serial helper copies")
    args = parser.parse_args()
    validate(Path(__file__).resolve().parents[1], sync=args.sync)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
