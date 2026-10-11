#!/usr/bin/env python3
"""
JingJoVH Payload Obfuscator & Native Packer
- Packages backend modules & launcher.py into an XOR-obfuscated payload
- Produces libJingJoNative.so native C decoder
- Replaces launcher.py with a 15-line native stub
- Obfuscates frontend/app.js so no plain source code remains

This is source obfuscation, not a security boundary: the offline client contains
everything needed to recover its code.
"""

import os
import sys
import zlib
import json
import shutil
import subprocess
from pathlib import Path

MASTER_KEY = bytes([
    0x57, 0x75, 0x57, 0x61, 0x5F, 0x4E, 0x54, 0x45,
    0x5F, 0x4A, 0x69, 0x6E, 0x67, 0x4A, 0x6F, 0x5F,
    0x56, 0x48, 0x5F, 0x32, 0x30, 0x32, 0x36, 0x21,
    0x9A, 0x8B, 0x7C, 0x6D, 0x5E, 0x4F, 0x3E, 0x2D
])


def encrypt(data: bytes) -> bytes:
    out = bytearray(len(data))
    for i in range(len(data)):
        k = MASTER_KEY[i % len(MASTER_KEY)] ^ ((i * 37 + 101) & 0xFF)
        out[i] = data[i] ^ k
    return bytes(out)


