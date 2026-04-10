import re
from typing import List


def compress(content: str, file_ext: str) -> str:
    """Transform source file into a compact, readable skeleton for LLM consumption."""
    if file_ext == ".java":
        return _compress_java(content)
    if file_ext in (".py",):
        return _compress_python(content)
    # fallback: strip blank lines and comments only
    return _strip_generic(content)


# ── Java ──────────────────────────────────────────────────────────────────────

def _compress_java(src: str) -> str:
    lines = src.splitlines()
    out: List[str] = []

    # package
    for line in lines:
        s = line.strip()
        if s.startswith("package "):
            out.append(s)
            break

    # imports — collapse to unique top-level packages
    imports = set()
    for line in lines:
        s = line.strip()
        if s.startswith("import "):
            pkg = s.removeprefix("import ").removesuffix(";").strip()
            top = ".".join(pkg.split(".")[:2])
            imports.add(f"import {top}.*")
    if imports:
        out.append("")
        out.extend(sorted(imports))

    # class/interface/enum declaration + annotations + fields + method sigs
    out.append("")
    in_block_comment = False
    brace_depth = 0
    method_brace_start = None  # depth at which a method body opened

    for line in lines:
        s = line.strip()

        # block comment handling
        if "/*" in s:
            in_block_comment = True
        if in_block_comment:
            if "*/" in s:
                in_block_comment = False
            continue
        if s.startswith("//"):
            continue
        if not s:
            continue

        # track brace depth
        opens = s.count("{")
        closes = s.count("}")

        # class / interface / enum declaration (depth 0)
        if brace_depth == 0 and re.search(r'\b(class|interface|enum|record)\b', s):
            out.append(s.split("{")[0].strip() + " {")
            if opens > closes:
                brace_depth += opens - closes
            continue

        # annotations at any depth
        if s.startswith("@") and brace_depth <= 1:
            out.append("  " + s)
            continue

        # fields at class body level (depth 1)
        if brace_depth == 1 and not s.startswith("}"):
            is_method = bool(re.search(r'\b\w+\s*\(', s)) and ("{" in s or s.endswith(";") is False)
            is_field = (
                re.search(r'\b(private|protected|public|static|final)\b', s)
                and "(" not in s
                and s.endswith(";")
            )
            if is_field:
                out.append("  " + s)
                brace_depth += opens - closes
                continue

        # method signatures at class body level (depth 1)
        if brace_depth == 1 and re.search(r'\b(public|protected|private|static|void|final)\b', s) and "(" in s:
            sig = s.split("{")[0].strip()
            out.append("  " + sig + (" {}" if "{" in s else ";"))
            if opens > closes:
                brace_depth += opens - closes
                method_brace_start = brace_depth
            continue

        # update depth for everything else (method bodies we skip)
        brace_depth += opens - closes

        # closing brace back to class level
        if brace_depth == 1 and method_brace_start is not None:
            method_brace_start = None

        if brace_depth == 0 and s == "}":
            out.append("}")

    return "\n".join(out)


# ── Python ────────────────────────────────────────────────────────────────────

def _compress_python(src: str) -> str:
    out: List[str] = []
    lines = src.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        # imports
        if s.startswith("import ") or s.startswith("from "):
            out.append(line)
        # class / def signatures
        elif s.startswith("class ") or s.startswith("def ") or re.match(r'\s+(def |async def )', line):
            out.append(line.rstrip().rstrip(":") + ":")
            # include docstring if present
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt.startswith('"""') or nxt.startswith("'''"):
                    out.append(lines[i + 1])
        i += 1
    return "\n".join(out)


# ── Generic ───────────────────────────────────────────────────────────────────

def _strip_generic(src: str) -> str:
    out = []
    for line in src.splitlines():
        s = line.strip()
        if s and not s.startswith("//") and not s.startswith("#"):
            out.append(line)
    return "\n".join(out)
