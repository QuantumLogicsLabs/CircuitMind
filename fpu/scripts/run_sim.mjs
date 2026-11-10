// Runs the FPU testbenches with the WASM build of Icarus Verilog, so no native
// simulator install is required.  Usage: node scripts/run_sim.mjs [add|top]
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { simulate } from '@veriflow/iverilog-wasm';

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

const SUITES = {
  add: { top: 'tb_fp_add', tb: 'tb/tb_fp_add.v' },
  top: { top: 'tb_fpu_top', tb: 'tb/tb_fpu_top.v' },
};

const wanted = process.argv[2];
if (wanted && !SUITES[wanted]) {
  console.error(`unknown suite "${wanted}" (use add or top)`);
  process.exit(2);
}

let failures = 0;

for (const [name, suite] of Object.entries(SUITES)) {
  if (wanted && wanted !== name) continue;

  const files = [];
  for (const rel of [...RTL, suite.tb]) {
    files.push({ path: rel, data: await readFile(path.join(FPU, rel), 'utf8') });
  }
  for (const vec of ['add_vectors.txt', 'sub_vectors.txt']) {
    files.push({
      path: vec,
      data: await readFile(path.join(FPU, 'vectors', vec), 'utf8'),
    });
  }

  const result = await simulate({
    files,
    sources: [...RTL, suite.tb],
    top: suite.top,
    generation: '2005',
    timeoutMs: 120000,
  });

  const pass =
    result.success &&
    result.stdout.includes('RESULT: PASS') &&
    !result.stdout.includes('MISMATCH');

  console.log(`\n=== ${name} (${suite.top}) ===`);
  if (result.stdout.trim()) console.log(result.stdout.trim());
  if (result.stderr.trim()) console.error(result.stderr.trim());

  if (!pass) failures += 1;
}

if (failures) {
  console.error(`\n${failures} suite(s) failed`);
  process.exit(1);
}
console.log('\nAll suites passed');
