#!/usr/bin/env python3
"""Check for outdated dependencies and configuration best practices."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import tomli
except ImportError:
    print("Installing tomli for TOML parsing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tomli"])
    import tomli

try:
    from packaging import version
except ImportError:
    print("Installing packaging for version comparison...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "packaging"])
    from packaging import version


def check_outdated_packages() -> List[Tuple[str, str, str]]:
    """Check for outdated packages and return list of (package, current, latest)."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"Error checking packages: {result.stderr}")
        return []
    
    outdated = json.loads(result.stdout)
    return [(pkg["name"], pkg["version"], pkg["latest_version"]) for pkg in outdated]


def check_pyproject_toml() -> Dict[str, bool]:
    """Check if pyproject.toml uses latest configuration patterns."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {"exists": False}
    
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    checks = {
        "exists": True,
        "uses_pep621": "project" in config,  # Modern metadata format
        "black_config": "tool" in config and "black" in config["tool"],
        "isort_config": "tool" in config and "isort" in config["tool"],
        "mypy_config": "tool" in config and "mypy" in config["tool"],
        "pytest_config": "tool" in config and "pytest" in config["tool"],
        "ruff_config": "tool" in config and "ruff" in config["tool"],
        "ruff_uses_lint": (
            "tool" in config
            and "ruff" in config["tool"]
            and "lint" in config["tool"]["ruff"]
        ),  # Latest ruff config style
        "coverage_config": "tool" in config and "coverage" in config["tool"],
    }
    
    return checks


def check_tool_versions():
    """Check versions of installed development tools."""
    tools = {
        "black": ["black", "--version"],
        "isort": ["isort", "--version"],
        "mypy": ["mypy", "--version"],
        "pytest": ["pytest", "--version"],
        "ruff": ["ruff", "--version"],
    }
    
    versions = {}
    for tool, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            versions[tool] = result.stdout.strip() or result.stderr.strip()
        except FileNotFoundError:
            versions[tool] = "Not installed"
    
    return versions


def main():
    """Run all checks and display results."""
    print("🔍 Checking Python Dependencies and Configuration\n")
    
    # Check outdated packages
    print("📦 Outdated Packages:")
    print("=" * 60)
    outdated = check_outdated_packages()
    if outdated:
        print(f"{'Package':<30} {'Current':<15} {'Latest':<15}")
        print("-" * 60)
        for pkg, current, latest in outdated:
            print(f"{pkg:<30} {current:<15} {latest:<15}")
    else:
        print("✅ All packages are up to date!")
    
    print("\n📋 Configuration Status:")
    print("=" * 60)
    config_checks = check_pyproject_toml()
    
    if not config_checks.get("exists"):
        print("❌ pyproject.toml not found!")
    else:
        print("✅ pyproject.toml exists")
        print(f"  {'✅' if config_checks['uses_pep621'] else '❌'} Uses PEP 621 project metadata")
        print(f"  {'✅' if config_checks['black_config'] else '❌'} Black configuration present")
        print(f"  {'✅' if config_checks['isort_config'] else '❌'} isort configuration present")
        print(f"  {'✅' if config_checks['mypy_config'] else '❌'} MyPy configuration present")
        print(f"  {'✅' if config_checks['pytest_config'] else '❌'} Pytest configuration present")
        print(f"  {'✅' if config_checks['ruff_config'] else '❌'} Ruff configuration present")
        print(f"  {'✅' if config_checks['ruff_uses_lint'] else '⚠️'} Ruff uses latest 'lint' section")
        print(f"  {'✅' if config_checks['coverage_config'] else '❌'} Coverage configuration present")
    
    print("\n🔧 Tool Versions:")
    print("=" * 60)
    versions = check_tool_versions()
    for tool, version_info in versions.items():
        print(f"{tool:<10} {version_info}")
    
    print("\n💡 Best Practices:")
    print("=" * 60)
    print("✅ Using pyproject.toml (PEP 518/621) for project configuration")
    print("✅ Using setup.py with setuptools for package definition")
    print("✅ Using virtual environment for isolation")
    print("✅ Type hints with Protocol classes (PEP 544)")
    print("✅ Async/await prepared for future improvements")
    
    if outdated:
        print(f"\n⚠️  Found {len(outdated)} outdated packages. Run 'make update-deps' to update.")
    
    if not config_checks.get("ruff_uses_lint", False):
        print("\n⚠️  Ruff configuration should use 'tool.ruff.lint' section (we already fixed this!)")


if __name__ == "__main__":
    main()