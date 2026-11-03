from __future__ import annotations

import hashlib
import json
import math
import os
import re
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
        return [], None
    if parser is None:
        return [], None
    source = path.read_bytes()
    try:
        tree = _parse(parser, source.decode("utf-8", "replace"))
    except (TypeError, UnicodeError):
        tree = _parse(parser, source)
    root = getattr(tree, "root_node", None)
    if root is None:
        root = tree.root_node
    lines = source.decode("utf-8", "replace").splitlines()
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
    return found, bool(getattr(root, "has_error", False)() if callable(getattr(root, "has_error", None)) else getattr(root, "has_error", False))


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
