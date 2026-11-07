from __future__ import annotations

import hashlib
import ast
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EXTENSIONS = {".py": "python", ".pyi": "python", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".ts": "typescript", ".tsx": "tsx"}
SKIP_DIRS = {".git", ".leancode", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".next"}
SYMBOL_KINDS = {"function_definition", "class_definition", "function_declaration", "class_declaration", "method_definition", "method_declaration", "interface_declaration", "type_alias_declaration", "enum_declaration"}
WORD = re.compile(r"[A-Za-z_$][\w$]*|\d+")


@dataclass
class Symbol:
    path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    signature: str
    identifiers: list[str]


def tokens(text: str) -> list[str]:
    return [word.lower() for word in WORD.findall(text)]


def _position(node: Any, name: str) -> int:
    point = getattr(node, name, None)
    if point is None:
        point = getattr(node, "start_position" if name == "start_point" else "end_position")
    row = getattr(point, "row", None)
    if row is None:
        row = point[0]
    return int(row) + 1


def _kind(node: Any) -> str:
    return str(getattr(node, "type", getattr(node, "kind", "")))


def _node_text(node: Any, source: bytes) -> str:
    if hasattr(node, "start_byte"):
        return source[node.start_byte:node.end_byte].decode("utf-8", "replace")
    byte_range = node.byte_range()
    return source[byte_range.start:byte_range.end].decode("utf-8", "replace")


def _children(node: Any) -> list[Any]:
    value = getattr(node, "named_children", None)
    if value is not None:
        return list(value)
    return [node.named_child(i) for i in range(node.named_child_count())]


def _name(node: Any, source: bytes) -> str:
    try:
        name_node = node.child_by_field_name("name")
    except (AttributeError, TypeError):
        name_node = None
    return _node_text(name_node, source).strip() if name_node else "<anonymous>"


def parse_symbols(path: Path, repo: Path) -> tuple[list[Symbol], bool | None]:
    language = EXTENSIONS.get(path.suffix.lower())
    if not language:
        return [], None
    try:
        parser = _offline_parser(language)
    except (ImportError, OSError, RuntimeError, ValueError):
        parser = None
    if parser is None:
        if language == "python":
            return _python_symbols(path, repo)
        return _javascript_symbols(path, repo) if language in {"javascript", "typescript", "tsx"} else ([], None)
    raw_source = path.read_bytes()
    source = raw_source.decode("utf-8-sig", "replace") if language == "python" else raw_source
    try:
        tree = _parse(parser, source if isinstance(source, str) else source.decode("utf-8", "replace"))
    except (TypeError, UnicodeError):
        tree = _parse(parser, source)
    root = getattr(tree, "root_node", None)
    if root is None:
        root = tree.root_node
    lines = source.splitlines() if isinstance(source, str) else source.decode("utf-8", "replace").splitlines()
    found: list[Symbol] = []
    stack = [root]
    while stack:
        node = stack.pop()
        kind = _kind(node)
        is_arrow_binding = False
        if kind == "variable_declarator":
            try:
                value = node.child_by_field_name("value")
                is_arrow_binding = value is not None and _kind(value) in {"arrow_function", "function_expression"}
            except (AttributeError, TypeError):
                pass
        if kind in SYMBOL_KINDS or is_arrow_binding:
            start, end = _position(node, "start_point"), _position(node, "end_point")
            text = _node_text(node, source)
            signature = next((line.strip() for line in text.splitlines() if line.strip()), "")[:240]
            identifiers = list(dict.fromkeys(tokens(text)))
            symbol_kind = "arrow_function" if is_arrow_binding else kind
            found.append(Symbol(path.relative_to(repo).as_posix(), _name(node, source), symbol_kind, start, end, signature, identifiers))
        stack.extend(reversed(_children(node)))
    if not found and language in {"javascript", "typescript", "tsx"}:
        return _javascript_symbols(path, repo)
    return found, bool(getattr(root, "has_error", False)() if callable(getattr(root, "has_error", None)) else getattr(root, "has_error", False))


