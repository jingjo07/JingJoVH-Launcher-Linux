"""Custom-font override PAK support for Neverness to Everness."""

import base64
import io
import os
import shutil
import struct
import subprocess
import tempfile

from backend import nte, wuwa_game


CUSTOM_FONT_PAK_NAME = "pakchunk9999-Windows_9999_P.pak"
TRANSLATION_PAK_NAME = "pakchunk999-Windows_999_P.pak"
FONT_ASSET_PATHS = (
    "HT/Content/Environment/Building/TrainStation/Fonts/MiSans-Bold.ufont",
    "HT/Content/Environment/Building/TrainStation/Fonts/MiSans-Demibold.ufont",
    "HT/Content/Environment/Building/TrainStation/Fonts/MiSans-Heavy.ufont",
)
_MAX_FONT_SIZE = 20 * 1024 * 1024
_MAX_PAK_SIZE = 200 * 1024 * 1024


def _pak_dir() -> str:
    root = nte.detect_game_path()
    if not root:
        raise FileNotFoundError("Không tìm thấy thư mục game NTE")
    path = os.path.join(root, "Client", "WindowsNoEditor", "HT", "Content", "Paks")
    os.makedirs(path, exist_ok=True)
    return path


def _find_repak() -> str:
    appdir = os.environ.get("APPDIR")
    bundled = os.path.join(appdir, "usr", "bin", "repak") if appdir else None
    found = bundled if bundled and os.path.isfile(bundled) else shutil.which("repak")
    if not found:
        raise RuntimeError("Không tìm thấy repak để đóng gói font NTE")
    return found


def _require_stopped():
    if nte.is_game_running():
        raise RuntimeError("Hãy đóng NTE trước khi thay đổi font")


