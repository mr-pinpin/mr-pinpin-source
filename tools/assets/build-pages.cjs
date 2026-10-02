#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {parseArgs} = require('node:util');
const {parse} = require('parse5');
const acorn = require('acorn');
const walk = require('acorn-walk');
const postcss = require('postcss');
const valueParser = require('postcss-value-parser');
const parseSrcset = require('parse-srcset');

const BUDGET = 950000000;
const EXCLUDED = ['docs/comparison', 'docs/storyboard/review', 'docs/storyboard/models', 'docs/storyboard/production',
  ...require('./review-entrypoints.json').paths];
const STATIC = new Set(['.html','.css','.js','.mjs','.cjs','.json','.txt','.md','.xml','.webmanifest','.wgsl','.license','.map']);
const URL_EXT = /\.(?:html?|css|[cm]?js|json|png|jpe?g|webp|avif|gif|svg|ico|mp4|webm|mp3|wav|ogg|glb|bin(?:\.gz)?|wgsl|woff2?|ttf|otf)(?:[?#].*)?$/i;
const METADATA = new Set(['generationReview','rejectedRoutePlanSource','routeSurveySource','provenance','registration','preparation','prompt','generationLog','reference','sourceMask','sourceDraft','logs']);
const RUNTIME_IMAGE_JSON = new Set(['docs/storyboard/images/atlas/shire-focus-field-v1.json',
  'docs/storyboard/images/atlas/walk/manifest.json']);
const excluded = name => EXCLUDED.some(prefix => name === prefix || name.startsWith(prefix + '/')) ||
  (/^docs\/storyboard\/(images|videos)\/.*\.(json|md|html)$/.test(name) && !RUNTIME_IMAGE_JSON.has(name));
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

function safePath(name) {
  return typeof name === 'string' && name.startsWith('docs/') && !name.includes('\\') &&
    !/[\x00-\x1f\x7f]/.test(name) && name.split('/').every(part => part && part !== '.' && part !== '..');
}

function manifestEntries(manifest) {
  if (manifest.version !== 1 || manifest.bucket !== 'miguelemosreverte/mr-pinpin-archive' || !Array.isArray(manifest.assets))
    throw Error('Invalid v1 asset manifest/bucket');
  const entries = new Map();
  for (const entry of manifest.assets) {
    if (!safePath(entry.path) || !['production','archive'].includes(entry.role) ||
        !Number.isSafeInteger(entry.bytes) || entry.bytes < 0 || !/^[a-f0-9]{64}$/.test(entry.sha256) ||
        typeof entry.object !== 'string' || !entry.object || entry.object.startsWith('/') ||
        entry.object.split('/').some(part => !part || part === '..' || part === '.') || entry.object.includes('\\'))
      throw Error(`Invalid manifest entry: ${entry.path}`);
    if (entries.has(entry.path)) throw Error(`Duplicate manifest path: ${entry.path}`);
    if (entry.role === 'production' && excluded(entry.path)) throw Error(`Production entry in excluded tree: ${entry.path}`);
    entries.set(entry.path, entry);
  }
  return entries;
}

function collectFiles(root, entries) {
  const files = new Map();
  function visit(name) {
    if (excluded(name) || entries.get(name)?.role === 'archive') return;
    const absolute = path.join(root, name), stat = fs.lstatSync(absolute);
    if (stat.isSymbolicLink()) throw Error(`Selected symlink: ${name}`);
    if (stat.isDirectory()) {
      for (const child of fs.readdirSync(absolute).sort()) visit(name + '/' + child);
    } else if (stat.isFile()) {
      const entry = entries.get(name);
      if (!entry && !STATIC.has(path.extname(name).toLowerCase()) && !['.nojekyll','CNAME','robots.txt','LICENSE','LICENSE-MIT'].includes(path.basename(name)))
        throw Error(`Unmanaged production file (refresh catalogue): ${name}`);
      if (entry && (stat.size !== entry.bytes || hash(absolute) !== entry.sha256))
        throw Error(`Production hash/size mismatch: ${name}`);
      files.set(name, stat.size);
    } else throw Error(`Unsupported file: ${name}`);
  }
  visit('docs');
  for (const [name, entry] of entries)
    if (entry.role === 'production' && !files.has(name)) throw Error(`Missing production file: ${name}`);
  return files;
}

function references(source, filename) {
  const refs = [];
  const add = (url, line = 1, base = filename) => {
    if (typeof url === 'string' && url.trim()) refs.push({url: url.trim(), line, base});
  };
  function css(text, base, line = 1) {
    const tree = postcss.parse(text, {from: filename});
    tree.walkDecls(decl => valueParser(decl.value).walk(node => {
      if (node.type === 'function' && node.value.toLowerCase() === 'url')
        add(valueParser.stringify(node.nodes).replace(/^['"]|['"]$/g, ''), line + decl.source.start.line - 1, base);
    }));
    tree.walkAtRules('import', rule => {
      const node = valueParser(rule.params).nodes[0];
      if (node?.type === 'string') add(node.value, line + rule.source.start.line - 1, base);
      else if (node?.type === 'function' && node.value === 'url')
        add(valueParser.stringify(node.nodes).replace(/^['"]|['"]$/g, ''), line + rule.source.start.line - 1, base);
    });
  }
  function js(text, base, line = 1) {
    const tree = acorn.parse(text, {ecmaVersion:'latest', sourceType:'module', locations:true, allowReturnOutsideFunction:true});
    walk.ancestor(tree, {
      Literal(node, ancestors) {
        if (typeof node.value !== 'string' || !URL_EXT.test(node.value) || /\s/.test(node.value)) return;
        if (ancestors.some(a => a.type === 'Property' && METADATA.has(a.key.name || a.key.value))) return;
        if (!node.value.includes('/') && ancestors.some(a => a.type === 'BinaryExpression' && a.operator === '+')) return;
        // Source-code extension constants and replacement suffixes are not URLs.
        if (node.value.startsWith('.') && !node.value.startsWith('./') && !node.value.startsWith('../')) return;
        add(node.value, line + node.loc.start.line - 1, base);
      },
      TemplateLiteral(node) {
        if (!node.expressions.length && URL_EXT.test(node.quasis[0].value.cooked))
          add(node.quasis[0].value.cooked, line + node.loc.start.line - 1, base);
      }
    });
  }
  const ext = path.extname(filename);
  if (ext === '.html') {
    const tree = parse(source, {sourceCodeLocationInfo:true});
    let base = filename;
    function visit(node) {
      const attrs = Object.fromEntries((node.attrs || []).map(a => [a.name,a.value]));
      const line = node.sourceCodeLocation?.startLine || 1;
      if (node.tagName === 'base' && attrs.href) {
        if (/^[a-z]+:|^\/\//i.test(attrs.href)) throw Error(`External HTML base is unsupported: ${filename}:${line}`);
        base = new URL(attrs.href, 'https://pages.invalid/' + filename.slice(5)).pathname;
        base = 'docs' + (base.endsWith('/') ? base + 'index.html' : base);
      }
      for (const name of ['src','href','poster','data-src']) if (attrs[name] && node.tagName !== 'base') add(attrs[name],line,base);
      for (const name of ['srcset','imagesrcset']) if (attrs[name])
        for (const item of parseSrcset(attrs[name])) add(item.url,line,base);
      if (attrs.style) css(attrs.style,base,line);
      if (node.tagName === 'style') css((node.childNodes || []).map(n => n.value || '').join(''),base,line);
      if (node.tagName === 'script' && !attrs.src && (!attrs.type || ['module','text/javascript','application/javascript'].includes(attrs.type)))
        js((node.childNodes || []).map(n => n.value || '').join(''),base,line);
      for (const child of node.childNodes || []) visit(child);
      if (node.content) visit(node.content);
    }
    visit(tree);
  } else if (ext === '.css') css(source,filename);
  else if (['.js','.mjs'].includes(ext) && !filename.includes('/vendor/')) js(source,filename);
  else if ((ext === '.json' && !filename.includes('/images/') && !filename.includes('/videos/')) || RUNTIME_IMAGE_JSON.has(filename)) {
    // Runtime registries use document-relative paths; focus-field data uses JSON-relative paths.
    const base = filename.includes('/stories/') ? 'docs/storyboard/index.html' : filename;
    function visit(value, keys = []) {
      if (keys.some(key => METADATA.has(key))) return;
      if (typeof value === 'string' && URL_EXT.test(value) && !/\s/.test(value)) add(value,1,base);
      else if (Array.isArray(value)) value.forEach(item => visit(item,keys));
      else if (value && typeof value === 'object') for (const [key, item] of Object.entries(value)) visit(item,[...keys,key]);
    }
    visit(JSON.parse(source));
  }
  return refs;
}

function checkReferences(root, files) {
  const errors = [], seen = new Set();
  for (const name of files.keys()) {
    if (!/\.(html|css|js|mjs|json)$/.test(name)) continue;
    for (const ref of references(fs.readFileSync(path.join(root,name),'utf8'),name)) {
      if (/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(ref.url)) continue;
      const resolved = new URL(ref.url, 'https://pages.invalid/' + ref.base.slice(5));
      const pathname = decodeURIComponent(resolved.pathname);
      let target = 'docs' + pathname;
      if (target.endsWith('/')) target += 'index.html';
      if (!files.has(target)) {
        const message = `${name}:${ref.line}: dangling local reference ${ref.url} -> ${target}`;
        if (!seen.has(message)) { errors.push(message); seen.add(message); }
      }
    }
  }
  if (errors.length) throw Error(errors.join('\n'));
}

function buildPages({root = path.resolve(__dirname,'../..'), manifest = 'assets/manifest.json', dest = '.pages-site', check = false, budget = BUDGET} = {}) {
  root = fs.realpathSync(root);
  const entries = manifestEntries(JSON.parse(fs.readFileSync(path.resolve(root,manifest),'utf8')));
  const files = collectFiles(root,entries);
  const bytes = [...files.values()].reduce((sum,size) => sum + size, 0);
  if (!Number.isSafeInteger(budget) || budget <= 0 || budget > BUDGET || bytes >= budget)
    throw Error(`Pages size ${bytes} must be below ${budget} bytes (maximum ${BUDGET})`);
  checkReferences(root,files);
  const result = {files:files.size, managedProduction:[...entries.values()].filter(e => e.role === 'production').length, bytes, budget};
  if (check) return {...result, check:true};
  const output = path.resolve(root,dest);
  if (output === root || root.startsWith(output + path.sep) || output === path.join(root,'docs') || output.startsWith(path.join(root,'docs') + path.sep))
    throw Error('Destination must be separate from the repository source');
  // Never delete an existing destination, or follow a symlink in its parent chain.
  let parent = path.dirname(output);
  while (!fs.existsSync(parent)) parent = path.dirname(parent);
  if (fs.realpathSync(parent) !== parent) throw Error('Destination parent contains a symlink');
  if (fs.existsSync(output) || fs.lstatSync(output,{throwIfNoEntry:false})) throw Error(`Destination already exists: ${output}`);
  fs.mkdirSync(path.dirname(output),{recursive:true});
  const staging = fs.mkdtempSync(path.join(path.dirname(output),'.pinpin-pages-'));
  try {
    for (const [name,size] of files) {
      const from = path.join(root,name), to = path.join(staging,name.slice(5));
      fs.mkdirSync(path.dirname(to),{recursive:true});
      if (!fs.lstatSync(from).isFile()) throw Error(`Source changed during build: ${name}`);
      fs.copyFileSync(from,to);
      if (fs.statSync(to).size !== size || hash(from) !== hash(to) || (entries.has(name) && hash(to) !== entries.get(name).sha256))
        throw Error(`Source changed during build: ${name}`);
    }
    fs.renameSync(staging,output);
  } catch (error) { fs.rmSync(staging,{recursive:true,force:true}); throw error; }
  return {...result,dest:output};
}

if (require.main === module) {
  try {
    const {values} = parseArgs({options:{root:{type:'string'},manifest:{type:'string'},dest:{type:'string'},check:{type:'boolean'},budget:{type:'string'}}});
    if (values.budget !== undefined) values.budget = Number(values.budget);
    console.log(JSON.stringify(buildPages(values),null,2));
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = {buildPages, manifestEntries, references, BUDGET};