def _javascript_symbols(path: Path, repo: Path) -> tuple[list[Symbol], bool | None]:
    """Extract common JS/TS function and class ranges without optional grammars."""
    source = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = source.splitlines()
    starts: list[tuple[int, str, str]] = []
    patterns = (
        (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([\w$]+)\s*\("), "function_declaration"),
        (re.compile(r"^\s*(?:export\s+)?class\s+([\w$]+)\b"), "class_declaration"),
        (re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([\w$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>"), "arrow_function"),
    )
    for index, line in enumerate(lines):
        for pattern, kind in patterns:
            match = pattern.search(line)
            if match:
                starts.append((index, match.group(1), kind))
                break

    def end_line(start: int) -> int:
        text = "\n".join(lines[start:])
        opening = text.find("{")
        if opening < 0:
            return start + 1
        depth = 0
        quote = ""
        escaped = False
        line_comment = False
        block_comment = False
        i = opening
        while i < len(text):
            char = text[i]
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if line_comment:
                if char == "\n":
                    line_comment = False
            elif block_comment:
                if char == "*" and nxt == "/":
                    block_comment = False
                    i += 1
            elif quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = ""
            elif char == "/" and nxt == "/":
                line_comment = True
                i += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                i += 1
            elif char in {"'", '"', "`"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return start + text[:i + 1].count("\n") + 1
            i += 1
        return len(lines)

    found = []
    for start, name, kind in starts:
        finish = end_line(start)
        segment = "\n".join(lines[start:finish])
        signature = next((line.strip() for line in segment.splitlines() if line.strip()), "")[:240]
        found.append(Symbol(path.relative_to(repo).as_posix(), name, kind, start + 1, finish, signature, list(dict.fromkeys(tokens(segment)))))
    return found, None


def _python_symbols(path: Path, repo: Path) -> tuple[list[Symbol], bool]:
    """Use Python's built-in AST when the optional tree-sitter pack is absent."""
    source = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        module = ast.parse(source)
    except SyntaxError:
        return [], True
    found: list[Symbol] = []
    for node in ast.walk(module):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
        end = getattr(node, "end_lineno", node.lineno)
        segment = ast.get_source_segment(source, node) or ""
        signature = next((line.strip() for line in segment.splitlines() if line.strip()), "")[:240]
        identifiers = list(dict.fromkeys([child.id.lower() for child in ast.walk(node) if isinstance(child, ast.Name)] + [node.name.lower()]))
        found.append(Symbol(path.relative_to(repo).as_posix(), node.name, "class_definition" if isinstance(node, ast.ClassDef) else "function_definition", start, end, signature, identifiers))
    return found, False


def _offline_parser(language: str):
    from tree_sitter_language_pack import get_parser, has_parser

    return get_parser(language) if has_parser(language) else None


def _parse(parser, source):
    tree = parser.parse(source)
    return tree


def syntax_check(path: Path, source: str) -> bool | None:
    """Return parse validity, or None when no offline grammar is installed."""
    language = EXTENSIONS.get(path.suffix.lower())
    if not language:
        return None
    if language == "python":
        source = source.removeprefix("\ufeff")
    try:
        parser = _offline_parser(language)
    except (ImportError, OSError, RuntimeError, ValueError):
        parser = None
    if parser is not None:
        try:
            tree = _parse(parser, source)
        except TypeError:
            tree = _parse(parser, source.encode("utf-8"))
        root = getattr(tree, "root_node", tree.root_node if hasattr(tree, "root_node") else None)
        if root is None:
            return None
        has_error = getattr(root, "has_error", False)
        return not (has_error() if callable(has_error) else has_error)
    if language == "python":
        source = source.removeprefix("\ufeff")
        try:
            ast.parse(source)
            return True
        except SyntaxError:
            return False
    if language == "javascript" and shutil.which("node"):
        check_path = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".mjs", encoding="utf-8", dir=path.parent, delete=False) as handle:
                handle.write(source)
                check_path = Path(handle.name)
            result = subprocess.run(
                ["node", "--check", str(check_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return None
        finally:
            if check_path is not None:
                check_path.unlink(missing_ok=True)
    return None


class SymbolIndex:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.cache_path = self.repo / ".leancode" / "index.json"
        self.files: dict[str, dict[str, Any]] = {}
        self.symbols: list[Symbol] = []
        self.updated = 0
        self.removed = 0

    def build(self, *, force: bool = False) -> "SymbolIndex":
        old: dict[str, dict[str, Any]] = {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            old = data.get("files", {})
        except (OSError, ValueError, AttributeError):
            pass
        current: set[str] = set()
        for path in self._source_files():
            rel = path.relative_to(self.repo).as_posix()
            current.add(rel)
            stat = path.stat()
            digest = hashlib.blake2b(path.read_bytes(), digest_size=8).hexdigest()
            previous = old.get(rel)
            if not force and previous and previous.get("digest") == digest and previous.get("has_syntax_error") is not None:
                self.files[rel] = previous
                continue
            symbols, has_error = parse_symbols(path, self.repo)
            self.files[rel] = {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size, "digest": digest, "symbols": [asdict(symbol) for symbol in symbols], "has_syntax_error": has_error}
            self.updated += 1
        self.removed = len(set(old) - current)
        for rel in current:
            self.symbols.extend(Symbol(**item) for item in self.files[rel].get("symbols", []))
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "files": self.files}, separators=(",", ":")), encoding="utf-8")
        tmp.replace(self.cache_path)
        return self

    def _source_files(self):
        for root, dirs, files in os.walk(self.repo):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for name in files:
                path = Path(root) / name
                if path.suffix.lower() in EXTENSIONS and not name.startswith(".") and path.stat().st_size <= 1_000_000:
                    yield path

    def rank(self, query: str, *, limit: int = 12) -> list[tuple[Symbol, float]]:
        if not self.symbols:
            return []
        q = set(tokens(query))
        if not q:
            return []
        docs = [(s, set(tokens(" ".join([s.name, s.kind, s.signature, s.path, " ".join(s.identifiers)])))) for s in self.symbols]
        avgdl = sum(len(doc) for _, doc in docs) / max(1, len(docs))
        df = {term: sum(term in doc for _, doc in docs) for term in q}
        scored: list[tuple[Symbol, float]] = []
        for symbol, doc in docs:
            score = 0.0
            for term in q:
                freq = sum(tokens(" ".join([symbol.name, symbol.signature, " ".join(symbol.identifiers)])).count(term) for _ in (0,))
                if not freq:
                    continue
                idf = math.log(1 + (len(docs) - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * freq * 2.2 / (freq + 1.2 * (0.25 + 0.75 * len(doc) / max(avgdl, 1)))
                if term in tokens(symbol.name):
                    score += 1.5
            if score:
                scored.append((symbol, score))
        return sorted(scored, key=lambda item: (-item[1], item[0].path, item[0].start_line))[:limit]
