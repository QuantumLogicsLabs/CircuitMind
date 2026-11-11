// Randomized FPU soak test. Generates fresh vectors with the exact reference
// model, runs them through tb_fp_add on the WASM build of Icarus Verilog, and
// records the result in vectors/soak_results.txt.
//
// Usage: node scripts/soak.mjs [--pairs N] [--seed S]
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FPU = path.resolve(HERE, '..');

const RTL = [
  'rtl/fp_compare_mag.v',
  'rtl/fp_align.v',
  'rtl/fp_addsub_core.v',
  'rtl/fp_normalize.v',
  'rtl/fp_add.v',
  'rtl/fpu_control.v',
  'rtl/stubs/fp_mul_stub.v',
  'rtl/stubs/fp_div_stub.v',
  'rtl/fpu_top.v',
];

function parseArgs(argv) {
  let pairs = 20000;
  let seed = 20261112;

  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--pairs') pairs = Number(argv[++i]);
    else if (argv[i] === '--seed') seed = Number(argv[++i]);
    else if (argv[i] === '--help' || argv[i] === '-h') {
      console.log('usage: node scripts/soak.mjs [--pairs N] [--seed S]');
      process.exit(0);
    } else {
      console.error(`unknown argument: ${argv[i]}`);
      process.exit(2);
    }
  }

  if (!Number.isInteger(pairs) || pairs < 1) {
    console.error('--pairs must be a positive integer');
    process.exit(2);
  }
  if (!Number.isSafeInteger(seed)) {
    console.error('--seed must be an integer');
    process.exit(2);
  }
  return { pairs, seed };
}

const { pairs, seed } = parseArgs(process.argv.slice(2));

const REQUIRED = [
  'package.json',
  'scripts/gen_vectors.py',
  'scripts/gen_soak_vectors.py',
  'rtl/fpu_top.v',
  'tb/tb_fp_add.v',
];
for (const rel of REQUIRED) {
  try {
    await readFile(path.join(FPU, rel));
  } catch {
    console.error(`missing ${rel}; the FPU sources must be present first`);
    process.exit(2);
  }
}

const { simulate } = await import('@veriflow/iverilog-wasm');

const tmp = await mkdtemp(path.join(tmpdir(), 'fpu-soak-'));
try {
  const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  const gen = spawnSync(
    python,
    [
      'scripts/gen_soak_vectors.py',
      '--pairs', String(pairs),
      '--seed', String(seed),
      '--out-dir', tmp,
    ],
    { cwd: FPU, stdio: 'inherit' },
  );
  if (gen.status !== 0) {
    console.error(`vector generation failed (exit ${gen.status})`);
    process.exit(1);
  }

  const files = [];
  for (const rel of [...RTL, 'tb/tb_fp_add.v']) {
    files.push({ path: rel, data: await readFile(path.join(FPU, rel), 'utf8') });
  }
  for (const name of ['add_vectors.txt', 'sub_vectors.txt']) {
    files.push({ path: name, data: await readFile(path.join(tmp, name), 'utf8') });
  }

  const result = await simulate({
    files,
    sources: [...RTL, 'tb/tb_fp_add.v'],
    top: 'tb_fp_add',
    generation: '2005',
    timeoutMs: 600000,
  });

  if (result.stdout.trim()) console.log(result.stdout.trim());
  if (result.stderr.trim()) console.error(result.stderr.trim());

  const match = result.stdout.match(/RESULT: PASS \((\d+) vectors\)/);
  const pass = result.success && Boolean(match) && !result.stdout.includes('MISMATCH');
  const vectors = match ? Number(match[1]) : 0;

  const summary = [
    'FPU soak test',
    `date_utc: ${new Date().toISOString()}`,
    `seed: ${seed}`,
    `pairs: ${pairs}`,
    `vectors: ${vectors}`,
    `result: ${pass ? 'PASS' : 'FAIL'}`,
    'simulator: @veriflow/iverilog-wasm (Icarus Verilog, generation 2005)',
    `node: ${process.version}`,
    '',
  ].join('\n');

  await writeFile(path.join(FPU, 'vectors', 'soak_results.txt'), summary, 'utf8');
  console.log(`\n${summary}`);

  if (!pass) process.exitCode = 1;
} finally {
  await rm(tmp, { recursive: true, force: true });
}
