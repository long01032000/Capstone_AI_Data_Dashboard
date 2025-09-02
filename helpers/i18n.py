#i18n.py
import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional, Union, Dict

@lru_cache(maxsize=3)
def load_language(lang: str = "en", locales_dir: str = "locales") -> dict:
    # Chuẩn hóa: chỉ 'en' hoặc 'vi'
    l = str(lang).lower()
    normal = "vi" if l.startswith("vi") else "en"

    def _load(path: Path) -> dict:
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception:
            return {}

    base = _load(Path(locales_dir) / "en.json")
    if normal == "en":
        return MappingProxyType(base)

    overlay = _load(Path(locales_dir) / f"{normal}.json")  # 'vi.json'
    merged = base.copy()
    merged.update(overlay)  
    return MappingProxyType(merged)

def trans(locale: Mapping[str, str], key: str, fallback: Optional[str] = None, strict: bool = False) -> str:
    """
    Lấy chuỗi theo key từ locale.
    - Nếu thiếu key: trả fallback (nếu có) hoặc chính key (nếu strict=False).
    - Nếu strict=True: raise KeyError để bắt lỗi sớm trong môi trường dev.
    """
    if key in locale:
        return locale[key]
    if strict:
        raise KeyError(f"[i18n] missing key: {key}")
    return fallback if fallback is not None else key

def reload_locales() -> None:
    """
    Xóa cache để lần gọi load_language() tiếp theo đọc lại file JSON (hot-reload).
    Dùng khi bạn vừa chỉnh en.json/vi.json.
    """
    load_language.cache_clear()