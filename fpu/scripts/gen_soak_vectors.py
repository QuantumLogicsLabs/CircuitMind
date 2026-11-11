#!/usr/bin/env python3
"""Generate randomized add/sub vectors for the FPU soak test.

The vectors use the exact reference model in gen_vectors.py, so every expected
result and flag is checked against rational arithmetic rather than a second
floating-point implementation.
"""

import argparse
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    import gen_vectors as gv
except ImportError as exc:
    sys.exit(f"gen_vectors.py is required (it ships with the FPU sources): {exc}")


def rand_normal(rng):
    sign = rng.getrandbits(1)
    exp = rng.randint(1, 254)
    frac = rng.getrandbits(23)
    return (sign << 31) | (exp << 23) | frac


def rand_subnormal(rng):
    return (rng.getrandbits(1) << 31) | rng.randint(0, 0x7FFFFF)


def build_soak_pairs(count, seed):
    rng = random.Random(seed)
    pairs = set()

    while len(pairs) < count:
        mode = rng.random()
        if mode < 0.35:
            # Unrestricted bit patterns: NaNs, infinities, zeros, subnormals.
            a, b = rng.getrandbits(32), rng.getrandbits(32)
        elif mode < 0.65:
            # Normal operands with nearby exponents.
            a = rand_normal(rng)
            ea = (a >> 23) & 0xFF
            eb = min(254, max(1, ea + rng.randint(-4, 4)))
            b = (rng.getrandbits(1) << 31) | (eb << 23) | rng.getrandbits(23)
        elif mode < 0.82:
            # Subnormal operands.
            a, b = rand_subnormal(rng), rand_subnormal(rng)
        else:
            # Large exponent difference: exercises alignment, guard and sticky.
            a = rand_normal(rng)
            ea = (a >> 23) & 0xFF
            eb = min(254, max(1, ea + rng.randint(20, 80)))
            b = (rng.getrandbits(1) << 31) | (eb << 23) | rng.getrandbits(23)

        pairs.add((a, b))

    return sorted(pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261112)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    if args.pairs < 1:
        parser.error("--pairs must be at least 1")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    pairs = build_soak_pairs(args.pairs, args.seed)
    n_add = gv.write_vectors(out / "add_vectors.txt", pairs, False)
    n_sub = gv.write_vectors(out / "sub_vectors.txt", pairs, True)

    print(f"soak pairs: {len(pairs)} (seed {args.seed})")
    print(f"add_vectors.txt: {n_add} vectors")
    print(f"sub_vectors.txt: {n_sub} vectors")


if __name__ == "__main__":
    main()
