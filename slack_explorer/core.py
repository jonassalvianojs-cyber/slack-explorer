from __future__ import annotations

import datetime as dt
import mimetypes
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class FileEntry:
    path: Path
    name: str
    is_dir: bool
    size: int
    modified: float
    mode: int
    type_name: str


def human_size(size: int, is_dir: bool = False) -> str:
    if is_dir:
        return ""
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def format_date(timestamp: float) -> str:
    return dt.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")


def permission_text(mode: int) -> str:
    return stat.filemode(mode)


def file_type(path: Path, is_dir: bool) -> str:
    if is_dir:
        return "Pasta de arquivos"
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        major, _, minor = mime.partition("/")
        labels = {
            "image": "Imagem",
            "video": "Vídeo",
            "audio": "Áudio",
            "text": "Documento de texto",
            "application": "Arquivo",
        }
        label = labels.get(major, "Arquivo")
        return f"{label} ({minor.upper()})" if minor else label
    suffix = path.suffix.lstrip(".").upper()
    return f"Arquivo {suffix}" if suffix else "Arquivo"


def list_directory(path: Path, show_hidden: bool = False, query: str = "") -> List[FileEntry]:
    query = query.casefold().strip()
    entries: List[FileEntry] = []
    with os.scandir(path) as items:
        for item in items:
            if not show_hidden and item.name.startswith("."):
                continue
            if query and query not in item.name.casefold():
                continue
            try:
                info = item.stat(follow_symlinks=False)
                is_dir = item.is_dir(follow_symlinks=False)
            except (FileNotFoundError, PermissionError, OSError):
                continue
            item_path = Path(item.path)
            entries.append(FileEntry(
                path=item_path,
                name=item.name,
                is_dir=is_dir,
                size=info.st_size,
                modified=info.st_mtime,
                mode=info.st_mode,
                type_name=file_type(item_path, is_dir),
            ))
    return sorted(entries, key=lambda entry: (not entry.is_dir, entry.name.casefold()))


def existing_parent(path: Path) -> Path:
    candidate = path.expanduser().absolute()
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate if candidate.is_dir() else candidate.parent
