import os
import fnmatch
from dataclasses import dataclass
from typing import List


SPRING_PRIORITY_ANNOTATIONS = [
    "@SpringBootApplication",
    "@RestController",
    "@Controller",
    "@Service",
    "@Repository",
    "@Entity",
    "@Configuration",
]

SECRET_PATTERNS = [".env", "*.pem", "*.key", "*secret*", "*credential*"]


@dataclass
class FileChunk:
    path: str
    content: str
    priority: int = 0  # higher = more important


def collect_chunks(root: str, hint: str, ignore_patterns: List[str]) -> List[FileChunk]:
    """Phase 3: collect and prioritize source files for worker agents."""
    chunks = []

    if hint == "spring-boot":
        src_root = os.path.join(root, "src", "main", "java")
        if os.path.exists(src_root):
            for path in _walk_files(src_root, [".java"], ignore_patterns):
                content = _safe_read(path)
                priority = _spring_priority(content)
                chunks.append(FileChunk(path=path, content=content, priority=priority))
    else:
        for path in _walk_files(root, [".py", ".js", ".ts", ".java", ".go", ".rb"], ignore_patterns):
            content = _safe_read(path)
            chunks.append(FileChunk(path=path, content=content, priority=0))

    chunks.sort(key=lambda c: c.priority, reverse=True)
    return chunks


def _walk_files(root: str, extensions: List[str], ignore_patterns: List[str]) -> List[str]:
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _is_ignored(os.path.join(dirpath, d), ignore_patterns)]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            if any(fname.endswith(ext) for ext in extensions) and not _is_secret(fname):
                if not _is_ignored(fpath, ignore_patterns):
                    results.append(fpath)
    return results


def _is_ignored(path: str, patterns: List[str]) -> bool:
    name = os.path.basename(path)
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern.rstrip("/**")) or fnmatch.fnmatch(path, pattern):
            return True
    return False


def _is_secret(filename: str) -> bool:
    return any(fnmatch.fnmatch(filename.lower(), p) for p in SECRET_PATTERNS)


def _spring_priority(content: str) -> int:
    return sum(1 for ann in SPRING_PRIORITY_ANNOTATIONS if ann in content)


def _safe_read(path: str) -> str:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()
