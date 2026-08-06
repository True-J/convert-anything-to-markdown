"""Smoke tests for scripts/install.py.

These tests guard against the BUNDLED_SRC regression that shipped in
v1.0.x - v1.3.6, where the installer pointed at <kit>/src/src/ (a
nonexistent path) and every installer fallback failed.

We deliberately avoid actually invoking `pip` / `uv` / `pipx` here so the
tests stay fast and hermetic. The check is: the script's BUNDLED_SRC
constant must resolve to the directory that holds pyproject.toml.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_SRC = Path(__file__).resolve().parent.parent  # <kit>/src
INSTALL_PY = REPO_SRC / "scripts" / "install.py"


@pytest.fixture
def install_module():
    """Import scripts/install.py as a module so we can introspect constants."""
    spec = importlib.util.spec_from_file_location("_cam_install", INSTALL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_cam_install"] = module
    spec.loader.exec_module(module)
    return module


def test_bundled_src_points_at_pyproject_directory(install_module):
    """The CRITICAL regression: BUNDLED_SRC must equal <kit>/src/.

    The 1.3.x regression appended an extra "/ src" segment so
    BUNDLED_SRC came out as <kit>/src/src/ - a path that does not
    exist. uv / pipx / pip all then refused to install from it.
    """
    pyproject = install_module.BUNDLED_SRC / "pyproject.toml"
    assert pyproject.is_file(), (
        f"BUNDLED_SRC={install_module.BUNDLED_SRC} does not contain "
        "pyproject.toml; the installer would fail in production. "
        "Likely cause: an extraneous '/ \"src\"' suffix was added back to "
        "the BUNDLED_SRC calculation."
    )


def test_bundled_src_is_package_root(install_module):
    """BUNDLED_SRC should also contain the convert_anything_md package dir."""
    package_dir = install_module.BUNDLED_SRC / "convert_anything_md"
    assert package_dir.is_dir(), (
        "BUNDLED_SRC must contain the convert_anything_md package "
        "directory; otherwise the installer ships an empty wheel."
    )


def test_pyproject_version_matches_runtime_version(install_module):
    """A version drift between pyproject.toml and version.py masked v1.3.x bugs.

    v1.3.5 shipped with the kit manifest declaring v1.3.5 while
    version.py still printed v1.0.0. Catch that regression here.
    """
    pyproject = (install_module.BUNDLED_SRC / "pyproject.toml").read_text()
    # crude but dep-free: find `version = "X.Y.Z"`
    import re

    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, flags=re.MULTILINE)
    assert match, "could not locate version in pyproject.toml"
    pyproject_version = match.group(1)

    from convert_anything_md.version import __version__

    assert pyproject_version == __version__, (
        f"version drift: pyproject.toml says {pyproject_version}, "
        f"convert_anything_md.version.__version__ says {__version__}"
    )
