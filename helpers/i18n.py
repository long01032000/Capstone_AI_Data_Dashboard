# helpers/i18n.py
import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional

@lru_cache(maxsize=3)
def load_language(lang: str = "en", locales_dir: str = "locales") -> Mapping[str, str]:
    """
    Load language strings with a simple EN/VI overlay (VI overrides EN keys).
    """
    l = str(lang).lower()
    normal = "vi" if l.startswith("vi") else "en"

    def _load(path: Path) -> dict:
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    base = _load(Path(locales_dir) / "en.json")
    if normal == "en":
        return MappingProxyType(base)

    overlay = _load(Path(locales_dir) / "vi.json")
    merged = base.copy(); merged.update(overlay)
    return MappingProxyType(merged)

def trans(locale: Mapping[str, str], key: str, fallback: Optional[str] = None, strict: bool = False) -> str:
    if key in locale:
        return locale[key]
    if strict:
        raise KeyError(f"[i18n] missing key: {key}")
    return fallback if fallback is not None else key

def reload_locales() -> None:
    load_language.cache_clear()
