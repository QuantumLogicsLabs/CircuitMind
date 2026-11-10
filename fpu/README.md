# FPU — Integration Lead deliverable

32-bit IEEE-754 single-precision floating-point unit in Verilog-2001.

This folder is the **Member 1 (Integration Lead)** slice of the FPU project:
the floating-point addition datapath plus the integrated top level. Member 2's
multiplier and divider plug into the sockets in `rtl/stubs/`.

## Task → module map

| Project task | File |
|---|---|
| Floating-Point Addition | `rtl/fp_add.v` |
| Exponent Comparison ("Exposition Comparison") | `rtl/fp_compare_mag.v` |
| Mantissa Alignment | `rtl/fp_align.v` |
| Addition Circuit | `rtl/fp_addsub_core.v` |
| Normalization | `rtl/fp_normalize.v` |
| FPU Integration | `rtl/fpu_top.v` |
| Control Logic & Final Testing | special-case control in `rtl/fp_add.v`, `rtl/fpu_control.v`, `tb/`, `vectors/`, `scripts/` |

## Design

Combinational, single-cycle; no clock or pipeline registers. Addition and
subtraction share one datapath (`sub` flips the sign of `b`).

```
a,b ──► unpack ──► special-case control ──► compare magnitudes
                         │                        │
                         │                        ▼
                         │                  align smaller mantissa
                         │                  (guard / round / sticky)
                         │                        │
                         │                        ▼
                         │                  significand add / sub
                         │                        │
                         │                        ▼
                         │                  normalize + round-to-nearest-even
                         ▼                        ▼
                    NaN / Inf / ±0            pack + exception flags
                         └──────────► result ◄───┘
```

Details that matter:

- Subnormals use effective exponent 1 and a zero hidden bit; normals use the
  stored exponent and a one hidden bit.
- The sticky bit is kept **outside** the arithmetic value. Alignment truncates
  the smaller operand, and `fp_addsub_core` subtracts one extra LSB on
  subtraction to compensate for the truncated remainder. This keeps a single
  rounding step correct.
- Normalization handles three cases: significand carry, leading-zero
  cancellation, and clamping at the subnormal boundary.
- Rounding is round-to-nearest-even only. Underflow is flagged when the packed
  result is subnormal/zero and the rounding was inexact.
- Special cases: quiet/signaling NaN, ±Inf, ±0, Inf−Inf and 0×∞-style invalid
  operation for add/sub. NaN results are canonicalized to `0x7FC00000`.

## Interfaces

```verilog
fp_add(a[31:0], b[31:0], sub) -> result, invalid, overflow, underflow, inexact

fpu_top(op[1:0], a[31:0], b[31:0])
    -> result, invalid, overflow, underflow, inexact, stub_active

// op: 00 ADD, 01 SUB, 10 MUL, 11 DIV
```

### Member 2 sockets

`rtl/stubs/fp_mul_stub.v` and `rtl/stubs/fp_div_stub.v` implement the exact port
list the real modules must provide:

```verilog
fp_mul(a, b) -> result, invalid, overflow, underflow, inexact
fp_div(a, b) -> result, invalid, overflow, underflow, inexact
```

Both stubs return a canonical NaN and assert `stub_active`, which `fpu_top`
exposes at its output. Replace `u_mul`/`u_div` with the real modules when they
land; no other wiring changes are needed. Divide-by-zero is not part of the
integrated flag set yet; add it together with the divider.

## Verification

`scripts/gen_vectors.py` is an exact reference model: finite operands are
decoded to `fractions.Fraction`, added/subtracted exactly, and rounded to
binary32 with round-to-nearest-even. It is independent of the RTL and of
NumPy's float32 pipeline. Expected IEEE flags are part of every vector.

Coverage in the committed vector set (7,631 operand pairs, run for add and
sub):

- all pairs of ±0, ±min/max subnormal, ±min normal, ±1, ±max finite, ±Inf,
  qNaN, sNaN, π;
- rounding ties (`1.0 + 2^-24`, odd-LSB ties), overflow, cancellation to zero,
  cancellation to subnormal, subnormal→normal carry;
- random full-pattern pairs, close-exponent pairs, subnormal pairs, large
  exponent-difference pairs.

Results:

| Suite | Checks | Result |
|---|---|---|
| `tb_fp_add` (add + sub) | 15,262 | PASS |
| `tb_fpu_top` (op decode + add/sub + stub sockets) | 15,264 | PASS |
| additional 60,000-pair soak (not committed) | 120,000 | PASS |

## Run the tests

The simulation uses the WebAssembly build of Icarus Verilog, so no native
simulator install is needed:

```bash
cd fpu
npm install
npm test
```

Vectors are committed, but can be regenerated with Python 3 (standard library
only):

```bash
python scripts/gen_vectors.py
```

With a native Icarus Verilog install:

```bash
iverilog -g2005 -o fpu_sim.vvp rtl/*.v rtl/stubs/*.v tb/tb_fp_add.v
cd vectors && vvp ../fpu_sim.vvp
```

## Limitations

- Combinational only; no pipeline, clock, or ready/valid handshake.
- One rounding mode (RNE); no rounding-mode input.
- NaN payloads are not propagated; every NaN result is `0x7FC00000`.
- MUL/DIV are integration stubs until Member 2's modules replace them.
