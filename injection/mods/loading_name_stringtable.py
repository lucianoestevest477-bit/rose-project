#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a small CSLOL fallback mod that overrides the localized champion display
string used by the loading screen card.

LCU re-selection remains the primary path for making the official loading
screen show the chosen skin. In practice,
PATCH /lol-champ-select/v1/session/my-selection can return 204 even for
unowned skins, so this stringtable override is kept as a fallback when the
client accepts the selection request but the loading-card text still resolves
to the champion name. The source stringtable must follow the active LCU locale
when available. The current integer-key fallback replaces entries by exact
champion-name value and is functional, but it should be narrowed in a follow-up
to the specific loading-card display-name hash once that mapping is known.
"""

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from utils.core.logging import get_logger
from utils.core.paths import get_injection_dir, get_user_data_dir

log = get_logger()

RST_MAGIC = b"RST"
RST_VERSION = 5
RST_HASH_BITS = 38
CACHE_VERSION = "loading-name-locale-v1"


def create_loading_name_stringtable_mod(
    game_dir: Path | None,
    champion_name: str,
    skin_name: str,
    output_dir: Path,
    locale: str | None = None,
) -> Path | None:
    """Create a temporary mod folder that patches the global stringtable."""
    champion_name = (champion_name or "").strip()
    skin_name = (skin_name or "").strip()
    if not champion_name or not skin_name or champion_name == skin_name:
        return None

    source_wad = _find_global_stringtable_wad(game_dir, locale=locale)
    if not source_wad:
        log.info("[LoadingName] Global stringtable WAD not found; skipping")
        return None

    output_dir = Path(output_dir)
    tools_dir, checked_tool_dirs = _find_tools_dir(output_dir)
    if not tools_dir:
        log.info(
            "[LoadingName] WAD tools missing; skipping. Checked: %s",
            "; ".join(str(path) for path in checked_tool_dirs),
        )
        return None

    wad_extract = tools_dir / "wad-extract.exe"
    wad_make = tools_dir / "wad-make.exe"
    hashdict = tools_dir / "hashes.game.txt"

    mod_dir = output_dir / "_rose_loading_name_text"
    if mod_dir.exists():
        shutil.rmtree(mod_dir, ignore_errors=True)
    (mod_dir / "META").mkdir(parents=True, exist_ok=True)
    (mod_dir / "WAD").mkdir(parents=True, exist_ok=True)

    try:
        cached_wad = _get_cached_wad(source_wad, champion_name, skin_name, locale)
        out_wad = mod_dir / "WAD" / source_wad.name
        if cached_wad.exists():
            shutil.copy2(cached_wad, out_wad)
            _write_info(mod_dir, champion_name, skin_name, locale)
            log.info("[LoadingName] Reused cached stringtable override: %s", cached_wad.name)
            return mod_dir

        with tempfile.TemporaryDirectory(prefix="rose_loading_name_") as tmp:
            tmp_dir = Path(tmp)
            extract_dir = tmp_dir / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)

            extract_cmd = [str(wad_extract), str(source_wad), str(extract_dir)]
            if hashdict.exists():
                extract_cmd.append(str(hashdict))
            if _run_tool(extract_cmd) != 0:
                shutil.rmtree(mod_dir, ignore_errors=True)
                return None

            patched = 0
            for rst_path in extract_dir.rglob("*.stringtable"):
                patched += _patch_rst_file(rst_path, champion_name, skin_name)

            if patched <= 0:
                shutil.rmtree(mod_dir, ignore_errors=True)
                log.info("[LoadingName] No stringtable entries patched for %s", champion_name)
                return None

            if _run_tool([str(wad_make), str(extract_dir), str(out_wad)]) != 0 or not out_wad.exists():
                shutil.rmtree(mod_dir, ignore_errors=True)
                return None

        cached_wad.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_wad, cached_wad)
        _write_info(mod_dir, champion_name, skin_name, locale)
        log.info("[LoadingName] Created stringtable mod with %s patched entrie(s)", patched)
        return mod_dir
    except Exception as exc:
        shutil.rmtree(mod_dir, ignore_errors=True)
        log.warning("[LoadingName] Failed to create stringtable mod: %s", exc)
        return None


def _find_global_stringtable_wad(game_dir: Path | None, locale: str | None = None) -> Path | None:
    if not game_dir:
        return None

    localized_dir = Path(game_dir) / "DATA" / "FINAL" / "Localized"
    if not localized_dir.exists():
        return None

    locale = (locale or "").strip()
    if locale:
        preferred = localized_dir / f"Global.{locale}.wad.client"
        if preferred.exists():
            return preferred

    candidates = sorted(localized_dir.glob("Global.*.wad.client"))
    return candidates[0] if candidates else None


def _should_replace(key: int | str, value: str, champion_name: str) -> bool:
    if value != champion_name:
        return False

    if isinstance(key, str):
        normalized_key = key.lower()
        return (
            normalized_key.startswith("game_character_displayname_")
            or "game_character_displayname_" in normalized_key
        )

    # TODO: This integer-key fallback is broader than ideal. Narrow it to the
    # loading-card display-name hash once the exact mapping is known.
    if isinstance(key, int):
        return True

    return False


def _find_tools_dir(output_dir: Path) -> tuple[Path | None, list[Path]]:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "injection" / "tools")
        else:
            base_dir = Path(sys.executable).parent
            candidates.extend(
                [
                    base_dir / "injection" / "tools",
                    base_dir / "_internal" / "injection" / "tools",
                ]
            )
    else:
        candidates.append(Path(__file__).resolve().parent.parent / "tools")

    candidates.extend(
        [
            output_dir.parent / "tools",
            get_injection_dir() / "tools",
        ]
    )

    checked: list[Path] = []
    seen: set[str] = set()
    for tools_dir in candidates:
        resolved = tools_dir.resolve() if tools_dir.exists() else tools_dir
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        checked.append(tools_dir)
        if (tools_dir / "wad-extract.exe").exists() and (tools_dir / "wad-make.exe").exists():
            return tools_dir, checked

    return None, checked


def _patch_rst_file(rst_path: Path, champion_name: str, skin_name: str) -> int:
    entries = _read_rst(rst_path)
    patched = 0
    for key, value in list(entries.items()):
        if _should_replace(key, value, champion_name):
            entries[key] = skin_name
            patched += 1

    if patched:
        rst_path.write_bytes(_write_rst(entries))
        log.info("[LoadingName] Patched %s entrie(s) in %s", patched, rst_path.name)
    return patched


def _get_cached_wad(source_wad: Path, champion_name: str, skin_name: str, locale: str | None) -> Path:
    stat = source_wad.stat()
    raw = "|".join(
        [
            CACHE_VERSION,
            locale or "",
            source_wad.name,
            str(stat.st_size),
            str(stat.st_mtime_ns),
            champion_name,
            skin_name,
        ]
    )
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return get_user_data_dir() / "cache" / "loading-name-rst" / f"{digest}.wad.client"


def _write_info(mod_dir: Path, champion_name: str, skin_name: str, locale: str | None) -> None:
    info = {
        "Name": "Rose Loading Name Text",
        "Author": "Rose",
        "Version": "1.0",
        "Description": f"Overrides {champion_name} loading name with {skin_name}.",
        "Locale": locale or "auto",
    }
    (mod_dir / "META" / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_rst(path: Path) -> dict[int, str]:
    data = path.read_bytes()
    if data[:3] != RST_MAGIC or data[3] != RST_VERSION:
        raise ValueError(f"Unsupported RST file: {path}")

    count = struct.unpack_from("<I", data, 4)[0]
    header_end = 8 + (count * 8)
    strings = data[header_end:]
    mask = (1 << RST_HASH_BITS) - 1
    entries: dict[int, str] = {}

    for index in range(count):
        packed = struct.unpack_from("<Q", data, 8 + (index * 8))[0]
        offset = packed >> RST_HASH_BITS
        key_hash = packed & mask
        end = strings.find(b"\x00", offset)
        if end < 0:
            end = len(strings)
        entries[key_hash] = strings[offset:end].decode("utf-8", errors="replace")

    return entries


def _write_rst(entries: dict[int, str]) -> bytes:
    data_block = bytearray()
    rows: list[tuple[int, int]] = []
    mask = (1 << RST_HASH_BITS) - 1

    for key_hash, text in entries.items():
        offset = len(data_block)
        data_block.extend(text.encode("utf-8"))
        data_block.append(0)
        rows.append((key_hash & mask, offset))

    out = bytearray()
    out.extend(RST_MAGIC)
    out.append(RST_VERSION)
    out.extend(struct.pack("<I", len(rows)))
    for key_hash, offset in rows:
        out.extend(struct.pack("<Q", (offset << RST_HASH_BITS) | key_hash))
    out.extend(data_block)
    return bytes(out)


def _run_tool(cmd: Iterable[str]) -> int:
    try:
        flags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            flags = subprocess.CREATE_NO_WINDOW
        proc = subprocess.run(
            list(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=flags,
            timeout=60,
        )
        if proc.returncode != 0:
            log.debug("[LoadingName] Tool failed (%s): %s", proc.returncode, " ".join(cmd))
            if proc.stderr:
                log.debug("[LoadingName] stderr: %s", proc.stderr[:500])
        return proc.returncode
    except Exception as exc:
        log.debug("[LoadingName] Tool execution failed: %s", exc)
        return 1
