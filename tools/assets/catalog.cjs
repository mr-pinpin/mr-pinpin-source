#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const DEFAULT_ROOT = path.resolve(__dirname, '../..');
const skipped = name => name === '__pycache__' || name === '.DS_Store' || /^backups?$/i.test(name) ||
  /(?:\.py[co]|\.blend\d+|\.bak|\.backup|\.part|~)$/i.test(name);

function logical(value) {
  if (typeof value !== 'string' || !value.startsWith('docs/') ||
      value.includes('\\') || /[\x00-\x1f\x7f]/.test(value) ||
      path.posix.normalize(value) !== value || value.endsWith('/')) {
    throw new Error(`Unsafe asset path: ${value}`);
  }
  return value;
}

function objectKey(digest, filename) {
  return `sha256/${digest.slice(0, 2)}/${digest}/${path.posix.basename(filename)}`;
}

function validateManifest(manifest, bucket) {
  if (manifest.version !== 1 || manifest.bucket !== bucket || !Array.isArray(manifest.assets)) {
    throw new Error('Manifest version, bucket, or assets mismatch');
  }
  const seen = new Set();
  for (const entry of manifest.assets) {
    logical(entry.path);
    if (seen.has(entry.path) || !['production', 'archive'].includes(entry.role) ||
        !Number.isSafeInteger(entry.bytes) || entry.bytes < 0 ||
        !/^[a-f0-9]{64}$/.test(entry.sha256) ||
        entry.object !== objectKey(entry.sha256, entry.path)) {
      throw new Error(`Invalid manifest entry: ${entry.path}`);
    }
    seen.add(entry.path);
  }
  return manifest;
}

function readJson(filename) {
  return JSON.parse(fs.readFileSync(filename, 'utf8'));
}

function inventory(root, policy, previous) {
  const assets = new Map();
  const managed = new Set(policy.managedSymlinks || []);
  const extensions = new Set(policy.extensions);
  let nonAssetBytes = 0;
  let nonAssetFiles = 0;
  const archived = previous.assets.filter(e => e.role === 'archive');
  function walk(relative, ancestors = new Set()) {
    const filename = path.join(root, relative);
    let stat = fs.lstatSync(filename);
    if (stat.isSymbolicLink()) {
      if (!managed.has(relative)) throw new Error(`Unmanaged symlink: ${relative}`);
      try { stat = fs.statSync(filename); } catch (error) {
        if (error.code === 'ENOENT' && archived.some(e => e.path === relative || e.path.startsWith(relative + '/'))) return;
        throw new Error(`Broken managed symlink without archived manifest: ${relative}`);
      }
    }
    if (stat.isDirectory()) {
      const real = fs.realpathSync(filename);
      if (ancestors.has(real)) throw new Error(`Symlink cycle: ${relative}`);
      const next = new Set([...ancestors, real]);
      for (const name of fs.readdirSync(filename).sort()) {
        if (!skipped(name)) walk(path.posix.join(relative, name), next);
      }
    } else if (stat.isFile()) {
      if (extensions.has(path.extname(relative).toLowerCase())) {
        assets.set(logical(relative), {filename, bytes: stat.size});
      } else {
        nonAssetBytes += stat.size;
        nonAssetFiles++;
      }
    } else throw new Error(`Unsupported filesystem entry: ${relative}`);
  }
  for (const directory of policy.roots) {
    if (directory !== 'docs') throw new Error(`Unsupported asset root: ${directory}`);
    walk(directory);
  }
  return {assets, nonAssetBytes, nonAssetFiles};
}

function* strings(value, preferRuntimeSrc = false) {
  if (typeof value === 'string') yield value;
  else if (Array.isArray(value)) {
    for (const item of value) yield* strings(item, preferRuntimeSrc);
  } else if (value && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) {
      if (preferRuntimeSrc && key === 'src' && typeof value.runtimeSrc === 'string' && value.runtimeSrc.trim()) continue;
      yield key;
      yield* strings(item, preferRuntimeSrc);
    }
  }
}

