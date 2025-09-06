from __future__ import annotations
import json, os, sys, tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class FlooSettings:
    """
    Generic JSON settings store for FlooCast.

    - Arbitrary key/value storage (use any string as the key)
    - Persisted to a cross-platform, user-writable location (MSIX-friendly on Windows)
    - Includes helpers for saving/loading dict-based device info
    """

    def __init__(self, app_name: str = "FlooCast", filename: str = "settings.json"):
        self.app_name = app_name
        self.filename = filename
        self.path: Path = self._default_settings_path(app_name, filename)
        self._data: Dict[str, Any] = {}
        self.load()

    # ---------- Core I/O ----------

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(self._data, dict):
                    self._data = {}
            except Exception:
                self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise

    # ---------- Generic get/set ----------

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, mapping: Dict[str, Any]) -> None:
        self._data.update(mapping)

    def remove(self, key: str) -> None:
        self._data.pop(key, None)

    # ---------- Named helpers for dict-based items ----------

    def set_item(self, name, item):
        if isinstance(item, dict):
            # shallow copy so the caller can't mutate stored dicts
            self._data[name] = dict(item)
        else:
            # store scalars (bool, int, str, list, etc.) directly
            self._data[name] = item

    def get_item(self, name, default=None):
        value = self._data.get(name, default)
        if isinstance(value, dict):
            # return a copy so caller can’t mutate our stored copy
            return dict(value)
        return value

    # ---------- Path helper ----------

    @staticmethod
    def _default_settings_path(app_name: str, filename: str) -> Path:
        if sys.platform == "win32":
            base = os.getenv("LOCALAPPDATA") or str(Path.home())
            return Path(base) / app_name / filename
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / app_name / filename
        else:
            cfg = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            return Path(cfg) / app_name / filename
