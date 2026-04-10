import os
import glob
from typing import Optional


SPRING_INDICATORS = {"pom.xml", "mvnw", "gradlew", "build.gradle"}
SECRET_FILES = {".env", "application-prod.yml", "application-prod.properties"}


def discover(root: str) -> dict:
    """Phase 1 & 2: scan root, detect project type, ingest docs."""
    root_entries = set(os.listdir(root))

    hint = _detect_hint(root_entries, root)
    readme = _find_readme(root)
    config_files = _find_config_files(root, hint)

    return {
        "root": root,
        "hint": hint,
        "readme_content": _read_file(readme) if readme else None,
        "config_files": {name: _read_file(path) for name, path in config_files.items()},
    }


def _detect_hint(entries: set, root: str) -> str:
    if SPRING_INDICATORS & entries:
        return "spring-boot"
    if "package.json" in entries:
        return "node"
    if "manage.py" in entries:
        return "django"
    return "generic"


def _find_readme(root: str) -> Optional[str]:
    for name in ["README.md", "readme.md", "Readme.md"]:
        path = os.path.join(root, name)
        if os.path.exists(path):
            return path
    md_files = glob.glob(os.path.join(root, "*.md")) + glob.glob(os.path.join(root, "docs", "*.md"))
    return md_files[0] if md_files else None


def _find_config_files(root: str, hint: str) -> dict:
    candidates = {
        "pom.xml": os.path.join(root, "pom.xml"),
        "build.gradle": os.path.join(root, "build.gradle"),
        "application.yml": os.path.join(root, "src", "main", "resources", "application.yml"),
        "application.properties": os.path.join(root, "src", "main", "resources", "application.properties"),
    }
    return {k: v for k, v in candidates.items() if os.path.exists(v)}


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()
