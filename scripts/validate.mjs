import assert from 'node:assert/strict';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = path => readFileSync(join(root, path), 'utf8');
const json = path => JSON.parse(read(path));
const catalog = json('marketplace.json');
const aliases = ['.github/plugin/marketplace.json', '.claude-plugin/marketplace.json'];
assert(process.argv.slice(2).every(arg => arg === '--sync'), 'Only --sync is supported');

if (process.argv.includes('--sync')) {
  for (const path of aliases) {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), `${JSON.stringify(catalog, null, 2)}\n`);
  }
}

for (const path of aliases) {
  assert.deepEqual(json(path), catalog, `${path} differs from the root catalog`);
}

const namePattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
assert(namePattern.test(catalog.name), 'Invalid marketplace name');
assert(typeof catalog.owner?.name === 'string' && catalog.owner.name.trim(), 'Missing owner');
assert(Array.isArray(catalog.plugins) && catalog.plugins.length > 0, 'Missing plugins');
const names = new Set();

for (const entry of catalog.plugins) {
  assert(namePattern.test(entry.name) && !names.has(entry.name), `Invalid/duplicate plugin: ${entry.name}`);
  names.add(entry.name);
  assert(typeof entry.source === 'string' && entry.source.startsWith('./plugins/'), 'Expected a local plugin source');
  assert(!entry.source.split(/[\\/]/).includes('..'), 'Plugin source must not escape the repository');
  const pluginRoot = resolve(root, entry.source);
  assert(existsSync(pluginRoot), `Missing source: ${entry.source}`);
  const portable = JSON.parse(readFileSync(join(pluginRoot, 'plugin.json'), 'utf8'));
  const claude = JSON.parse(readFileSync(join(pluginRoot, '.claude-plugin', 'plugin.json'), 'utf8'));
  assert.equal(portable.$schema, 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json');
  const { $schema, ...shared } = portable;
  assert.deepEqual(claude, shared, `${entry.name}: plugin manifests differ`);
  for (const field of ['name', 'version', 'description']) {
    assert(typeof entry[field] === 'string' && entry[field].trim(), `${entry.name}: missing ${field}`);
    assert.equal(portable[field], entry[field], `${entry.name}: mismatched ${field}`);
  }
  assert(/^\d+\.\d+\.\d+$/.test(entry.version), `${entry.name}: invalid version`);
  assert.equal(portable.repository, 'https://github.com/josverl/mp-agents');
  assert.equal(portable.license, 'MIT');
  for (const file of ['README.md', 'CHANGELOG.md']) {
    assert(existsSync(join(pluginRoot, file)), `${entry.name}: missing ${file}`);
  }
  assert(readFileSync(join(pluginRoot, 'CHANGELOG.md'), 'utf8').includes(`## ${entry.version}`));
  const skillsRoot = join(pluginRoot, 'skills');
  const skills = readdirSync(skillsRoot, { withFileTypes: true }).filter(item => item.isDirectory());
  assert(skills.length > 0, `${entry.name}: missing skills`);
  for (const skill of skills) {
    const text = readFileSync(join(skillsRoot, skill.name, 'SKILL.md'), 'utf8');
    const frontmatter = text.match(/^---\r?\nname: ([a-z0-9-]+)\r?\ndescription: ([^\r\n]+)\r?\n---\r?\n/);
    assert(frontmatter && frontmatter[1] === skill.name && namePattern.test(skill.name), `Invalid skill: ${skill.name}`);
    assert(frontmatter[2].trim().length <= 1024, `${skill.name}: description too long`);
    assert.equal((text.match(/^```/gm) || []).length % 2, 0, `${skill.name}: unbalanced fences`);
    for (const match of text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1];
      if (/^https?:\/\//.test(target) || target.startsWith('#')) continue;
      const path = target.split('#')[0];
      assert(!isAbsolute(path), `${skill.name}: absolute resource link`);
      const resolved = resolve(skillsRoot, skill.name, path);
      const withinPlugin = relative(pluginRoot, resolved);
      assert(!withinPlugin.startsWith('..') && !isAbsolute(withinPlugin), `${skill.name}: resource escapes plugin`);
      assert(existsSync(resolved), `${skill.name}: missing resource ${path}`);
    }
  }
}

console.log(`Validated ${catalog.plugins.length} plugin(s), three catalogs, manifests, and skills.`);
