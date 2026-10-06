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
LOCRES_ASSET_PATH = "HT/Content/Localization/Game/en/game.locres"
FONT_ASSET_PATHS = (
    "HT/Content/Environment/Building/TrainStation/Fonts/MiSans-Bold.ufont",
    "HT/Content/Environment/Building/TrainStation/Fonts/MiSans-Demibold.ufont",
    "HT/Content/Environment/Building/TrainStation/Fonts/MiSans-Heavy.ufont",
)
_MAX_FONT_SIZE = 20 * 1024 * 1024
_MAX_PAK_SIZE = 200 * 1024 * 1024

FALLBACK_SYMBOLS = {
    0x2015: ord("-"),
    0x2012: ord("-"),
    0x201C: ord("\""),
    0x201D: ord("\""),
    0x2018: ord("'"),
    0x2019: ord("'"),
    0x300C: ord("\""),
    0x300D: ord("\""),
    0x300A: ord("\""),
    0x300B: ord("\""),
    0x2190: ord("<"),
    0x2192: ord(">"),
    0x2191: ord("^"),
    0x2193: ord("v"),
    0x2197: ord(">"),
    0x2022: ord("*"),
    0x25CF: ord("*"),
    0x25AA: ord("*"),
    0x25C6: ord("*"),
    0x25C7: ord("*"),
    0x25A0: ord("#"),
    0x25B2: ord("^"),
    0x25BC: ord("v"),
    0x25B3: ord("^"),
    0x25BD: ord("v"),
    0x2160: ord("I"),
    0x2161: ord("I"),
    0x2162: ord("I"),
    0x2163: ord("I"),
    0x2164: ord("V"),
    0x2165: ord("V"),
    0x2166: ord("V"),
    0x2167: ord("V"),
    0x2168: ord("I"),
    0x2169: ord("X"),
    0x2460: ord("1"),
    0x2461: ord("2"),
    0x2462: ord("3"),
    0x2463: ord("4"),
    0x2464: ord("5"),
    0x2465: ord("6"),
    0x2468: ord("9"),
    0xFF05: ord("%"),
    0xFF1C: ord("<"),
    0xFF1E: ord(">"),
    0xFF08: ord("("),
    0xFF09: ord(")"),
    0xFF5C: ord("|"),
    0xFF3F: ord("_"),
}

