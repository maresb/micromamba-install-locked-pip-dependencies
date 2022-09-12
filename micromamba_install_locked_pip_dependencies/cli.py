#!/usr/bin/env python3

import argparse
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional


def main():
    args = parse_args()
    if args.category is None:
        category = ["main"]
    else:
        category = args.category
    packages: Dict[str, Dict[str, str]] = parse_yaml(
        args.lockfile.read_text(), args.platform
    )
    pip_packages = {
        package_name: package
        for package_name, package in packages.items()
        if package.get("manager") == "pip"
    }
    pip_packages_to_install = {
        package_name: package
        for package_name, package in pip_packages.items()
        if package.get("category") in category
    }
    if len(pip_packages_to_install) > 0:
        packages_missing_urls = [
            package["name"]
            for package in pip_packages_to_install.values()
            if "url" not in package
        ]
        if len(packages_missing_urls) > 0:
            raise ValueError(
                f"The following packages are missing a URL: {packages_missing_urls}"
            )
        urls = [package["url"] for package in pip_packages_to_install.values()]
        with tempfile.NamedTemporaryFile() as tf:
            tf.write("\n".join(urls).encode())
            tf.seek(0)
            cmd = [
                str(args.pip_location),
                "uninstall" if args.uninstall else "install",
                "--no-cache-dir",
                "--requirement",
                tf.name,
            ]
            if args.uninstall:
                cmd.append("--yes")
            else:
                cmd.append("--no-deps")
            if args.dry_run:
                print("Planning to run:\n\n    ", end="")
                if sys.version_info >= (3, 8):
                    print(shlex.join(cmd))
                else:
                    print(" ".join(cmd))
                print(f"\nwhere the file {tf.name} contains:\n\n    ", end="")
                print("\n    ".join(tf.read().decode().splitlines()))
                cmd.append("--dry-run")
                if not args.uninstall:
                    print("\nRunning the above command with --dry-run:\n")
                    subprocess.run(cmd, check=True)
            else:
                subprocess.run(cmd, check=True)
    else:
        if args.dry_run:
            print("No packages found to install.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install pip dependencies from new-style lockfiles"
    )
    parser.add_argument(
        "-f",
        "--lockfile",
        help="Filename of the lockfile (default 'conda-lock.yml')",
        default="conda-lock.yml",
        type=Path,
    )
    parser.add_argument(
        "-c",
        "--category",
        help="Category to install (default 'main')",
        action="append",
        type=str,
    )
    parser.add_argument(
        "--dry-run",
        help="Do not actually install anything",
        action="store_true",
    )
    parser.add_argument(
        "--uninstall",
        help="Do not actually install anything",
        action="store_true",
    )
    parser.add_argument(
        "--pip-location",
        help="Location of pip executable",
        default=Path("pip"),
        type=Path,
    )
    parser.add_argument(
        "--platform",
        help="Override the detected installation platform",
        default=None,
        type=str,
    )
    args = parser.parse_args()
    return args


