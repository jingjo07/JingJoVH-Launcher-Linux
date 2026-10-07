#!/usr/bin/env python3
"""
JingJoVH Payload Encryptor & Native Packer
Packages backend modules into an encrypted binary payload
and produces libJingJoNative.so native C decryptor.
"""

import os
import sys
import zlib
import json
import shutil
import subprocess

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


def main():
    if len(sys.argv) < 2:
        print("Usage: encrypt_payload.py <APP_DIR>")
        sys.exit(1)

    app_dir = os.path.abspath(sys.argv[1])
    backend_dir = os.path.join(app_dir, "backend")

    if not os.path.isdir(backend_dir):
        print(f"[!] Error: Missing backend directory in {app_dir}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    native_c = os.path.join(script_dir, "native.c")
    out_lib_dir = os.path.join(app_dir, "usr", "lib")
    os.makedirs(out_lib_dir, exist_ok=True)
    out_so = os.path.join(out_lib_dir, "libJingJoNative.so")

    print(f"[*] Biên dịch native library C: {out_so}...")
    subprocess.check_call([
        "gcc", "-O3", "-fPIC", "-shared", "-s",
        "-fvisibility=hidden",
        native_c, "-o", out_so
    ])

    print("[*] Đóng gói các module Python backend...")
    modules = {}
    for root, _, files in os.walk(backend_dir):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, backend_dir)
                mod_name = rel_path.replace("/", ".").removesuffix(".py")
                with open(full_path, "r", encoding="utf-8") as sf:
                    modules[mod_name] = sf.read()

    print(f"[*] Thu thập {len(modules)} module backend.")

    payload_json = json.dumps(modules).encode("utf-8")
    compressed = zlib.compress(payload_json, 9)
    encrypted = encrypt(compressed)

    out_dat = os.path.join(app_dir, "backend.dat")
    with open(out_dat, "wb") as f:
        f.write(encrypted)

    print(f"[*] Ghi file nhị phân mã hóa: {out_dat} ({len(encrypted) // 1024} KB).")

    # Xóa toàn bộ file .py trong thư mục backend của AppDir
    shutil.rmtree(backend_dir)
    os.makedirs(backend_dir, exist_ok=True)
    print("[*] Đã xóa toàn bộ file mã nguồn .py trong thư mục backend.")

    # Tạo backend/__init__.py làm native loader duy nhất
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
        _modules = json.loads(_dec.decode("utf-8"))
        del _dec
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
        code_str = _modules.get(sub, "")
        module.__file__ = os.path.join(_APPDIR, "backend", sub + ".py")
        compiled = compile(code_str, f"<native:{sub}>", "exec")
        exec(compiled, module.__dict__)

sys.meta_path.insert(0, _SubmoduleLoader())
'''

    init_file = os.path.join(backend_dir, "__init__.py")
    with open(init_file, "w", encoding="utf-8") as f:
        f.write(loader_init_code)

    print("[*] Đã cấu hình backend/__init__.py native loader.")
    print("[+] Hoàn tất mã hóa toàn bộ backend!")


if __name__ == "__main__":
    main()
