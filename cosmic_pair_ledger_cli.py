#!/usr/bin/env python3
"""
Cosmic Pair Ledger CLI – runtime converters and readers.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import signal

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (ImportError, AttributeError):
    pass

from cosmic_pair_ledger.core import (
    load_pair_csv_with_keymap,
    write_pair_csv,
    entries_to_json_data,
    json_data_to_entries,
)


def _stringify_scalar(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class AliasGenerator:
    def __init__(self, prefix: str = "k") -> None:
        self._path_to_alias: Dict[str, str] = {}
        self._alias_to_path: Dict[str, str] = {}
        self._prefix = prefix

    def alias_for(self, path: str) -> str:
        if path not in self._path_to_alias:
            alias = f"{self._prefix}{len(self._path_to_alias)}"
            self._path_to_alias[path] = alias
            self._alias_to_path[alias] = path
        return self._path_to_alias[path]

    def as_keymap(self) -> Dict[str, str]:
        return dict(self._alias_to_path)


def _walk_yaml_paths(node, prefix: str = "") -> Iterable[Tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _walk_yaml_paths(value, child_prefix)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            child_prefix = f"{prefix}.{index}" if prefix else str(index)
            yield from _walk_yaml_paths(value, child_prefix)
    else:
        yield prefix, _stringify_scalar(node)


def _flatten_yaml_documents(documents: Iterable[dict]) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    alias_gen = AliasGenerator()
    entries: List[Dict[str, str]] = []
    for doc_index, document in enumerate(documents):
        entry: Dict[str, str] = {"record": "yaml-doc", "doc_index": str(doc_index)}
        if document is None:
            entries.append(entry)
            continue
        for path, value in _walk_yaml_paths(document):
            if not path:
                continue
            alias = alias_gen.alias_for(path)
            entry[alias] = value
        entries.append(entry)
    return entries, alias_gen.as_keymap()


class HtmlCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: List[Dict[str, str]] = []
        self.node_children: Dict[str, List[str]] = defaultdict(list)
        self.stack: List[str] = []
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        ident = f"{prefix}{self._counter}"
        self._counter += 1
        return ident

    def handle_starttag(self, tag, attrs):
        node_id = self._next_id("n")
        parent_id = self.stack[-1] if self.stack else ""
        node: Dict[str, str] = {
            "record": "element",
            "id": node_id,
            "tag": tag,
        }
        if parent_id:
            node["parent"] = parent_id
            self.node_children[parent_id].append(node_id)
        for attr_key, attr_value in attrs:
            node[f"attr.{attr_key}"] = attr_value or ""
        self.nodes.append(node)
        self.stack.append(node_id)

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        parent_id = self.stack[-1] if self.stack else ""
        node_id = self._next_id("t")
        node: Dict[str, str] = {"record": "text", "id": node_id, "text": text}
        if parent_id:
            node["parent"] = parent_id
            self.node_children[parent_id].append(node_id)
        self.nodes.append(node)

    def to_entries(self) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        for node in self.nodes:
            node_id = node["id"]
            children = self.node_children.get(node_id, [])
            entry = dict(node)
            for child_index, child_id in enumerate(children):
                entry[f"child{child_index}"] = child_id
            entries.append(entry)
        return entries


def _write_text_output(output: str | None, text: str) -> None:
    if output in (None, "-", ""):
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    else:
        Path(output).write_text(text, encoding="utf-8")


def cmd_to_json(args):
    entries, keymap = load_pair_csv_with_keymap(args.input, expand_keymap=True)
    payload = entries_to_json_data(entries, keymap if keymap else None)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    _write_text_output(args.output, text)


def cmd_to_yaml(args):
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required for YAML operations") from exc

    entries, keymap = load_pair_csv_with_keymap(args.input, expand_keymap=True)
    payload = entries_to_json_data(entries, keymap if keymap else None)
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    _write_text_output(args.output, text)


def _read_json_file(path):
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def cmd_from_json(args):
    data = _read_json_file(args.input)
    entries, keymap = json_data_to_entries(data)
    write_pair_csv(entries, args.output, keymap=keymap or None)


def cmd_from_yaml(args):
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required for YAML operations") from exc

    text = Path(args.input).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    entries, keymap = json_data_to_entries(data)
    write_pair_csv(entries, args.output, keymap=keymap or None)


def cmd_read(args):
    entries, keymap = load_pair_csv_with_keymap(args.input, expand_keymap=False)
    if keymap:
        sys.stdout.write("--- Key Map ---\n")
        for alias, target in keymap.items():
            sys.stdout.write(f"{alias} -> {target}\n")
        sys.stdout.write("\n")
    for idx, entry in enumerate(entries, 1):
        sys.stdout.write(f"--- Entry {idx} ---\n")
        for key, value in entry.items():
            sys.stdout.write(f"{key}: {value}\n")
        sys.stdout.write("\n")


def cmd_yaml_to_ledger(args):
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required for YAML ingestion") from exc

    text = Path(args.input).read_text(encoding="utf-8")
    documents = list(yaml.safe_load_all(text))
    entries, keymap = _flatten_yaml_documents(documents)
    write_pair_csv(entries, args.output, keymap=keymap or None)


def cmd_html_to_ledger(args):
    parser = HtmlCollector()
    text = Path(args.input).read_text(encoding="utf-8")
    parser.feed(text)
    entries = parser.to_entries()
    write_pair_csv(entries, args.output)


def build_parser():
    parser = argparse.ArgumentParser(description="Cosmic Pair Ledger converter CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    to_json = sub.add_parser("to-json", help="convert CPL to JSON")
    to_json.add_argument("--input", required=True, help="CPL input file")
    to_json.add_argument("--output", default="-", help="JSON output file or '-' for stdout")
    to_json.set_defaults(func=cmd_to_json)

    to_yaml = sub.add_parser("to-yaml", help="convert CPL to YAML")
    to_yaml.add_argument("--input", required=True)
    to_yaml.add_argument("--output", default="-", help="YAML output file or '-' for stdout")
    to_yaml.set_defaults(func=cmd_to_yaml)

    from_json = sub.add_parser("from-json", help="convert JSON payload back to CPL")
    from_json.add_argument("--input", required=True)
    from_json.add_argument("--output", required=True, help="CPL output file")
    from_json.set_defaults(func=cmd_from_json)

    from_yaml = sub.add_parser("from-yaml", help="convert YAML payload back to CPL")
    from_yaml.add_argument("--input", required=True)
    from_yaml.add_argument("--output", required=True)
    from_yaml.set_defaults(func=cmd_from_yaml)

    read_cmd = sub.add_parser("read", help="pretty print a CPL file without converting")
    read_cmd.add_argument("--input", required=True)
    read_cmd.set_defaults(func=cmd_read)

    yaml_ingest = sub.add_parser("yaml-to-ledger", help="flatten a YAML document directly to CPL")
    yaml_ingest.add_argument("--input", required=True)
    yaml_ingest.add_argument("--output", required=True)
    yaml_ingest.set_defaults(func=cmd_yaml_to_ledger)

    html_ingest = sub.add_parser("html-to-ledger", help="convert HTML into CPL records")
    html_ingest.add_argument("--input", required=True)
    html_ingest.add_argument("--output", required=True)
    html_ingest.set_defaults(func=cmd_html_to_ledger)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
