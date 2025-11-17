"""
Core helpers for reading/writing Cosmic Pair Ledger files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

KEYMAP_RECORD = "keymap"


def _separate_keymap(entries: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """Split the keymap entry (if present) from the data entries."""
    data_entries: List[Dict[str, str]] = []
    keymap: Dict[str, str] = {}
    for entry in entries:
        if entry.get("record") == KEYMAP_RECORD:
            for key, value in entry.items():
                if key == "record":
                    continue
                keymap[key] = value
            continue
        data_entries.append(entry)
    return data_entries, keymap


def _apply_keymap(entry: Dict[str, str], keymap: Dict[str, str]) -> Dict[str, str]:
    if not keymap:
        return entry
    return {keymap.get(key, key): value for key, value in entry.items()}


def parse_pair_line(line: str) -> Dict[str, str]:
    """
    Parse a single CPL line into a dict of key/value strings.
    Each segment is expected to look like ``key:value`` and segments are comma
    separated. Extra whitespace is trimmed.
    """
    record: Dict[str, str] = {}
    if not line:
        return record

    parts = [segment for segment in line.strip().split(",") if segment]
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        record[key.strip()] = value.strip()
    return record


def load_pair_csv(path: Path | str, *, expand_keymap: bool = False) -> List[Dict[str, str]]:
    """Read a CPL file into a list of records."""
    path = Path(path)
    records: List[Dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            records.append(parse_pair_line(line))
    data_entries, keymap = _separate_keymap(records)
    if expand_keymap and keymap:
        data_entries = [_apply_keymap(entry, keymap) for entry in data_entries]
    return data_entries


def load_pair_csv_with_keymap(path: Path | str, *, expand_keymap: bool = True) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """Return entries and the resolved keymap."""
    path = Path(path)
    records: List[Dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            records.append(parse_pair_line(line))
    data_entries, keymap = _separate_keymap(records)
    if expand_keymap and keymap:
        data_entries = [_apply_keymap(entry, keymap) for entry in data_entries]
    return data_entries, keymap


def write_pair_csv(entries: Iterable[Dict[str, str]], path: Path | str, keymap: Dict[str, str] | None = None) -> None:
    """Write CPL entries (optionally with a keymap header) to a file."""
    path = Path(path)
    keymap = keymap or {}

    def _write_entry(entry: Dict[str, str], handle) -> None:
        segments = [f"{key}:{value}" for key, value in entry.items()]
        handle.write(",".join(segments) + "\n")

    with path.open("w", encoding="utf-8") as handle:
        if keymap:
            keymap_entry: Dict[str, str] = {"record": KEYMAP_RECORD}
            for alias in sorted(keymap):
                keymap_entry[alias] = keymap[alias]
            _write_entry(keymap_entry, handle)
        for entry in entries:
            _write_entry(entry, handle)


def entries_to_json_data(entries: List[Dict[str, str]], keymap: Dict[str, str] | None = None) -> Dict[str, Any]:
    """Convert CPL entries to a JSON-serializable payload."""
    payload: Dict[str, List[Dict[str, str]] | Dict[str, str]] = {"entries": entries}
    if keymap:
        payload["keymap"] = keymap
    return payload


def json_data_to_entries(data: Dict[str, Any]) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """Convert JSON/YAML payload back to CPL entries and an optional keymap."""
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("JSON/YAML representation must include a top-level 'entries' list")
    keymap_data = data.get("keymap", {})
    if keymap_data and not isinstance(keymap_data, dict):
        raise ValueError("'keymap' must be an object mapping alias -> full key")
    keymap: Dict[str, str] = {str(key): str(value) for key, value in keymap_data.items()} if keymap_data else {}
    return [dict(item) for item in entries], keymap
