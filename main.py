#!/usr/bin/env python3
"""DETIK SEBELUM -- ai-excited-01 entry.

A tiny human silhouette stands on a dark plain before a colossal glowing
torus ring in the night sky: one focal point, extreme contrast, scale.
Pure Python 3 stdlib, no network, deterministic (fixed seed).

Writes one 1024x1024 JPEG (named entry.png, per the kit: the file is told
apart by its first bytes) to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
JPEG is chosen because the tie-break favours the smaller file.
"""
import math
import os
import random

W = H = 1024
SEED = 20261116
QUALITY = 88

# ---------------------------------------------------------------- render ----

def render():
    buf = bytearray(W * H * 3)
    rnd = random.Random(SEED)

    # --- sky: vertical gradient, per-row fill (fast) ---
    # (y, r, g, b) stops
    stops = [(0, 3, 6, 20), (420, 8, 14, 40), (700, 14, 20, 52),
             (855, 18, 24, 54), (856, 7, 9, 16), (1024, 2, 2, 5)]
    for (y0, r0, g0, b0), (y1, r1, g1, b1) in zip(stops, stops[1:]):
        for y in range(y0, y1):
            t = (y - y0) / max(1, y1 - y0 - 1)
            r = int(r0 + (r1 - r0) * t)
            g = int(g0 + (g1 - g0) * t)
            b = int(b0 + (b1 - b0) * t)
            base = y * W * 3
            buf[base:base + W * 3] = bytes((r, g, b)) * W

    # --- ambient glow behind the ring ---
    cx, cy = 512.0, 400.0
    for y in range(0, 855):
        dy = (y - cy) / 520.0
        for x in range(0, W):
            dx = (x - cx) / 520.0
            d2 = dx * dx + dy * dy
            if d2 > 1.0:
                continue
            f = (1.0 - d2) ** 2 * 0.55
            i = (y * W + x) * 3
            buf[i] = min(255, buf[i] + int(26 * f))
            buf[i + 1] = min(255, buf[i + 1] + int(52 * f))
            buf[i + 2] = min(255, buf[i + 2] + int(120 * f))

    # --- stars (seeded) ---
    for _ in range(340):
        x = rnd.randrange(0, W)
        y = rnd.randrange(0, 810)
        v = rnd.randrange(50, 230)
        i = (y * W + x) * 3
        buf[i] = min(255, buf[i] + v)
        buf[i + 1] = min(255, buf[i + 1] + v)
        buf[i + 2] = min(255, buf[i + 2] + v)
        if v > 185:  # bright star: tiny cross
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + ox, y + oy
                if 0 <= xx < W and 0 <= yy < H:
                    j = (yy * W + xx) * 3
                    hv = v // 3
                    buf[j] = min(255, buf[j] + hv)
                    buf[j + 1] = min(255, buf[j + 1] + hv)
                    buf[j + 2] = min(255, buf[j + 2] + hv)

    # --- palette around the ring (256-entry lookup) ---
    pal_stops = [(90, 225, 255), (120, 110, 255), (255, 95, 210),
                 (255, 150, 80), (90, 225, 255)]
    pal = []
    for k in range(256):
        t = k / 255.0 * 4.0
        s = int(t)
        if s >= 4:
            s = 3
            f = 1.0
        else:
            f = t - s
        c0, c1 = pal_stops[s], pal_stops[s + 1]
        pal.append((int(c0[0] + (c1[0] - c0[0]) * f),
                    int(c0[1] + (c1[1] - c0[1]) * f),
                    int(c0[2] + (c1[2] - c0[2]) * f)))

    # --- the colossal torus ---
    a, b = 435.0, 305.0
    ia, ib = 1.0 / a, 1.0 / b
    exp = math.exp
    sqrt = math.sqrt
    atan2 = math.atan2
    pi = math.pi
    hot_ang = -2.05  # upper-left hot spot
    for y in range(0, 790):
        dy = (y - cy) * ib
        row = y * W
        for x in range(0, W):
            dx = (x - cx) * ia
            r = sqrt(dx * dx + dy * dy)
            d = r - 1.0
            if d > 0.42 or d < -0.42:
                continue
            ad = d if d >= 0 else -d
            core = exp(-(d / 0.013) * (d / 0.013))
            body = exp(-(d / 0.080) * (d / 0.080))
            halo = exp(-(d / 0.24) * (d / 0.24))
            inten = core * 1.05 + body * 0.85 + halo * 0.42
            if inten < 0.02:
                continue
            ang = atan2(dy, dx)
            # hot spot boost (upper-left of the ring)
            da = ang - hot_ang
            while da > pi:
                da -= 2 * pi
            while da < -pi:
                da += 2 * pi
            hot = exp(-(da / 0.38) * (da / 0.38))
            pr, pg, pb = pal[int((ang + pi) / (2 * pi) * 255.0) & 255]
            r_ = pr * inten + hot * 255.0 * (core + body * 0.6)
            g_ = pg * inten + hot * 240.0 * (core + body * 0.6)
            b_ = pb * inten + hot * 235.0 * (core + body * 0.6)
            i = (row + x) * 3
            if r_ > 0:
                buf[i] = 255 if buf[i] + r_ > 255 else buf[i] + int(r_)
            if g_ > 0:
                buf[i + 1] = 255 if buf[i + 1] + g_ > 255 else buf[i + 1] + int(g_)
            if b_ > 0:
                buf[i + 2] = 255 if buf[i + 2] + b_ > 255 else buf[i + 2] + int(b_)

    # --- light beam: ring bottom -> the figure ---
    for y in range(700, 932):
        t = (y - 700) / 232.0
        half = 7.0 + t * 30.0
        strength = 0.20 * (1.0 - t * 0.45)
        row = y * W
        for x in range(512 - int(half) - 4, 512 + int(half) + 5):
            dd = (x - 512.0) / half
            f = exp(-dd * dd * 2.2) * strength
            if f < 0.008:
                continue
            i = (row + x) * 3
            buf[i] = min(255, buf[i] + int(120 * f))
            buf[i + 1] = min(255, buf[i + 1] + int(200 * f))
            buf[i + 2] = min(255, buf[i + 2] + int(255 * f))

    # --- ground reflection of the ring ---
    for y in range(855, 1024):
        fall = math.exp(-(y - 855) / 95.0)
        row = y * W
        for x in range(150, 875):
            prof = math.exp(-((x - 512.0) / 330.0) ** 2)
            f = fall * prof * 0.16
            if f < 0.004:
                continue
            i = (row + x) * 3
            buf[i] = min(255, buf[i] + int(70 * f))
            buf[i + 1] = min(255, buf[i + 1] + int(130 * f))
            buf[i + 2] = min(255, buf[i + 2] + int(235 * f))

    # --- the tiny human (88 px tall, back to viewer, facing the ring) ---
    def fig_px(x, y, rim):
        i = (y * W + x) * 3
        if rim:
            buf[i] = 110
            buf[i + 1] = 200
            buf[i + 2] = 255
        else:
            buf[i] = 2
            buf[i + 1] = 2
            buf[i + 2] = 5

    # head: disc, rim-lit on the top and ring-facing side
    for dy in range(-8, 9):
        for dx in range(-8, 9):
            if dx * dx + dy * dy <= 64:
                fig_px(512 + dx, 857 + dy, dy <= -5 or dx >= 5)
    # torso: shoulders tapering to the waist
    for y in range(867, 907):
        hw = 14 - (y - 867) * 4 // 39
        for x in range(512 - hw, 512 + hw + 1):
            fig_px(x, y, x >= 512 + hw - 1 or y == 867)
    # legs: two dark columns, rim on their outer right edges
    for y in range(907, 931):
        for x in range(502, 510):
            fig_px(x, y, x == 509)
        for x in range(515, 523):
            fig_px(x, y, x == 522)
    # glow pool around the figure's feet
    for y in range(912, 958):
        for x in range(460, 565):
            d2 = ((x - 512.0) / 44.0) ** 2 + ((y - 930.0) / 18.0) ** 2
            if d2 > 1.0:
                continue
            f = (1.0 - d2) * 0.35
            i = (y * W + x) * 3
            buf[i] = min(255, buf[i] + int(60 * f))
            buf[i + 1] = min(255, buf[i + 1] + int(120 * f))
            buf[i + 2] = min(255, buf[i + 2] + int(180 * f))
    return buf


