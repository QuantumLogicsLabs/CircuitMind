#!/usr/bin/env python3
"""Generate self-checking vectors for fp_add / fp_sub.

The reference model works on exact rational values (fractions.Fraction) and
rounds to binary32 with round-to-nearest-even.  It is deliberately independent
of NumPy's float32 pipeline so subnormal, tie and overflow cases are checked
against exact arithmetic.

Output line format:  <a:8hex> <b:8hex> <expected:8hex> <flags:1hex>
flags = {invalid, overflow, underflow, inexact}
"""

from fractions import Fraction
from pathlib import Path
import random

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "vectors"

QNAN = 0x7FC00000
INF = 0x7F800000


def decode(bits):
    sign = (bits >> 31) & 1
    exp = (bits >> 23) & 0xFF
    frac = bits & 0x7FFFFF
    if exp == 0xFF:
        return ("nan" if frac else "inf"), sign, None
    if exp == 0:
        value = Fraction(frac, 1 << 149)
        return "finite", sign, -value if sign else value
    m = (1 << 23) + frac
    shift = exp - 150
    if shift >= 0:
        value = Fraction(m << shift, 1)
    else:
        value = Fraction(m, 1 << (-shift))
    return "finite", sign, -value if sign else value


def is_snan(bits):
    return ((bits >> 23) & 0xFF) == 0xFF and (bits & 0x7FFFFF) != 0 \
        and not ((bits >> 22) & 1)


def floor_log2(v):
    n, d = v.numerator, v.denominator
    e = n.bit_length() - d.bit_length()
    if e >= 0:
        if v < (1 << e):
            e -= 1
    else:
        if v < Fraction(1, 1 << (-e)):
            e -= 1
    return e


def rne(x):
    """Round a non-negative Fraction to the nearest integer, ties to even."""
    whole = x.numerator // x.denominator
    rem = x - whole
    if rem > Fraction(1, 2):
        return whole + 1
    if rem < Fraction(1, 2):
        return whole
    return whole if whole % 2 == 0 else whole + 1


def scale_pow2(x, k):
    if k >= 0:
        return Fraction(x.numerator << k, x.denominator)
    return Fraction(x.numerator, x.denominator << (-k))


def round_f32(value):
    """Round an exact Fraction to binary32. Returns (bits, flags)."""
    sign = 1 if value < 0 else 0
    v = -value if sign else value
    e = floor_log2(v)

    if e < -126:
        scaled = scale_pow2(v, 149)
        frac = rne(scaled)
        inexact = scaled.denominator != 1
        if frac >= (1 << 23):
            # Rounded up to the smallest normal.
            return sign << 31 | (1 << 23) | 0, (0, 0, 0, int(inexact))
        bits = sign << 31 | frac
        underflow = 1 if inexact else 0
        return bits, (0, 0, underflow, int(inexact))

    scaled = scale_pow2(v, 23 - e)
    mant = rne(scaled)
    inexact = scaled.denominator != 1
    if mant == (1 << 24):
        mant >>= 1
        e += 1
    if e > 127:
        return sign << 31 | INF, (0, 1, 0, 1)

    field = e + 127
    frac = mant - (1 << 23)
    return sign << 31 | (field << 23) | frac, (0, 0, 0, int(inexact))


def ref_add(ab, bb, sub=False):
    kind_a, sign_a, val_a = decode(ab)
    kind_b, sign_b, val_b = decode(bb)
    if sub:
        sign_b ^= 1
        if val_b is not None:
            val_b = -val_b

    if kind_a == "nan" or kind_b == "nan":
        return QNAN, (int(is_snan(ab) or is_snan(bb)), 0, 0, 0)

    if kind_a == "inf" and kind_b == "inf":
        if sign_a != sign_b:
            return QNAN, (1, 0, 0, 0)
        return (sign_a << 31) | INF, (0, 0, 0, 0)

    if kind_a == "inf":
        return (sign_a << 31) | INF, (0, 0, 0, 0)
    if kind_b == "inf":
        return (sign_b << 31) | INF, (0, 0, 0, 0)

    exact = val_a + val_b
    if exact == 0:
        neg_zero = 1 if (val_a == 0 and val_b == 0 and sign_a and sign_b) else 0
        return neg_zero << 31, (0, 0, 0, 0)

    bits, flags = round_f32(exact)
    return bits, flags


