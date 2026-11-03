"""LZ00 compression of the Cotton Boomerang sprites (the format cblib.unlz
reads): "LZ00", the unpacked size (32-bit), then
  byte b < 0x10: b + 1 literal bytes follow
  byte b >= 0x10: copy (next byte + 3) bytes from b - 0x0f bytes back"""
import struct

MAXD = 0xff - 0x0f      # farthest distance
MAXL = 0xff + 3         # longest copy


def lz(data):
    out = bytearray(b'LZ00' + struct.pack('>I', len(data)))
    lit = bytearray()

    def flush():
        while lit:
            n = min(len(lit), 16)
            out.append(n - 1)
            out.extend(lit[:n])
            del lit[:n]
    i = 0
    n = len(data)
    while i < n:
        best_l = best_d = 0
        for d in range(1, min(MAXD, i) + 1):
            l = 0
            while l < MAXL and i + l < n and data[i + l - d] == data[i + l]:
                l += 1
            if l > best_l:
                best_l, best_d = l, d
                if l == MAXL:
                    break
        if best_l >= 3:
            flush()
            out.append(best_d + 0x0f)
            out.append(best_l - 3)
            i += best_l
        else:
            lit.append(data[i])
            i += 1
    flush()
    return bytes(out)