def parse_yaml(s: str, specified_platform: Optional[str]) -> Dict[str, Dict[str, str]]:
    """Crudely parse a YAML file into a packages dict.

    Finds the top-level "packages" entry.
    Each list item from the YAML becomes a key-value pair in the resulting dict.
    The key is the name of the package.
    The value is a dict of key-value pairs from the YAML where the key and value
    appear on the same line.
    """
    try:
        computed_platform = get_platform_prefix()
    except ValueError as e:
        print(e, file=sys.stderr)
        if specified_platform is None:
            raise ValueError(
                "Could not determine platform (perhaps because Windows isn't "
                "supported?). One must be specified manually with --platform."
            )
        computed_platform = specified_platform
    if specified_platform is not None:
        if computed_platform != specified_platform:
            print(
                f"Warning: Specified platform {specified_platform} does not match "
                f"computed platform {computed_platform}."
            )
        active_platform = specified_platform
    else:
        active_platform = computed_platform
    packages: Dict[str, Dict[str, str]] = {}
    current_package: Optional[Dict[str, str]] = None
    encountered_package_header = False
    package_list_indentation = None
    package_indentation = None
    line_no = 0
    for line_no, line in enumerate(s.splitlines(), start=1):
        if not encountered_package_header:
            encountered_package_header = line == "package:"
            # We are before the top-level package section
            continue
        if line.strip() == "" or line.strip().startswith("#"):
            # Ignore empty lines and comments
            continue
        if package_list_indentation is None:
            # The first content line after the package header must be a list item.
            # The list deliminter is the "-" character. Determine its indentation.
            package_list_indentation = line.index("-")
        # We are now considering a content line after the start of the package section.
        if not line.startswith(" " * package_list_indentation):
            # The content line lacks the indentation to belong to the package section.
            # We are done with the package section.
            break
        # The content line belongs to the package section.
        # Dedent to the level of "-" and call this line2.
        line2 = line[package_list_indentation:]
        # Note that line2 cannot be empty, because otherwise it would consist only
        # of spaces, and we already filtered lines containing only spaces.
        if line2[0] == "-":
            # We are at the beginning of a new package entry.
            if current_package is not None:
                _add_package_to_package_dict(
                    packages, current_package, line_no, active_platform
                )
            current_package = {}
            line2 = " " + line2[1:]
            package_indentation = len(line2) - len(line2.lstrip())
        if package_indentation is None or current_package is None:
            raise ValueError(
                f"Package section does not start with a "
                f"list item at line {line_no}: {line}"
            )
        if not line2.startswith(" " * package_indentation):
            # The content line lacks the indentation to belong to the package section.
            # We are done with the package section.
            break
        # Dedent to the level of top-level keys within a package entry.
        line3 = line2[package_indentation:]
        if line3[0] == "" or line3.lstrip()[0] == "#":
            raise ValueError(
                f"Empty list item in package section at line {line_no}: {line}"
            )
        if line3[0] == " ":
            # This line is indented beyond the top-level keys.
            continue
        if ":" not in line3:
            raise ValueError(f"Missing ':' delimiter in line {line_no}: {line}")
        key, value = line3.split(":", 1)
        key = key.strip()
        value = value.strip()
        # Also strip quotes from the value, if present.
        if len(value) >= 2:
            if value[0] == value[-1] == '"':
                value = value[1:-1]
            elif value[0] == value[-1] == "'":
                value = value[1:-1]
        if key == "":
            raise ValueError(f"Empty key in line {line_no}: {line}")
        if value != "":
            current_package[key] = value

    if current_package is not None:
        _add_package_to_package_dict(
            packages, current_package, line_no, active_platform
        )
    return packages


def _add_package_to_package_dict(
    packages: dict, current_package: dict, line_no: int, active_platform: Optional[str]
):
    if "name" not in current_package:
        raise ValueError(f"Package at line {line_no} has no name")
    if "platform" not in current_package:
        raise ValueError(f"Package at line {line_no} has no platform")
    name = current_package["name"]
    if current_package["platform"] == active_platform:
        if name in packages:
            raise ValueError(f"Duplicate package {name!r} at line {line_no!r}")
        packages[name] = current_package


def get_platform_prefix():
    """Following the logic of <https://micro.mamba.pm/install.sh>"""
    # Execute uname -m to get the architecture
    arch = subprocess.check_output(["uname", "-m"]).decode().strip()
    os = subprocess.check_output(["uname"]).decode().strip()
    if os == "Linux":
        platform = "linux"
        if arch not in ["aarch64", "ppc64le"]:
            arch = "64"
    elif os == "Darwin":
        platform = "osx"
        if arch not in ["arm64"]:
            arch = "64"
    else:
        raise ValueError(f"Unsupported platform: {os}")
    prefix = f"{platform}-{arch}"
    return prefix


if __name__ == "__main__":
    main()