EMBEDDED_PUA_PAIRS = (
    (0xE000, 0x30CE), (0xE011, 0x1EDF), (0xE015, 0x2267), (0xE020, 0x30), (0xE02B, 0xC1), (0xE049, 0x7A0B),
    (0xE05A, 0x1EA9), (0xE07A, 0x2312), (0xE08E, 0x1EA3), (0xE090, 0xE0), (0xE095, 0x3014), (0xE0B9, 0x1EA8),
    (0xE0C9, 0x1EAB), (0xE0D5, 0x27A1), (0xE0ED, 0x1EE8), (0xE0F2, 0x41E), (0xE0FA, 0x1EE7), (0xE11D, 0xB2),
    (0xE128, 0x3B1), (0xE141, 0x1ED2), (0xE15A, 0xF4), (0xE160, 0x77), (0xE16F, 0x44), (0xE18C, 0x4E4B),
    (0xE190, 0x79), (0xE1A4, 0x111), (0xE1BA, 0x31), (0xE1C2, 0x438), (0xE1D5, 0x38), (0xE1E0, 0x1EE1),
    (0xE1E5, 0x56), (0xE200, 0xFF89), (0xE212, 0x169), (0xE220, 0xFE36), (0xE229, 0x1ED3), (0xE22D, 0x59),
    (0xE232, 0xA5), (0xE239, 0x6F), (0xE23A, 0x2248), (0xE246, 0x1EAA), (0xE249, 0x3C9), (0xE24F, 0xD7),
    (0xE278, 0x14E), (0xE281, 0x301), (0xE298, 0x1EA4), (0xE2A4, 0x5F), (0xE2BF, 0xD9), (0xE2CE, 0x42),
    (0xE2DC, 0x1EC1), (0xE2E5, 0xFF9F), (0xE2EC, 0x1EEF), (0xE317, 0x1EF7), (0xE339, 0x7A), (0xE33B, 0x3C3),
    (0xE34A, 0x443), (0xE366, 0x441), (0xE3B5, 0x1EBB), (0xE3C2, 0x1EB5), (0xE3C7, 0x1EC2), (0xE3D0, 0xE9),
    (0xE3E2, 0x1EBF), (0xE3EC, 0x76), (0xE3F4, 0x5D), (0xE3FE, 0x46), (0xE40E, 0x6E38), (0xE467, 0x110),
    (0xE4CB, 0x1EC0), (0xE4F9, 0x33), (0xE50C, 0x4A), (0xE524, 0x66F3), (0xE549, 0xE8), (0xE54E, 0x2C),
    (0xE55D, 0x2264), (0xE596, 0x3C1), (0xE5BA, 0x64), (0xE5BC, 0x2266), (0xE5BF, 0x6F2B), (0xE5C1, 0x3B5),
    (0xE5D1, 0xF6), (0xE5DA, 0x65E9), (0xE5E0, 0x1EC9), (0xE606, 0x47), (0xE60B, 0x57CE), (0xE615, 0xED),
    (0xE61F, 0x1EA5), (0xE623, 0x3B9), (0xE63C, 0xBB), (0xE63E, 0x5C), (0xE674, 0x256D), (0xE692, 0x2192),
    (0xE695, 0x221A), (0xE6B9, 0x74), (0xE6DB, 0x1EA1), (0xE6EF, 0x2035), (0xE6F9, 0x1ED1), (0xE6FD, 0x1EE3),
    (0xE709, 0x300A), (0xE716, 0x2166), (0xE722, 0x1ED5), (0xE72F, 0xB3), (0xE76A, 0x1EDB), (0xE76B, 0x25C7),
    (0xE76E, 0x300C), (0xE781, 0x4B), (0xE79E, 0x25CF), (0xE7A6, 0x1EB7), (0xE7EA, 0x394), (0xE7EB, 0xEA),
    (0xE829, 0x3B), (0xE831, 0x1ECC), (0xE833, 0x35), (0xE834, 0x25BD), (0xE858, 0x1EB6), (0xE878, 0x2160),
    (0xE887, 0x1EAF), (0xE898, 0x1EC3), (0xE899, 0x258C), (0xE8A4, 0x5F00), (0xE8C2, 0x2F47), (0xE8D3, 0x2468),
    (0xE8DC, 0x1EDD), (0xE909, 0x41), (0xE91F, 0x8000), (0xE927, 0x1EBD), (0xE92B, 0x1EA0), (0xE94B, 0x2460),
    (0xE951, 0x1ECD), (0xE960, 0x1EC6), (0xE968, 0x201D), (0xE971, 0x2165), (0xE984, 0x49), (0xE995, 0x2587),
    (0xE9C2, 0x1EEB), (0xE9ED, 0x1EF1), (0xE9FA, 0x1EE9), (0xEA0B, 0x103), (0xEA17, 0x5E55), (0xEA24, 0x1EED),
    (0xEA45, 0xD4), (0xEA59, 0x75), (0xEA5E, 0x1EB1), (0xEA70, 0xFD), (0xEA80, 0x78), (0xEA8A, 0x5361),
    (0xEA8D, 0x69), (0xEA94, 0x25C6), (0xEA99, 0x3015), (0xEA9A, 0x1EF5), (0xEAA0, 0xCA), (0xEAAD, 0x27),
    (0xEACA, 0x1EBA), (0xEAD3, 0xE7), (0xEADA, 0x266A), (0xEAEA, 0x23), (0xEB06, 0x4F), (0xEB08, 0x6211),
    (0xEB47, 0x1EAD), (0xEB60, 0x256F), (0xEB92, 0xE1), (0xEB95, 0x5B), (0xEBA1, 0x2169), (0xEBA9, 0x2022),
    (0xEBAE, 0x1A0), (0xEBC1, 0x43E), (0xEBC4, 0x2168), (0xEBD7, 0x4E), (0xEBD9, 0x71), (0xEBDE, 0x433),
    (0xEBE0, 0x50), (0xEBF0, 0x2122), (0xEC02, 0x1EE4), (0xEC04, 0x2161), (0xEC10, 0xDA), (0xEC13, 0xE3),
    (0xEC41, 0x1EBE), (0xEC4C, 0x1ECB), (0xEC50, 0x2665), (0xEC57, 0x30FD), (0xEC5D, 0x1EC8), (0xEC60, 0x1B0),
    (0xEC71, 0xC9), (0xEC7B, 0x62), (0xEC98, 0x2193), (0xECA9, 0x300B), (0xECB4, 0x30C4), (0xECB6, 0x300),
    (0xECCD, 0x102), (0xECDA, 0x25B2), (0xECE4, 0xC0), (0xECF2, 0x7720), (0xECFC, 0xF3), (0xED12, 0x6A),
    (0xED16, 0x1ECA), (0xED20, 0x2167), (0xED39, 0x2A), (0xED3D, 0xEC), (0xED4A, 0x70), (0xED5A, 0x1EE5),
    (0xED5E, 0x4D), (0xED62, 0x79BB), (0xED6E, 0x2F1D), (0xED70, 0xF5), (0xED91, 0x60), (0xED99, 0x2D),
    (0xEDA3, 0x2265), (0xEDAA, 0x25), (0xEDB8, 0x439), (0xEDD5, 0x25B3), (0xEDFA, 0x52), (0xEE3E, 0x2190),
    (0xEE5A, 0x2163), (0xEE75, 0xFFE5), (0xEE7E, 0xB0), (0xEE97, 0x5212), (0xEE99, 0x1EDE), (0xEEA0, 0xFC),
    (0xEED0, 0x51), (0xEEDE, 0xF9), (0xEEE3, 0x1EEA), (0xEEF3, 0x58), (0xEEF4, 0x1EF9), (0xEEFC, 0x2565),
    (0xEF10, 0x34), (0xEF16, 0x6E), (0xEF34, 0x24), (0xEF35, 0x2C7), (0xEF39, 0x3A3), (0xEF44, 0x32),
    (0xEF4A, 0x1EA6), (0xEF54, 0xFF05), (0xEF5E, 0x6C), (0xEF6C, 0x1EE2), (0xEF7D, 0x1EB3), (0xEF9F, 0x37),
    (0xEFB4, 0x61), (0xEFC6, 0x420), (0xEFD7, 0x53), (0xEFDC, 0x1EEC), (0xEFE9, 0x1EA7), (0xF011, 0x4E8E),
    (0xF02F, 0x4ECA), (0xF034, 0x2B), (0xF07F, 0x2461), (0xF098, 0x273F), (0xF09C, 0x2164), (0xF0A2, 0xAF),
    (0xF0AE, 0x25A0), (0xF0C0, 0xFF1C), (0xF0C5, 0x5E02), (0xF0D6, 0x14D), (0xF0E4, 0x1ED0), (0xF0ED, 0x1EB9),
    (0xF0EF, 0x26), (0xF0FA, 0x2F8B), (0xF100, 0x65), (0xF105, 0x43A), (0xF110, 0x6B), (0xF12C, 0x5A),
    (0xF136, 0x1AF), (0xF15D, 0x7C), (0xF182, 0x1EDC), (0xF18E, 0x1ED9), (0xF198, 0x2015), (0xF1AC, 0xFE4F),
    (0xF1C8, 0x2588), (0xF1D3, 0x1EEE), (0xF1D8, 0x2103), (0xF1E7, 0x66), (0xF1F1, 0xFF5C), (0xF1F2, 0xD8),
    (0xF201, 0x2212), (0xF20D, 0x45), (0xF219, 0x40), (0xF222, 0x1EF0), (0xF234, 0x73), (0xF240, 0xFE63),
    (0xF24A, 0x1ED4), (0xF256, 0x2030), (0xF25D, 0x6B64), (0xF261, 0x2605), (0xF266, 0x28), (0xF268, 0x1EC5),
    (0xF29D, 0xF2), (0xF2B8, 0x29), (0xF2C1, 0xB7), (0xF2CD, 0x5B89), (0xF2CE, 0x7E), (0xF2D8, 0xB4),
    (0xF2E9, 0xCD), (0xF2EF, 0x2E), (0xF30C, 0xFF08), (0xF32F, 0x1EE0), (0xF33A, 0xAB), (0xF33B, 0x6D41),
    (0xF345, 0x129), (0xF358, 0x1EA2), (0xF381, 0x9003), (0xF38B, 0x36), (0xF3BF, 0x2463), (0xF3C7, 0x4E0D),
    (0xF3D2, 0x39F), (0xF3EF, 0xFF3F), (0xF3FE, 0x1ED7), (0xF41A, 0x1ED8), (0xF441, 0xFA), (0xF449, 0xFF09),
    (0xF461, 0x3BD), (0xF4AE, 0x54), (0xF4BC, 0xF1), (0xF4CC, 0x57), (0xF4D1, 0x434), (0xF4DE, 0x2606),
    (0xF4E2, 0x2191), (0xF4EB, 0x39), (0xF509, 0x1EAE), (0xF521, 0x309D), (0xF53D, 0x1ECF), (0xF567, 0x256E),
    (0xF57E, 0x3A), (0xF58B, 0x1EC7), (0xF5B0, 0x221E), (0xF5B8, 0x2299), (0xF5F7, 0x4C), (0xF604, 0x21),
    (0xF611, 0x3F), (0xF622, 0x43), (0xF631, 0xDD), (0xF632, 0x25BC), (0xF635, 0x6D), (0xF637, 0x2207),
    (0xF660, 0xC2), (0xF66A, 0x72), (0xF672, 0x6253), (0xF68E, 0x2464), (0xF695, 0x2465), (0xF6A1, 0x201C),
    (0xF6B7, 0xD3), (0xF6D6, 0x1EF3), (0xF6DB, 0x2570), (0xF6E1, 0x1EE6), (0xF6E6, 0x300D), (0xF6F0, 0x414),
    (0xF704, 0xFFE3), (0xF707, 0xFE62), (0xF70A, 0x1EDA), (0xF713, 0x258A), (0xF71F, 0x2032), (0xF737, 0x2FA6),
    (0xF757, 0x2197), (0xF76B, 0x3BF), (0xF78A, 0x5F69), (0xF7A2, 0xFF1E), (0xF7A8, 0x3D), (0xF7CD, 0x2462),
    (0xF7CE, 0xAE), (0xF7D2, 0x203B), (0xF7DD, 0x591C), (0xF7F6, 0x1A1), (0xF818, 0x48), (0xF86B, 0x63),
    (0xF879, 0x2027), (0xF892, 0x5E), (0xF89A, 0x2012), (0xF8B3, 0xE2), (0xF8B8, 0x3B2), (0xF8B9, 0x68),
    (0xF8CF, 0x67), (0xF8D6, 0x25AA), (0xF8DD, 0x2162), (0xF8E0, 0x2589), (0xF8EF, 0x55), (0xF8F8, 0x56E0),
    (0xF8FA, 0x22),
)