function productionClosure(root, policy, known) {
  const production = new Set(policy.production.map(logical));
  const seeds = [...(policy.manifestSeeds || [])];
  for (const directory of policy.manifestDirectories || []) {
    logical(directory);
    for (const name of fs.readdirSync(path.join(root, directory)).sort()) {
      if (name.endsWith('.json')) seeds.push({path: path.posix.join(directory, name)});
    }
  }
  for (const seed of seeds) {
    logical(seed.path);
    let data = readJson(path.join(root, seed.path));
    for (const key of seed.select || []) {
      if (!data || !Object.hasOwn(data, key)) throw new Error(`Missing manifest selector: ${seed.path}:${key}`);
      data = data[key];
    }
    for (const value of strings(data, seed.preferRuntimeSrc === true)) {
      if (/^(?:[a-z][\w+.-]*:|\/\/)/i.test(value) || value.includes('${')) continue;
      const clean = value.split(/[?#]/)[0];
      if (!policy.extensions.includes(path.posix.extname(clean).toLowerCase())) continue;
      const candidates = [path.posix.dirname(seed.path), ...(policy.resolutionBases || []), '']
        .map(base => path.posix.normalize(path.posix.join(base, clean)));
      const match = candidates.find(candidate => known.has(candidate));
      if (match) production.add(match);
      else {
        throw new Error(`Missing manifest asset: ${seed.path}: ${value}`);
      }
    }
  }
  return production;
}

async function digestFile(filename, expectedBytes) {
  const before = fs.statSync(filename);
  const hash = crypto.createHash('sha256');
  let bytes = 0;
  for await (const chunk of fs.createReadStream(filename)) {
    bytes += chunk.length;
    hash.update(chunk);
  }
  const after = fs.statSync(filename);
  if (bytes !== expectedBytes || before.size !== after.size || before.mtimeMs !== after.mtimeMs ||
      before.ino !== after.ino) throw new Error(`Asset changed during hashing: ${filename}`);
  return hash.digest('hex');
}

async function buildCatalog(root, policy, previous = {version: 1, bucket: policy.bucket, assets: []}) {
  if (policy.version !== 1 || !/^[\w.-]+\/[\w.-]+$/.test(policy.bucket)) throw new Error('Invalid policy');
  if (policy.unreferencedRole !== undefined && policy.unreferencedRole !== 'archive') throw new Error('Invalid unreferencedRole policy');
  validateManifest(previous, policy.bucket);
  const files = inventory(root, policy, previous);
  const prior = new Map(previous.assets.map(entry => [entry.path, entry]));
  const known = new Set([...files.assets.keys(), ...prior.keys()]);
  const production = productionClosure(root, policy, known);
  const archive = new Set(policy.archive.map(logical));
  // Explicit production and archive policy overlap is a configuration error. A new
  // manifest reference may legitimately promote an older archive to production.
  for (const filename of policy.production) {
    if (archive.has(filename)) throw new Error(`Conflicting policy roles: ${filename}`);
  }
  const unknown = [...files.assets.keys()].filter(p => !production.has(p) && !archive.has(p));
  if (unknown.length && policy.unreferencedRole !== 'archive') throw new Error(`Unclassified assets (${unknown.length}); update assets/policy.json:\n${unknown.join('\n')}`);
  for (const filename of production) {
    if (!files.assets.has(filename)) throw new Error(`Missing production asset: ${filename}`);
  }
  for (const filename of archive) {
    if (!files.assets.has(filename) && prior.get(filename)?.role !== 'archive') {
      throw new Error(`Missing archive without prior identity: ${filename}`);
    }
  }
  const entries = [];
  const retained = [];
  for (const filename of [...known].sort()) {
    const file = files.assets.get(filename);
    const old = prior.get(filename);
    if (!file) {
      if (old.role !== 'archive') throw new Error(`Missing production asset: ${filename}`);
      entries.push(old);
      retained.push(filename);
      continue;
    }
    const sha256 = await digestFile(file.filename, file.bytes);
    entries.push({path: filename, role: production.has(filename) ? 'production' : 'archive',
      bytes: file.bytes, sha256, object: objectKey(sha256, filename)});
  }
  const manifest = {version: 1, bucket: policy.bucket, assets: entries};
  const summary = {production: {files: 0, bytes: 0}, archive: {files: 0, bytes: 0},
    retainedMissingArchiveFiles: retained.length, nonAssetFiles: files.nonAssetFiles,
    nonAssetBytes: files.nonAssetBytes};
  for (const entry of entries) {
    summary[entry.role].files++;
    summary[entry.role].bytes += entry.bytes;
  }
  summary.projectedPagesBytes = summary.production.bytes + files.nonAssetBytes;
  return {manifest, summary, retained};
}

function archiveIgnore(manifest) {
  const escape = value => value.replace(/[\\*?\[\]#! ]/g, '\\$&');
  return '# Generated by tools/assets/catalog.cjs; do not edit.\n' +
    '# Proposal only: apply after SHA-256-verified HF receipts.\n' +
    '# Paths are anchored to the repository root, not this assets/ directory.\n' +
    manifest.assets.filter(e => e.role === 'archive').map(e => '/' + escape(e.path)).join('\n') + '\n';
}

function receiptPlan(manifest) {
  return {version: 1, bucket: manifest.bucket, verificationRequired: true,
    assets: manifest.assets.filter(entry => entry.role === 'archive')};
}

async function main(argv = process.argv.slice(2)) {
  const options = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--check') options.check = true;
    else if (['--root', '--policy', '--manifest', '--ignore', '--receipt-plan'].includes(arg) && argv[i + 1] && !argv[i + 1].startsWith('--')) {
      options[arg.slice(2)] = argv[++i];
    } else throw new Error(`Unknown or incomplete option: ${arg}`);
  }
  const root = path.resolve(options.root || DEFAULT_ROOT);
  const output = name => path.resolve(root, options[name] || `assets/${name === 'ignore' ? 'archive.gitignore' : name + '.json'}`);
  const policy = readJson(output('policy'));
  const previous = fs.existsSync(output('manifest')) ? readJson(output('manifest')) : undefined;
  const result = await buildCatalog(root, policy, previous);
  const outputs = [[output('manifest'), JSON.stringify(result.manifest, null, 2) + '\n'],
    [output('ignore'), archiveIgnore(result.manifest)]];
  if (options['receipt-plan']) outputs.push([path.resolve(root, options['receipt-plan']), JSON.stringify(receiptPlan(result.manifest), null, 2) + '\n']);
  for (const [filename, content] of outputs) {
    if (options.check) {
      if (!fs.existsSync(filename) || fs.readFileSync(filename, 'utf8') !== content) throw new Error(`Generated file is stale: ${filename}`);
    } else {
      fs.mkdirSync(path.dirname(filename), {recursive: true});
      fs.writeFileSync(filename, content);
    }
  }
  console.log(JSON.stringify(result.summary, null, 2));
}

module.exports = {buildCatalog, archiveIgnore, receiptPlan, validateManifest, objectKey, main};
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 1; });