def _font_mime(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError("Không tìm thấy file font đã chọn")
    size = os.path.getsize(path)
    if not 12 <= size <= _MAX_FONT_SIZE:
        raise ValueError("Kích thước font không hợp lệ")
    with open(path, "rb") as source:
        magic = source.read(4)
    return _font_mime_for_magic(magic)


def _font_mime_for_magic(magic: bytes) -> str:
    if magic == b"\x00\x01\x00\x00":
        return "font/ttf"
    if magic == b"OTTO":
        return "font/otf"
    raise ValueError("File không phải font TTF/OTF hợp lệ")


def _convert_cff_to_ttf(data: bytes) -> bytes:
    # Based on fontTools/Snippets/otf2ttf.py and otf2ttf 0.2 (MIT).
    try:
        from fontTools.pens.cu2quPen import Cu2QuPen
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        from fontTools.ttLib import TTFont, newTable
    except ImportError as error:
        raise RuntimeError("Launcher thiếu bộ chuyển đổi font OpenType/CFF") from error

    font = TTFont(io.BytesIO(data))
    if font.sfntVersion != "OTTO" or "CFF " not in font:
        raise ValueError("Font OpenType không dùng CFF outlines nên không thể chuyển đổi")
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyphs[name] = pen.glyph()

    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = glyphs
    del font["CFF "]
    glyf.compile(font)

    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max(
        len(glyph.components if hasattr(glyph, "components") else [])
        for glyph in glyphs.values()
    )
    maxp.compile(font)

    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyph_order
    try:
        post.compile(font)
    except OverflowError:
        post.formatType = 3.0
    font.sfntVersion = "\0\1\0\0"
    output = io.BytesIO()
    font.save(output)
    return output.getvalue()


def _wrap_ufont(data: bytes) -> bytes:
    return struct.pack("<I", len(data)) + data + b"\0\0\0\0"


def _unwrap_ufont(payload: bytes) -> bytes:
    if (
        not 20 <= len(payload) <= _MAX_FONT_SIZE + 8
        or payload[-4:] != b"\0\0\0\0"
        or struct.unpack("<I", payload[:4])[0] != len(payload) - 8
    ):
        raise ValueError("PAK font NTE chứa dữ liệu font không hợp lệ")
    return payload[4:-4]


def _pak_entries(path: str) -> set[str]:
    if not os.path.isfile(path) or not 1 <= os.path.getsize(path) <= _MAX_PAK_SIZE:
        raise ValueError("File PAK font NTE không hợp lệ")
    result = subprocess.run(
        [_find_repak(), "list", path],
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def _cache_path() -> str:
    return os.path.join(os.path.dirname(wuwa_game.CONFIG_PATH), "nte-fonts", "custom-font.bin")


def _backup_path() -> str:
    return os.path.join(os.path.dirname(_cache_path()), "translation-font-backup.pak")


def _patch_translation_pak(font_data: bytes):
    pak_dir = _pak_dir()
    target = os.path.join(pak_dir, TRANSLATION_PAK_NAME)
    if not os.path.isfile(target):
        raise FileNotFoundError("Hãy cài Việt hóa NTE trước khi đổi font")
    original_entries = _pak_entries(target)
    if not set(FONT_ASSET_PATHS).issubset(original_entries):
        raise ValueError("PAK Việt hóa NTE không chứa font để thay thế")

    backup = _backup_path()
    if not os.path.isfile(backup):
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        temporary_backup = backup + ".tmp"
        shutil.copyfile(target, temporary_backup)
        os.replace(temporary_backup, backup)

    with tempfile.TemporaryDirectory(prefix=".nte-font-", dir=pak_dir) as workspace:
        source_root = os.path.join(workspace, "source")
        subprocess.run(
            [_find_repak(), "unpack", "-q", "-o", source_root, target],
            check=True,
            capture_output=True,
        )
        for relative in FONT_ASSET_PATHS:
            path = os.path.join(source_root, *relative.split("/"))
            with open(path, "wb") as output:
                output.write(_wrap_ufont(font_data))
        packed = os.path.join(workspace, TRANSLATION_PAK_NAME)
        subprocess.run(
            [_find_repak(), "pack", "-q", "--version", "V8B", source_root, packed],
            check=True,
            capture_output=True,
        )
        if _pak_entries(packed) != original_entries:
            raise RuntimeError("repak tạo lại PAK Việt hóa NTE không hợp lệ")
        os.replace(packed, target)

    old_override = os.path.join(pak_dir, CUSTOM_FONT_PAK_NAME)
    if os.path.isfile(old_override):
        os.unlink(old_override)


def _save_preview(data: bytes, mime: str):
    target = _cache_path()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    temporary = target + ".tmp"
    with open(temporary, "wb") as output:
        output.write(data)
    os.replace(temporary, target)
    cfg = wuwa_game.load_config()
    cfg["nte_custom_font_mime"] = mime
    wuwa_game.save_config(cfg)


def _save_name(name: str):
    cfg = wuwa_game.load_config()
    cfg["nte_custom_font_name"] = name
    wuwa_game.save_config(cfg)


def get_font_status() -> dict:
    try:
        pak_dir = _pak_dir()
    except FileNotFoundError:
        return {"active_font": "none", "custom_font_name": None, "default_available": False}
    default = os.path.isfile(os.path.join(pak_dir, TRANSLATION_PAK_NAME))
    cfg = wuwa_game.load_config()
    custom = bool(cfg.get("nte_custom_font_name") and os.path.isfile(_backup_path()))
    return {
        "active_font": "custom" if custom else "default" if default else "none",
        "custom_font_name": cfg.get("nte_custom_font_name") if custom else None,
        "default_available": default,
    }


def get_font_preview() -> dict:
    if get_font_status()["active_font"] != "custom":
        return {"data": None, "mime": None}
    path = _cache_path()
    mime = wuwa_game.load_config().get("nte_custom_font_mime")
    if not os.path.isfile(path) or mime not in ("font/ttf", "font/otf"):
        return {"data": None, "mime": None}
    with open(path, "rb") as source:
        data = source.read(_MAX_FONT_SIZE + 1)
    if len(data) > _MAX_FONT_SIZE:
        return {"data": None, "mime": None}
    return {"data": base64.b64encode(data).decode("ascii"), "mime": mime}


def install_custom_font(font_path: str) -> dict:
    if font_path.lower().endswith(".pak"):
        return install_font_from_pak(font_path)
    mime = _font_mime(font_path)
    _require_stopped()
    with open(font_path, "rb") as source:
        font_data = source.read()
    if mime == "font/otf":
        font_data = _convert_cff_to_ttf(font_data)
        mime = "font/ttf"
    _patch_translation_pak(font_data)

    _save_preview(font_data, mime)
    name = os.path.splitext(os.path.basename(font_path))[0]
    _save_name(name)
    return {"ok": True, "font_name": name, "pak_file": TRANSLATION_PAK_NAME}


def install_font_from_pak(pak_path: str) -> dict:
    _require_stopped()
    if _pak_entries(pak_path) != set(FONT_ASSET_PATHS):
        raise ValueError("PAK không phải gói font NTE hợp lệ")
    extracted = None
    mime = None
    for asset in FONT_ASSET_PATHS:
        payload = subprocess.run(
            [_find_repak(), "get", pak_path, asset],
            check=True,
            capture_output=True,
        ).stdout
        font_data = _unwrap_ufont(payload)
        asset_mime = _font_mime_for_magic(font_data[:4])
        if extracted is None:
            extracted, mime = font_data, asset_mime
    if mime == "font/otf":
        extracted = _convert_cff_to_ttf(extracted)
        mime = "font/ttf"
    _patch_translation_pak(extracted)
    _save_preview(extracted, mime)
    name = os.path.splitext(os.path.basename(pak_path))[0]
    _save_name(name)
    return {"ok": True, "font_name": name, "pak_file": TRANSLATION_PAK_NAME}


def install_default_font() -> dict:
    _require_stopped()
    pak_dir = _pak_dir()
    target = os.path.join(pak_dir, TRANSLATION_PAK_NAME)
    backup = _backup_path()
    if os.path.isfile(backup):
        os.replace(backup, target)
    old_override = os.path.join(pak_dir, CUSTOM_FONT_PAK_NAME)
    if os.path.isfile(old_override):
        os.unlink(old_override)
    cache = _cache_path()
    if os.path.isfile(cache):
        os.unlink(cache)
    cfg = wuwa_game.load_config()
    cfg.pop("nte_custom_font_name", None)
    cfg.pop("nte_custom_font_mime", None)
    wuwa_game.save_config(cfg)
    return {"ok": True, "font_name": "MiSans (Mặc định NTE)"}
