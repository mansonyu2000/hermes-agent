#!/usr/bin/env python3
"""
WinPeek 质量检查 — 对标 Hermes 上游的 lint + footgun checker。

用法:
  python scripts/winpeek-quality-check.py              # 全量扫描 WinPeek 代码+文档
  python scripts/winpeek-quality-check.py --diff DEV   # 只在文件变更上报告

退出码:
  0 — 全部通过
  1 — 至少一项违反 (CI 堵门)

检查项:
  1. TypeScript typecheck   (pnpm typecheck, apps/desktop)
  2. CSS token 检查          (禁止硬编码颜色)
  3. Python ruff 检查        (plugins/winpeek_rpa/)
  4. 文档 frontmatter 检查    (website/docs/winpeek/ 下每个 .md)
  5. 文件命名检查             (禁止大写字母文件名)
  6. 文档死链检查             (相对路径 .md 引用必须存在)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── 规则定义 ──────────────────────────────────────────────

# 死链检查只允许在 docs/website/winpeek/ 范围内解析相对路径。
# 任何试图通过 .. 逃逸到上层目录的引用都会被拒绝。
DOCS_ALLOWED_DIR = (REPO_ROOT / "website" / "docs" / "winpeek").resolve()
DOCS_WEBSITE_ROOT = (REPO_ROOT / "website" / "docs").resolve()

CSS_TOKEN_EXEMPT = [
    "0,0,0", "255,255,255",                 # black/white
    "transparent", "inherit", "currentColor",
    "none",
    "0%", "100%",
]

DOC_EXEMPT_FILES = [
    "_category_.json",
    "README.md",
]

FRONTMATTER_REQUIRED = ["sidebar_position", "title"]

def find_files(patterns: list[str], diff_base: str | None = None) -> list[Path]:
    """找出需要检查的文件。如果指定 diff_base，只返回变更文件。"""
    if diff_base:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", diff_base, "--", *patterns],
            cwd=REPO_ROOT, text=True
        ).strip()
        return [REPO_ROOT / f for f in out.split("\n") if f]
    else:
        files: list[Path] = []
        for pat in patterns:
            files.extend(REPO_ROOT.glob(pat))
        return files


# ═══════════════════════════════════════════════════════
# 检查 1: TypeScript
# ═══════════════════════════════════════════════════════

def check_typescript(diff_base: str | None = None) -> list[str]:
    errors: list[str] = []
    desktop_dir = REPO_ROOT / "apps" / "desktop"

    if not (desktop_dir / "node_modules").exists():
        errors.append("node_modules 未安装 — 请运行 npm install")
        return errors

    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=desktop_dir, capture_output=True, text=True
    )
    if result.returncode != 0:
        for line in result.stdout.strip().split("\n"):
            if "error TS" in line:
                errors.append(f"[TS] {line.strip()}")
    return errors


# ═══════════════════════════════════════════════════════
# 检查 2: CSS token — 禁止硬编码颜色
# ═══════════════════════════════════════════════════════

CSS_HARDCODED_RE = re.compile(
    r'(?:color|background|bg|fill|stroke|border)\s*[=:]\s*["\']'
    r'(?!(?:var\(--|transparent|inherit|currentColor|none))'
    r'(#[0-9a-fA-F]{3,8}|rgb\(|hsl\()',
)

def check_css_tokens(diff_base: str | None = None) -> list[str]:
    errors: list[str] = []
    patterns = ["apps/desktop/src/app/winpeek/**/*.tsx", "apps/desktop/src/app/winpeek/**/*.ts"]
    for f in find_files(patterns, diff_base):
        content = f.read_text(encoding="utf-8")
        for i, line in enumerate(content.split("\n"), 1):
            if CSS_HARDCODED_RE.search(line):
                errors.append(f"[CSS] {f}:{i} — 硬编码颜色, 请用 CSS token (e.g. var(--ui-accent))")
    return errors


# ═══════════════════════════════════════════════════════
# 检查 3: Python ruff (复用 Hermes pyproject.toml 规则)
# ═══════════════════════════════════════════════════════

def check_python_ruff(diff_base: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        result = subprocess.run(
            ["ruff", "check", "plugins/winpeek_rpa/"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
        if result.returncode != 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    errors.append(f"[Python] {line.strip()}")
    except FileNotFoundError:
        errors.append("[Python] ruff 未安装 — pip install ruff")
    return errors


# ═══════════════════════════════════════════════════════
# 检查 4: 文档 frontmatter
# ═══════════════════════════════════════════════════════

def check_doc_frontmatter(diff_base: str | None = None) -> list[str]:
    errors: list[str] = []
    patterns = ["website/docs/winpeek/**/*.md", "website/docs/winpeek/**/*.mdx"]
    for f in find_files(patterns, diff_base):
        if f.name in DOC_EXEMPT_FILES:
            continue
        content = f.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append(f"[DOC] {f} — 缺少 YAML frontmatter (--- ... ---)")
            continue
        frontmatter = content.split("---", 2)[1] if content.count("---", 0, 10) >= 2 else ""
        for key in FRONTMATTER_REQUIRED:
            if key not in frontmatter:
                errors.append(f"[DOC] {f} — 缺少 {key} frontmatter 字段")
    return errors


# ═══════════════════════════════════════════════════════
# 检查 5: 文件命名 — website/ 下禁止大写字母
# ═══════════════════════════════════════════════════════

FILENAME_UPPERCASE_RE = re.compile(r'[A-Z]')

def check_filename_case(diff_base: str | None = None) -> list[str]:
    errors: list[str] = []
    patterns = ["website/docs/winpeek/**/*.md", "website/docs/winpeek/**/*.mdx"]
    for f in find_files(patterns, diff_base):
        if f.name in DOC_EXEMPT_FILES:
            continue
        if FILENAME_UPPERCASE_RE.search(f.name):
            errors.append(
                f"[NAME] {f} — 文件名含大写字母, "
                f"建议 {f.with_name(f.name.lower()).name}"
            )
    return errors


# ═══════════════════════════════════════════════════════
# 检查 6: 死链 — 指向不存在的 .md 引用
# ═══════════════════════════════════════════════════════

LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def check_dead_links(diff_base: str | None = None) -> list[str]:
    errors: list[str] = []
    patterns = ["website/docs/winpeek/**/*.md", "website/docs/winpeek/**/*.mdx"]
    for f in find_files(patterns, diff_base):
        content = f.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(content):
            target = match.group(2)
            if target.startswith("http") or target.startswith("#"):
                continue
            # Reject path traversal — only allow links within website/docs/
            if ".." in target or target.startswith("/"):
                errors.append(
                    f"[LINK] {f}:{content[:match.start()].count(chr(10)) + 1}"
                    f" → {target} (禁止路径逃逸/绝对路径)"
                )
                continue
            resolved = (f.parent / target).resolve()
            try:
                resolved.relative_to(DOCS_WEBSITE_ROOT)
            except ValueError:
                errors.append(
                    f"[LINK] {f}:{content[:match.start()].count(chr(10)) + 1}"
                    f" → {target} (解析后越界)"
                )
                continue
            if resolved.exists() or (f.parent / f"{target}.mdx").resolve().exists():
                continue
            if resolved.suffix in (".png", ".jpg", ".svg", ".gif", ".pdf"):
                if resolved.exists():
                    continue
            errors.append(
                f"[LINK] {f}:{content[:match.start()].count(chr(10)) + 1}"
                f" → {target} (文件不存在)"
            )
    return errors


# ═══════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════

CHECKS = [
    ("TypeScript 类型检查",    check_typescript),
    ("CSS token 检查",         check_css_tokens),
    ("Python ruff 检查",       check_python_ruff),
    ("文档 frontmatter 检查",  check_doc_frontmatter),
    ("文件命名规范",            check_filename_case),
    ("死链检查",               check_dead_links),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="WinPeek Quality Check")
    parser.add_argument("--diff", metavar="BASE_REF",
                        help="Only check files changed vs BASE_REF")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON for CI consumption")
    parser.add_argument("--check", metavar="NAME",
                        help="Run only a specific check")
    args = parser.parse_args()

    all_errors: dict[str, list[str]] = {}
    for name, fn in CHECKS:
        if args.check and args.check.lower() not in name.lower():
            continue
        try:
            errs = fn(args.diff)
            all_errors[name] = errs
        except Exception as e:
            all_errors[name] = [f"{name} failed: {e}"]

    total = sum(len(v) for v in all_errors.values())

    if args.json:
        json.dump(all_errors, sys.stdout, indent=2, ensure_ascii=False)
        return 1 if total > 0 else 0

    passed = total == 0
    status = "PASS" if passed else f"FAIL ({total} violations)"
    print(f"\nWinPeek Quality Check ({'diff' if args.diff else 'full'}) — {status}\n")
    for name, errs in all_errors.items():
        print(f"  {len(errs):>3}  {name}")
        for e in errs:
            print(f"       {e}")

    return 1 if total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
