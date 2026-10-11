#include <stddef.h>
#include <stdint.h>

/*
 * JingJoVH native XOR payload decoder (obfuscation, not cryptographic security).
 */

static const uint8_t MASTER_KEY[] = {
    0x57, 0x75, 0x57, 0x61, 0x5F, 0x4E, 0x54, 0x45,
    0x5F, 0x4A, 0x69, 0x6E, 0x67, 0x4A, 0x6F, 0x5F,
    0x56, 0x48, 0x5F, 0x32, 0x30, 0x32, 0x36, 0x21,
    0x9A, 0x8B, 0x7C, 0x6D, 0x5E, 0x4F, 0x3E, 0x2D
};

__attribute__((visibility("default")))
void NativeDecrypt(const uint8_t* in, size_t len, uint8_t* out) {
    if (!in || !out || len == 0) return;
    for (size_t i = 0; i < len; ++i) {
        uint8_t k = MASTER_KEY[i % sizeof(MASTER_KEY)];
        k ^= (uint8_t)((i * 37 + 101) & 0xFF);
        out[i] = in[i] ^ k;
    }
}