DIRECTED = [
    0x00000000, 0x80000000,              # +0, -0
    0x00000001, 0x80000001,              # min subnormal
    0x007FFFFF, 0x807FFFFF,              # max subnormal
    0x00800000, 0x80800000,              # min normal
    0x3F800000, 0xBF800000,              # +/-1.0
    0x3F800001, 0xBF7FFFFF,              # 1.0+ulp, -(1.0-ulp)
    0x3FC00000, 0x40000000, 0x40400000,  # 1.5, 2.0, 3.0
    0x3F000000, 0x3F000001,              # 0.5
    0x33800000, 0x33C00000,              # 2^-24, 3*2^-24
    0x7F7FFFFF, 0xFF7FFFFF,              # max finite
    0x7F800000, 0xFF800000,              # +/-inf
    0x7FC00000, 0x7F800001,              # qNaN, sNaN
    0x40490FDB, 0xC0490FDB,              # +/-pi
]


def build_pairs():
    pairs = set()

    for a in DIRECTED:
        for b in DIRECTED:
            pairs.add((a, b))

    extra = [
        (0x3F800000, 0x33800000),   # 1.0 + 2^-24: tie
        (0x3F800000, 0x33C00000),   # 1.0 + 3*2^-24: tie
        (0x3F800001, 0x33800000),   # tie with odd LSB
        (0xBF800000, 0x33800000),
        (0x40400000, 0x3B800000),   # 2.0 + 2^-40
        (0x00800000, 0x807FFFFF),   # min normal - max subnormal
        (0x007FFFFF, 0x00000001),   # subnormal carry into normal
        (0x7F7FFFFF, 0x7F7FFFFF),   # overflow
        (0xFF7FFFFF, 0x7F7FFFFF),   # cancellation of max finite
        (0x00000001, 0x80000001),   # subnormal cancellation
        (0x3F800000, 0xBF7FFFFF),   # normal cancellation to 1 ulp
        (0x7F7FFFFF, 0x73800000),   # huge + tiny (sticky)
    ]
    pairs.update(extra)

    rng = random.Random(20261111)

    for _ in range(2000):
        pairs.add((rng.getrandbits(32), rng.getrandbits(32)))

    def rand_normal(rng):
        sign = rng.getrandbits(1)
        exp = rng.randint(1, 254)
        frac = rng.getrandbits(23)
        return (sign << 31) | (exp << 23) | frac

    for _ in range(2500):
        a = rand_normal(rng)
        ea = (a >> 23) & 0xFF
        eb = min(254, max(1, ea + rng.randint(-4, 4)))
        b = (rng.getrandbits(1) << 31) | (eb << 23) | rng.getrandbits(23)
        pairs.add((a, b))

    for _ in range(1200):
        def rand_subnormal(rng):
            return (rng.getrandbits(1) << 31) | rng.randint(0, 0x7FFFFF)
        pairs.add((rand_subnormal(rng), rand_subnormal(rng)))

    for _ in range(1200):
        a = rand_normal(rng)
        ea = (a >> 23) & 0xFF
        eb = min(254, max(1, ea + rng.randint(20, 60)))
        b = (rng.getrandbits(1) << 31) | (eb << 23) | rng.getrandbits(23)
        pairs.add((a, b))

    return sorted(pairs)


def write_vectors(path, pairs, sub):
    lines = []
    for a, b in pairs:
        y, flags = ref_add(a, b, sub)
        f = (flags[0] << 3) | (flags[1] << 2) | (flags[2] << 1) | flags[3]
        lines.append(f"{a:08x} {b:08x} {y:08x} {f:x}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return len(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = build_pairs()
    n_add = write_vectors(OUT / "add_vectors.txt", pairs, False)
    n_sub = write_vectors(OUT / "sub_vectors.txt", pairs, True)
    print(f"add_vectors.txt: {n_add} vectors")
    print(f"sub_vectors.txt: {n_sub} vectors")


if __name__ == "__main__":
    main()