def _checked_app_dir(raw_path: str) -> Path:
    app_dir = Path(raw_path).resolve()
    build_dir = Path(__file__).resolve().parent.parent / "build"
    if not app_dir.is_relative_to(build_dir) or app_dir.suffix != ".AppDir":
        raise ValueError(f"Refusing to package outside build/*.AppDir: {app_dir}")
    return app_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: encrypt_payload.py <APP_DIR>")
        sys.exit(1)

    app_dir = str(_checked_app_dir(sys.argv[1]))
    backend_dir = os.path.join(app_dir, "backend")
    launcher_file = os.path.join(app_dir, "launcher.py")

    if not os.path.isdir(backend_dir) or not os.path.isfile(launcher_file):
        sys.exit(f"[!] Error: Missing backend or launcher.py in {app_dir}")

    # 1. Biên dịch native C shared library
    script_dir = os.path.dirname(os.path.abspath(__file__))
    native_c = os.path.join(script_dir, "native.c")
    out_lib_dir = os.path.join(app_dir, "usr", "lib")
    os.makedirs(out_lib_dir, exist_ok=True)
    out_so = os.path.join(out_lib_dir, "libJingJoNative.so")

    print(f"[*] [1/4] Biên dịch native library C: {out_so}...")
    subprocess.check_call([
        "gcc", "-O3", "-fPIC", "-shared", "-s",
        "-fvisibility=hidden",
        native_c, "-o", out_so
    ])

    # 2. Đóng gói các module Python backend + launcher.py
    print("[*] [2/4] Đóng gói và mã hóa backend & launcher.py...")
    modules = {}
    for root, _, files in os.walk(backend_dir):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, backend_dir)
                mod_name = rel_path.replace("/", ".").removesuffix(".py")
                with open(full_path, "r", encoding="utf-8") as sf:
                    modules[mod_name] = sf.read()

    if os.path.isfile(launcher_file):
        with open(launcher_file, "r", encoding="utf-8") as lf:
            modules["__main_launcher__"] = lf.read()

    print(f"[*] Thu thập {len(modules)} module ({len(modules) - 1} backend + launcher.py).")

    payload_json = json.dumps(modules).encode("utf-8")
    compressed = zlib.compress(payload_json, 9)
    encrypted = encrypt(compressed)

    out_dat = os.path.join(app_dir, "backend.dat")
    with open(out_dat, "wb") as f:
        f.write(encrypted)

    print(f"[*] Ghi file nhị phân mã hóa: {out_dat} ({len(encrypted) // 1024} KB).")

    # Xóa toàn bộ file .py trong backend của AppDir
    shutil.rmtree(backend_dir)
    os.makedirs(backend_dir, exist_ok=True)

    # backend/__init__.py làm native loader
    loader_init_code = '''# JingJoVH Native Package Loader
import os, sys, zlib, json, ctypes
from importlib.machinery import ModuleSpec

_APPDIR = os.environ.get("APPDIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LIB_SO = os.path.join(_APPDIR, "usr", "lib", "libJingJoNative.so")
_DAT_PATH = os.path.join(_APPDIR, "backend.dat")

_modules = {}
if os.path.isfile(_LIB_SO) and os.path.isfile(_DAT_PATH):
    try:
        _native = ctypes.CDLL(_LIB_SO)
        _native.NativeDecrypt.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)]
        _native.NativeDecrypt.restype = None
        with open(_DAT_PATH, "rb") as _f:
            _enc = _f.read()
        _in_buf = (ctypes.c_uint8 * len(_enc)).from_buffer_copy(_enc)
        _out_buf = (ctypes.c_uint8 * len(_enc))()
        _native.NativeDecrypt(_in_buf, len(_enc), _out_buf)
        _dec = zlib.decompress(bytes(_out_buf))
        del _in_buf, _out_buf, _enc
        _source = json.loads(_dec.decode("utf-8"))
        _modules = {name: compile(source, f"<native:{name}>", "exec")
                    for name, source in _source.items()}
        del _dec, _source
    except Exception as _e:
        sys.stderr.write(f"[JingJoVH] Native decrypt error: {_e}\\n")

class _SubmoduleLoader:
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("backend."):
            sub = fullname[8:]
            if sub in _modules:
                return ModuleSpec(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        sub = module.__name__[8:]
        module.__file__ = os.path.join(_APPDIR, "backend", sub + ".py")
        exec(_modules[sub], module.__dict__)

sys.meta_path.insert(0, _SubmoduleLoader())
'''
    with open(os.path.join(backend_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(loader_init_code)

    # 3. Thay thế launcher.py bằng native bootstrap stub
    print("[*] [3/4] Thay thế launcher.py bằng native bootstrap stub...")
    launcher_stub = '''#!/usr/bin/env python3
"""JingJoVH Launcher — Native Bootstrapper"""
import os, sys
import backend

appdir = os.environ.get("APPDIR") or os.path.dirname(os.path.abspath(__file__))
launcher_code = backend._modules.get("__main_launcher__")
if launcher_code is None:
    sys.exit("[JingJoVH] Failed to load native launcher payload.")

launcher_globals = {
    "__name__": "__main__",
    "__file__": os.path.join(appdir, "launcher.py"),
    "__doc__": None,
}
exec(launcher_code, launcher_globals)
'''
    with open(launcher_file, "w", encoding="utf-8") as lf:
        lf.write(launcher_stub)
    os.chmod(launcher_file, 0o755)

    # Xóa wuwa_launcher.sh nếu còn sót trong AppDir
    sh_file = os.path.join(app_dir, "wuwa_launcher.sh")
    if os.path.isfile(sh_file):
        os.unlink(sh_file)

    # 4. Làm rối mã nguồn frontend/app.js
    app_js = os.path.join(app_dir, "frontend", "app.js")
    if os.path.isfile(app_js):
        print("[*] [4/4] Đang làm rối (obfuscate) frontend/app.js...")
        subprocess.run([
            "npx", "--yes", "--package=javascript-obfuscator@4.1.1",
            "javascript-obfuscator", app_js, "--output", app_js,
            "--compact", "true",
            "--string-array", "true",
            "--string-array-encoding", "base64",
            "--string-array-threshold", "0.75"
        ], check=True)
        print("[+] Đã làm rối frontend/app.js!")

    print("[+] Hoàn tất đóng gói và làm rối AppDir!")


if __name__ == "__main__":
    main()
