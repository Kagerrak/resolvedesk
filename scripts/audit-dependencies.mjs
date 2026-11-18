// Temporary, advisory-specific development exception approved 2026-11-18.
// Production vulnerabilities and every other moderate-or-higher advisory fail.
import { spawnSync } from 'node:child_process';
const allowed = 'https://github.com/advisories/GHSA-fc5q-39xc-vjpf';
const expires = Date.parse('2026-12-02T00:00:00Z');
function audit(args) {
  const result = spawnSync('npm', ['audit', '--json', '--fetch-timeout=30000', '--fetch-retries=0', ...args], { encoding: 'utf8', timeout: 45000 });
  if (result.error || ![0, 1].includes(result.status)) throw new Error('Dependency audit could not complete.');
  const report = JSON.parse(result.stdout);
  if (report.error || !report.vulnerabilities || !report.metadata) throw new Error('Invalid dependency audit report.');
  return report.vulnerabilities;
}
try {
  const production = audit(['--omit=dev']);
  const significant = new Set(['moderate', 'high', 'critical']);
  if (Object.values(production).some(v => significant.has(v.severity))) throw new Error('Production dependency advisory requires remediation.');
  const all = audit([]);
  const accepted = new Set();
  function permitted(name, visiting = new Set()) {
    const entry = all[name];
    if (!entry || visiting.has(name) || !entry.via?.length) return false;
    const next = new Set(visiting).add(name);
    return entry.via.every(v => typeof v === 'string' ? permitted(v, next) : v.url === allowed && v.name === 'picomatch');
  }
  for (const [name, entry] of Object.entries(all)) {
    if (!significant.has(entry.severity)) continue;
    if (Date.now() >= expires || !permitted(name)) throw new Error(`Unexcepted or expired dependency advisory: ${name}`);
    accepted.add(name);
  }
  console.log(`Production audit passed. ${accepted.size} development dependency findings covered by the single temporary advisory exception (expires 2026-12-02).`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