# ------------------------------------------------------- JPEG encoder ------
# Baseline DCT JPEG, 4:2:0, standard Annex K Huffman tables, quality 88.

ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5,
          12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21,
          28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37,
          44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47,
          55, 62, 63]

QLUM = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
        14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
        18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
        49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]
QCHR = [17, 18, 24, 47, 99, 99, 99, 99, 18, 21, 26, 66, 99, 99, 99, 99,
        24, 26, 56, 99, 99, 99, 99, 99, 47, 66, 99, 99, 99, 99, 99, 99,
        99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
        99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99]

# (counts per code length 1..16, symbols) -- JPEG Annex K standard tables
H_DC_LUM = ([0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
            list(range(12)))
H_DC_CHR = ([0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
            list(range(12)))
H_AC_LUM = ([0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7d],
            [0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31,
             0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
             0x81, 0x91, 0xa1, 0x08, 0x23, 0x42, 0xb1, 0xc1, 0x15, 0x52,
             0xd1, 0xf0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0a, 0x16,
             0x17, 0x18, 0x19, 0x1a, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2a,
             0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x43, 0x44, 0x45,
             0x46, 0x47, 0x48, 0x49, 0x4a, 0x53, 0x54, 0x55, 0x56, 0x57,
             0x58, 0x59, 0x5a, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
             0x6a, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7a, 0x83,
             0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x92, 0x93, 0x94,
             0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0xa2, 0xa3, 0xa4, 0xa5,
             0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6,
             0xb7, 0xb8, 0xb9, 0xba, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7,
             0xc8, 0xc9, 0xca, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8,
             0xd9, 0xda, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8,
             0xe9, 0xea, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8,
             0xf9, 0xfa])
H_AC_CHR = ([0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 0x77],
            [0x00, 0x01, 0x02, 0x03, 0x11, 0x04, 0x05, 0x21, 0x31, 0x06,
             0x12, 0x41, 0x51, 0x07, 0x61, 0x71, 0x13, 0x22, 0x32, 0x81,
             0x08, 0x14, 0x42, 0x91, 0xa1, 0xb1, 0xc1, 0x09, 0x23, 0x33,
             0x52, 0xf0, 0x15, 0x62, 0x72, 0xd1, 0x0a, 0x16, 0x24, 0x34,
             0xe1, 0x25, 0xf1, 0x17, 0x18, 0x19, 0x1a, 0x26, 0x27, 0x28,
             0x29, 0x2a, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x43, 0x44,
             0x45, 0x46, 0x47, 0x48, 0x49, 0x4a, 0x53, 0x54, 0x55, 0x56,
             0x57, 0x58, 0x59, 0x5a, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68,
             0x69, 0x6a, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7a,
             0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x92,
             0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0xa2, 0xa3,
             0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xb2, 0xb3, 0xb4,
             0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xc2, 0xc3, 0xc4, 0xc5,
             0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6,
             0xd7, 0xd8, 0xd9, 0xda, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7,
             0xe8, 0xe9, 0xea, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8,
             0xf9, 0xfa])


def _huff_codes(counts, symbols):
    """Canonical Huffman (code, length) per symbol from Annex K tables."""
    codes = {}
    code = 0
    k = 0
    for length in range(1, 17):
        for _ in range(counts[length - 1]):
            codes[symbols[k]] = (code, length)
            k += 1
            code += 1
        code <<= 1
    return codes


def _scale_quant(base, quality):
    if quality < 50:
        scale = 5000 // quality
    else:
        scale = 200 - 2 * quality
    out = []
    for i, q in enumerate(base):
        v = (q * scale + 50) // 100
        v = 1 if v < 1 else (255 if v > 255 else v)
        out.append(v)
    return out


def _fdct(block):
    """In-place AAN forward DCT on 64 floats (row-major)."""
    # rows
    for r in range(8):
        o = r * 8
        x0, x1, x2, x3, x4, x5, x6, x7 = block[o:o + 8]
        tmp0 = x0 + x7
        tmp7 = x0 - x7
        tmp1 = x1 + x6
        tmp6 = x1 - x6
        tmp2 = x2 + x5
        tmp5 = x2 - x5
        tmp3 = x3 + x4
        tmp4 = x3 - x4
        tmp10 = tmp0 + tmp3
        tmp13 = tmp0 - tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp1 - tmp2
        block[o] = tmp10 + tmp11
        block[o + 4] = tmp10 - tmp11
        z1 = (tmp12 + tmp13) * 0.541196100
        block[o + 2] = z1 + tmp13 * 0.765366865
        block[o + 6] = z1 + tmp12 * -1.847759065
        z1 = tmp4 + tmp7
        z2 = tmp5 + tmp6
        z3 = tmp4 + tmp6
        z4 = tmp5 + tmp7
        z5 = (z3 + z4) * 1.175875602
        tmp4 *= 0.298631336
        tmp5 *= 2.053119869
        tmp6 *= 3.072711026
        tmp7 *= 1.501321110
        z1 *= -0.899976223
        z2 *= -2.562915447
        z3 *= -1.961570560
        z4 *= -0.390180644
        z3 += z5
        z4 += z5
        block[o + 7] = tmp4 + z1 + z3
        block[o + 5] = tmp5 + z2 + z4
        block[o + 3] = tmp6 + z2 + z3
        block[o + 1] = tmp7 + z1 + z4
    # columns
    for c in range(8):
        x0 = block[c]
        x1 = block[8 + c]
        x2 = block[16 + c]
        x3 = block[24 + c]
        x4 = block[32 + c]
        x5 = block[40 + c]
        x6 = block[48 + c]
        x7 = block[56 + c]
        tmp0 = x0 + x7
        tmp7 = x0 - x7
        tmp1 = x1 + x6
        tmp6 = x1 - x6
        tmp2 = x2 + x5
        tmp5 = x2 - x5
        tmp3 = x3 + x4
        tmp4 = x3 - x4
        tmp10 = tmp0 + tmp3
        tmp13 = tmp0 - tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp1 - tmp2
        block[c] = tmp10 + tmp11
        block[32 + c] = tmp10 - tmp11
        z1 = (tmp12 + tmp13) * 0.541196100
        block[16 + c] = z1 + tmp13 * 0.765366865
        block[48 + c] = z1 + tmp12 * -1.847759065
        z1 = tmp4 + tmp7
        z2 = tmp5 + tmp6
        z3 = tmp4 + tmp6
        z4 = tmp5 + tmp7
        z5 = (z3 + z4) * 1.175875602
        tmp4 *= 0.298631336
        tmp5 *= 2.053119869
        tmp6 *= 3.072711026
        tmp7 *= 1.501321110
        z1 *= -0.899976223
        z2 *= -2.562915447
        z3 *= -1.961570560
        z4 *= -0.390180644
        z3 += z5
        z4 += z5
        block[56 + c] = tmp4 + z1 + z3
        block[40 + c] = tmp5 + z2 + z4
        block[24 + c] = tmp6 + z2 + z3
        block[8 + c] = tmp7 + z1 + z4


class _Bits:
    __slots__ = ("buf", "acc", "n")

    def __init__(self):
        self.buf = bytearray()
        self.acc = 0
        self.n = 0

    def put(self, code, nbits):
        if nbits == 0:
            return
        self.acc = (self.acc << nbits) | code
        self.n += nbits
        while self.n >= 8:
            self.n -= 8
            b = (self.acc >> self.n) & 0xFF
            self.buf.append(b)
            if b == 0xFF:
                self.buf.append(0)
        self.acc &= (1 << self.n) - 1 if self.n else 0

    def flush(self):
        if self.n:
            b = ((self.acc << (8 - self.n)) | ((1 << (8 - self.n)) - 1)) & 0xFF
            self.buf.append(b)
            if b == 0xFF:
                self.buf.append(0)
            self.acc = 0
            self.n = 0


def _cat_bits(v):
    """(category, bits) for a coefficient value."""
    if v == 0:
        return 0, 0
    a = v if v > 0 else -v
    cat = a.bit_length()
    bits = v if v > 0 else v + (1 << cat) - 1
    return cat, bits


def encode_jpeg(buf, quality=QUALITY):
    qlum = _scale_quant(QLUM, quality)
    qchr = _scale_quant(QCHR, quality)
    # _fdct outputs exactly 8x the textbook DCT (verified against a naive
    # DCT), uniformly for every coefficient, so quantize by 1/(8*Q).
    flum = [1.0 / (8.0 * qlum[i]) for i in range(64)]
    fchr = [1.0 / (8.0 * qchr[i]) for i in range(64)]
    dc_lum = _huff_codes(*H_DC_LUM)
    dc_chr = _huff_codes(*H_DC_CHR)
    ac_lum = _huff_codes(*H_AC_LUM)
    ac_chr = _huff_codes(*H_AC_CHR)

    out = bytearray(b"\xff\xd8")  # SOI
    # APP0 JFIF
    out += b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    # DQT (quant values are stored in zigzag order in the file)
    out += b"\xff\xdb\x00\x43\x00" + bytes(qlum[ZIGZAG[i]] for i in range(64))
    out += b"\xff\xdb\x00\x43\x01" + bytes(qchr[ZIGZAG[i]] for i in range(64))
    # SOF0 baseline, 3 comps, Y 2x2, Cb/Cr 1x1
    out += (b"\xff\xc0\x00\x11\x08" + H.to_bytes(2, "big") + W.to_bytes(2, "big")
            + b"\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01")
    # DHT x4
    for tc, th, (counts, syms) in ((0, 0, H_DC_LUM), (1, 0, H_AC_LUM),
                                   (0, 1, H_DC_CHR), (1, 1, H_AC_CHR)):
        out += b"\xff\xc4" + (19 + len(syms)).to_bytes(2, "big")
        out += bytes([(tc << 4) | th]) + bytes(counts) + bytes(syms)
    # SOS
    out += (b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00")

    bits = _Bits()
    prev_dc = [0, 0, 0]
    block = [0.0] * 64
    zz = ZIGZAG

    for my in range(0, H, 16):
        for mx in range(0, W, 16):
            # --- luma 4 blocks ---
            for by in (0, 8):
                for bx in (0, 8):
                    for r in range(8):
                        base = ((my + by + r) * W + mx + bx) * 3
                        for c in range(8):
                            i = base + c * 3
                            block[r * 8 + c] = (
                                0.299 * buf[i] + 0.587 * buf[i + 1]
                                + 0.114 * buf[i + 2] - 128.0)
                    _fdct(block)
                    _encode_block(bits, block, flum, dc_lum, ac_lum,
                                  prev_dc, 0, zz)
            # --- chroma 1 block each (2x2 box downsample) ---
            for comp, (kr, kg, kb) in ((1, (-0.168736, -0.331264, 0.5)),
                                       (2, (0.5, -0.418688, -0.081312))):
                ftab = fchr
                for r in range(8):
                    y0 = my + r * 2
                    for c in range(8):
                        x0 = mx + c * 2
                        s = 0.0
                        for dy in (0, 1):
                            base = ((y0 + dy) * W + x0) * 3
                            for dx in (0, 1):
                                i = base + dx * 3
                                s += kr * buf[i] + kg * buf[i + 1] + kb * buf[i + 2]
                        block[r * 8 + c] = s * 0.25
                _fdct(block)
                _encode_block(bits, block, ftab, dc_chr, ac_chr,
                              prev_dc, comp, zz)
    bits.flush()
    out += bits.buf
    out += b"\xff\xd9"  # EOI
    return bytes(out)


def _encode_block(bits, block, ftab, dc_tab, ac_tab, prev_dc, comp, zz):
    coef = [0] * 64
    for i in range(64):
        v = block[i] * ftab[i]
        coef[i] = int(v + 0.5) if v >= 0 else int(v - 0.5)
    zzcoef = [coef[zz[i]] for i in range(64)]
    diff = zzcoef[0] - prev_dc[comp]
    prev_dc[comp] = zzcoef[0]
    cat, val = _cat_bits(diff)
    code, nbits = dc_tab[cat]
    bits.put(code, nbits)
    if cat:
        bits.put(val, cat)
    run = 0
    for k in range(1, 64):
        v = zzcoef[k]
        if v == 0:
            run += 1
            continue
        while run > 15:
            code, nbits = ac_tab[0xF0]
            bits.put(code, nbits)
            run -= 16
        cat, val = _cat_bits(v)
        code, nbits = ac_tab[(run << 4) | cat]
        bits.put(code, nbits)
        bits.put(val, cat)
        run = 0
    if run:
        code, nbits = ac_tab[0x00]
        bits.put(code, nbits)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = encode_jpeg(render())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} {len(data)} bytes")


if __name__ == "__main__":
    main()