def _pak_dir() -> str:
    root = nte.detect_game_path()
    if not root:
        raise FileNotFoundError("Kh\xf4ng t\xecm th\u1ea5y th\u01b0 m\u1ee5c game NTE")
    path = os.path.join(root, "Client", "WindowsNoEditor", "HT", "Content", "Paks")
    os.makedirs(path, exist_ok=True)
    return path


def _find_repak() -> str:
    appdir = os.environ.get("APPDIR")
    bundled = os.path.join(appdir, "usr", "bin", "repak") if appdir else None
    found = bundled if bundled and os.path.isfile(bundled) else shutil.which("repak")
    if not found:
        raise RuntimeError("Kh\xf4ng t\xecm th\u1ea5y repak \u0111\u1ec3 \u0111\xf3ng g\xf3i font NTE")
    return found


def _require_stopped():
    if nte.is_game_running():
        raise RuntimeError("H\xe3y \u0111\xf3ng NTE tr\u01b0\u1edbc khi thay \u0111\u1ed5i font")


def _font_mime(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError("Kh\xf4ng t\xecm th\u1ea5y file font \u0111\xe3 ch\u1ecdn")
    size = os.path.getsize(path)
    if not 12 <= size <= _MAX_FONT_SIZE:
        raise ValueError("K\xedch th\u01b0\u1edbc font kh\xf4ng h\u1ee3p l\u1ec7")
    with open(path, "rb") as source:
        magic = source.read(4)
    return _font_mime_for_magic(magic)


def _font_mime_for_magic(magic: bytes) -> str:
    if magic == b"\x00\x01\x00\x00":
        return "font/ttf"
    if magic == b"OTTO":
        return "font/otf"
    raise ValueError("File kh\xf4ng ph\u1ea3i font TTF/OTF h\u1ee3p l\u1ec7")


def _convert_cff_to_ttf(data: bytes) -> bytes:
    try:
        from fontTools.pens.cu2quPen import Cu2QuPen
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        from fontTools.ttLib import TTFont, newTable
    except ImportError as error:
        raise RuntimeError("Launcher thi\u1ebfu b\u1ed9 chuy\u1ec3n \u0111\u1ed5i font OpenType/CFF") from error

    font = TTFont(io.BytesIO(data))
    if font.sfntVersion != "OTTO" or "CFF " not in font:
        raise ValueError("Font OpenType kh\xf4ng d\xf9ng CFF outlines n\xean kh\xf4ng th\u1ec3 chuy\u1ec3n \u0111\u1ed5i")
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


def _extract_pua_map_from_font(font_bytes: bytes) -> dict[int, int]:
    try:
        num_tables = struct.unpack(">H", font_bytes[4:6])[0]
        cmap_offset = None
        for i in range(num_tables):
            entry = font_bytes[12 + i * 16 : 28 + i * 16]
            if entry[:4] == b"cmap":
                cmap_offset = struct.unpack(">I", entry[8:12])[0]
                break
        if cmap_offset is None:
            return {}

        num_cmap_tables = struct.unpack(">H", font_bytes[cmap_offset + 2 : cmap_offset + 4])[0]
        fmt12_offset = None
        for i in range(num_cmap_tables):
            rec = font_bytes[cmap_offset + 4 + i * 8 : cmap_offset + 12 + i * 8]
            pid, eid, off = struct.unpack(">HHI", rec)
            if pid == 3 and eid == 10:
                fmt12_offset = cmap_offset + off
                break
        if fmt12_offset is None:
            return {}

        fmt, _, _, _, num_groups = struct.unpack(">HHIII", font_bytes[fmt12_offset : fmt12_offset + 16])
        if fmt != 12:
            return {}

        glyph_to_std = {}
        pua_to_glyph = {}
        for i in range(num_groups):
            grp = font_bytes[fmt12_offset + 16 + i * 12 : fmt12_offset + 28 + i * 12]
            start_c, end_c, start_g = struct.unpack(">III", grp)
            for c in range(start_c, end_c + 1):
                g = start_g + (c - start_c)
                if 0xE000 <= c <= 0xF8FF:
                    pua_to_glyph[c] = g
                else:
                    glyph_to_std.setdefault(g, []).append(c)

        pua_map = {}
        for pua, g in pua_to_glyph.items():
            std_chars = glyph_to_std.get(g, [])
            v = [c for c in std_chars if c < 0x2500]
            if v:
                pua_map[pua] = v[0]
            elif std_chars:
                pua_map[pua] = std_chars[0]
        return pua_map
    except Exception:
        return {}


def _get_pua_map(backup_pak: str | None = None) -> dict[int, int]:
    if backup_pak and os.path.isfile(backup_pak):
        try:
            res = subprocess.run(
                [_find_repak(), "get", backup_pak, FONT_ASSET_PATHS[0]],
                capture_output=True,
                check=True,
            )
            raw = res.stdout
            if len(raw) > 8:
                font_data = _unwrap_ufont(raw)
                extracted = _extract_pua_map_from_font(font_data)
                if len(extracted) >= 100:
                    return extracted
        except Exception:
            pass
    return dict(EMBEDDED_PUA_PAIRS)


def _patch_font_cmap(font_data: bytes, pua_map: dict[int, int]) -> bytes:
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return font_data

    try:
        font = TTFont(io.BytesIO(font_data))
    except Exception:
        return font_data

    cmap_tables = [t for t in font["cmap"].tables if t.isUnicode()]
    if not cmap_tables:
        return font_data

    best_cmap = font.getBestCmap()
    space_gid = best_cmap.get(ord(" ")) or ".notdef"

    for pua, target in pua_map.items():
        gid = best_cmap.get(target)
        if not gid:
            fallback = FALLBACK_SYMBOLS.get(target)
            if fallback:
                gid = best_cmap.get(fallback)
        if not gid:
            gid = space_gid
        for t in cmap_tables:
            t.cmap[pua] = gid

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
        raise ValueError("PAK font NTE ch\u1ee9a d\u1eef li\u1ec7u font kh\xf4ng h\u1ee3p l\u1ec7")
    return payload[4:-4]


def _pak_entries(path: str) -> set[str]:
    if not os.path.isfile(path) or not 1 <= os.path.getsize(path) <= _MAX_PAK_SIZE:
        raise ValueError("File PAK font NTE kh\xf4ng h\u1ee3p l\u1ec7")
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


def _create_font_override_pak(font_data: bytes):
    pak_dir = _pak_dir()
    translation_pak = os.path.join(pak_dir, TRANSLATION_PAK_NAME)
    backup = _backup_path()

    if not os.path.isfile(translation_pak) and not os.path.isfile(backup):
        raise FileNotFoundError("H\xe3y c\xe0i Vi\u1ec7t h\xf3a NTE tr\u01b0\u1edbc khi \u0111\u1ed5i font")

    os.makedirs(os.path.dirname(backup), exist_ok=True)
    if not os.path.isfile(backup) and os.path.isfile(translation_pak):
        shutil.copyfile(translation_pak, backup)

    locres_source = backup if os.path.isfile(backup) else translation_pak
    locres_bytes = subprocess.run(
        [_find_repak(), "get", locres_source, LOCRES_ASSET_PATH],
        check=True,
        capture_output=True,
    ).stdout

    pua_map = _get_pua_map(backup)
    patched_font = _patch_font_cmap(font_data, pua_map)
    ufont_payload = _wrap_ufont(patched_font)

    with tempfile.TemporaryDirectory(prefix=".nte-font-", dir=pak_dir) as workspace:
        source_root = os.path.join(workspace, "source")
        for relative in FONT_ASSET_PATHS:
            path = os.path.join(source_root, *relative.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as output:
                output.write(ufont_payload)

        locres_target = os.path.join(source_root, *LOCRES_ASSET_PATH.split("/"))
        os.makedirs(os.path.dirname(locres_target), exist_ok=True)
        with open(locres_target, "wb") as output:
            output.write(locres_bytes)

        packed = os.path.join(workspace, TRANSLATION_PAK_NAME)
        subprocess.run(
            [_find_repak(), "pack", "-q", "--version", "V8B", "-m", "../../../", source_root, packed],
            check=True,
            capture_output=True,
        )
        shutil.move(packed, translation_pak)

    legacy_override = os.path.join(pak_dir, CUSTOM_FONT_PAK_NAME)
    if os.path.isfile(legacy_override):
        try:
            os.unlink(legacy_override)
        except OSError:
            pass


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
    translation_pak = os.path.join(pak_dir, TRANSLATION_PAK_NAME)
    backup = _backup_path()
    cfg = wuwa_game.load_config()
    has_custom = bool(cfg.get("nte_custom_font_name")) and os.path.isfile(backup)
    has_default = os.path.isfile(backup) or os.path.isfile(translation_pak)
    return {
        "active_font": "custom" if has_custom else "default" if os.path.isfile(translation_pak) else "none",
        "custom_font_name": cfg.get("nte_custom_font_name") if has_custom else None,
        "default_available": has_default,
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
    _create_font_override_pak(font_data)

    _save_preview(font_data, mime)
    name = os.path.splitext(os.path.basename(font_path))[0]
    _save_name(name)
    return {"ok": True, "font_name": name, "pak_file": TRANSLATION_PAK_NAME}


def install_font_from_pak(pak_path: str) -> dict:
    _require_stopped()
    if not set(FONT_ASSET_PATHS).issubset(_pak_entries(pak_path)):
        raise ValueError("PAK kh\xf4ng ph\u1ea3i g\xf3i font NTE h\u1ee3p l\u1ec7")
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
    _create_font_override_pak(extracted)
    _save_preview(extracted, mime)
    name = os.path.splitext(os.path.basename(pak_path))[0]
    _save_name(name)
    return {"ok": True, "font_name": name, "pak_file": TRANSLATION_PAK_NAME}


def install_default_font() -> dict:
    _require_stopped()
    pak_dir = _pak_dir()
    backup = _backup_path()
    translation_pak = os.path.join(pak_dir, TRANSLATION_PAK_NAME)
    if os.path.isfile(backup):
        shutil.copyfile(backup, translation_pak)
    legacy = os.path.join(pak_dir, CUSTOM_FONT_PAK_NAME)
    if os.path.isfile(legacy):
        try:
            os.unlink(legacy)
        except OSError:
            pass
    cache = _cache_path()
    if os.path.isfile(cache):
        os.unlink(cache)
    cfg = wuwa_game.load_config()
    cfg.pop("nte_custom_font_name", None)
    cfg.pop("nte_custom_font_mime", None)
    wuwa_game.save_config(cfg)
    return {"ok": True, "font_name": "MiSans (M\u1eb7c \u0111\u1ecbnh NTE)"}
