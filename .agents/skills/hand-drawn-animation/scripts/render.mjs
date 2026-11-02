// Offline Canvas renderer. --grid N: overview; --strip START,COUNT: consecutive frames.
// --only 0,24: spot frames. --ar/--width override film defaults only when supplied.
// --crops N: N evenly spaced close-ups of the protagonist (the markFocus/drawRig box), with rig pin misses in red.
//   The grid is too small to see a wing over the face or a foot off a pedal; the crop sheet is not.
// Long films: --range A,B renders frames A..B-1 into <out>/<film>-cache/ (kept between runs, existing frames skipped
//   unless --force); --assemble encodes the cache + score once every frame exists. Re-render only the scenes you changed.
// --look ink|pencil|riso|screen|doodle is passed through to films that support it.
import puppeteer from 'puppeteer-core';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const args = process.argv.slice(2), flags = new Map();
let file;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--help' || args[i] === '-h') {
    console.log('Usage: node render.mjs film.html [--grid 24 | --strip 48,12 | --only 0,24 | --crops 12 | --range 0,480 [--force] | --assemble] [--seq 02] [--out dir] [--ar 16:9] [--width 1920] [--look ink|pencil|riso|screen|doodle]');
    process.exit(0);
  }
  if (args[i] === '--force' || args[i] === '--assemble') { flags.set(args[i], true); continue; }
  if (args[i].startsWith('--')) {
    if (!['--out', '--ar', '--width', '--grid', '--strip', '--only', '--look', '--crops', '--range', '--seq'].includes(args[i])) throw new Error(`Unknown option: ${args[i]}`);
    if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error(`Missing value: ${args[i]}`);
    flags.set(args[i], args[++i]);
  } else if (!file) file = args[i]; else throw new Error(`Unexpected argument: ${args[i]}`);
}
if (!file) throw new Error('Usage: node render.mjs film.html [--grid 24 | --strip 48,12 | --only 0,24] [--out dir]');
const integer = (v, name, min = 1, max = 16384) => {
  const n = Number(v); if (!Number.isInteger(n) || n < min || n > max) throw new Error(`${name}: expected integer ${min}..${max}`); return n;
};
const only = flags.has('--only') ? flags.get('--only').split(',').map(v => integer(v, 'frame', 0, 1e7)) : null;
const grid = flags.has('--grid') ? integer(flags.get('--grid'), 'grid', 1, 240) : null;
const strip = flags.has('--strip') ? flags.get('--strip').split(',').map(Number) : null;
if (strip && (strip.length !== 2 || !Number.isInteger(strip[0]) || strip[0] < 0 || !Number.isInteger(strip[1]) || strip[1] < 1 || strip[1] > 240)) throw new Error('--strip expects START_FRAME,COUNT (count 1..240)');
const crops = flags.has('--crops') ? integer(flags.get('--crops'), 'crops', 1, 48) : null;
const range = flags.has('--range') ? flags.get('--range').split(',').map(Number) : null;
if (range && (range.length !== 2 || !range.every(Number.isInteger) || range[0] < 0 || range[1] <= range[0])) throw new Error('--range expects START,END frames (END exclusive)');
const assemble = flags.has('--assemble');
if ([only, grid, strip, crops, range, assemble].filter(Boolean).length > 1) throw new Error('Choose only one of --only, --grid, --strip, --crops, --range, --assemble');
const preview = !!(only || grid || strip || crops), name = path.basename(file, '.html');
const out = path.resolve(flags.get('--out') || path.join(path.dirname(file), 'out'));
mkdirSync(out, {recursive: true});
// Every one-shot full render owns a new frame directory (failed attempts keep their files for diagnosis).
// --range/--assemble share a persistent cache so a long film is rendered and fixed scene by scene.
const cached = !!(range || assemble), cache = path.join(out, `${name}-cache`);
const work = preview ? out : cached ? cache : mkdtempSync(path.join(out, `.${name}-render-`));
const frames = cached ? cache : path.join(work, `${name}-frames`); mkdirSync(frames, {recursive: true});
// the film and its local scripts, hashed: --assemble names the ranges rendered from an older version of the code
const srcHash = () => { const h = createHash('sha1'), html = readFileSync(file, 'utf8'); h.update(html);
  for (const m of html.matchAll(/<script[^>]*src="([^"]+)"/g)) { const f = path.resolve(path.dirname(file), m[1]); if (existsSync(f)) h.update(readFileSync(f)); } return h.digest('hex').slice(0, 12); };
const manifestPath = path.join(cache, 'manifest.json'), readManifest = () => existsSync(manifestPath) ? JSON.parse(readFileSync(manifestPath, 'utf8')) : {ranges: []};
const url = pathToFileURL(path.resolve(file)); url.searchParams.set('bare', '1'); url.searchParams.set('frame', '0');
if (flags.has('--ar')) {
  const ar = flags.get('--ar'); if (!/^\d+(?:\.\d+)?[:x/]\d+(?:\.\d+)?$/.test(ar) || ar.split(/[:x/]/).some(v => Number(v) <= 0)) throw new Error('Invalid aspect ratio');
  url.searchParams.set('ar', ar);
}
if (flags.has('--width')) url.searchParams.set('w', integer(flags.get('--width'), 'width', 2));
if (flags.has('--look')) url.searchParams.set('look', flags.get('--look'));
// --seq 02: long films built from assets/long-film.html keep only that sequence (global time preserved) for previews
if (flags.has('--seq')) { if (!preview) throw new Error('--seq is for previews (--grid/--strip/--only/--crops); render the full film with --range'); url.searchParams.set('seq', flags.get('--seq')); }
function findChrome() {
  if (process.env.CHROME) return process.env.CHROME;
  const mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'; if (existsSync(mac)) return mac;
  for (const bin of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) {
    try { return execFileSync('which', [bin], {stdio: ['ignore', 'pipe', 'ignore']}).toString().trim(); } catch {}
  }
  throw new Error('No Chrome found. Set CHROME=/path/to/chrome');
}
// cropSheet (runs in the page): n frames, each cropped to the registered subject box + margin, 4 across, labelled.
// Frames where a rig pin misses get a red label; frames with no subject box show the whole frame with a red border.
function cropSheet(n) {
  const N = window.__NDRAW, fps = window.__fps, cv = document.getElementById('c'), cols = 4, cw = 420, chh = 420, lab = 22, rows = Math.ceil(n / cols);
  const sheet = document.createElement('canvas'); sheet.width = cols * cw; sheet.height = rows * (chh + lab); const g = sheet.getContext('2d');
  g.fillStyle = '#141414'; g.fillRect(0, 0, sheet.width, sheet.height); g.font = '13px ui-monospace, Menlo, monospace';
  for (let k = 0; k < n; k++) {
    const i = Math.round(k * (N - 1) / Math.max(1, n - 1)); window.__focus = null; window.__rig = []; window.__drawFrame(i);
    const f = window.__focus, miss = (window.__rig || []).flatMap(r => r.contacts.filter(q => q.err > q.tol).map(q => `${q.socket} ${q.err.toFixed(0)}px`));
    let [x0, y0, x1, y1] = f || [0, 0, cv.width, cv.height]; const m = .12 * Math.max(x1 - x0, y1 - y0), side = Math.max(x1 - x0, y1 - y0) + 2 * m, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const sx = Math.max(0, cx - side / 2), sy = Math.max(0, cy - side / 2), sw = Math.min(cv.width - sx, side), sh = Math.min(cv.height - sy, side), s = Math.min(cw / sw, chh / sh);
    const x = (k % cols) * cw, y = Math.floor(k / cols) * (chh + lab);
    g.drawImage(cv, sx, sy, sw, sh, x + (cw - sw * s) / 2, y + (chh - sh * s) / 2, sw * s, sh * s);
    if (!f) { g.strokeStyle = '#e0201b'; g.lineWidth = 3; g.strokeRect(x + 2, y + 2, cw - 4, chh - 4); }
    g.fillStyle = miss.length || !f ? '#ff6b5e' : '#e6e6e6'; g.fillText(`${String(i).padStart(4, '0')} ${(i / fps).toFixed(2)}s ${!f ? 'NO SUBJECT BOX' : miss.join(' ')}`.slice(0, 54), x + 4, y + chh + 15);
  }
  return sheet.toDataURL('image/jpeg', .9);
}
const save = (f, data) => writeFileSync(f, Buffer.from(data.split(',')[1], 'base64'));

let ffmpegBin = process.env.FFMPEG_PATH || 'ffmpeg';
if (ffmpegBin === 'ffmpeg') {
  for (const bin of ['/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg']) {
    if (existsSync(bin)) { ffmpegBin = bin; break; }
  }
}
if (ffmpegBin === 'ffmpeg') {
  try {
    const mod = await import('ffmpeg-static');
    if (mod.default && existsSync(mod.default)) ffmpegBin = mod.default;
  } catch {}
}
const ff = argv => execFileSync(ffmpegBin, ['-v', 'error', '-y', ...argv], {stdio: 'inherit'});
const browser = await puppeteer.launch({executablePath: findChrome(), headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']});
let N, fps, size, hasAudio = false;
try {
  const page = await browser.newPage(), errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url.href, {waitUntil: 'load'});
  await page.waitForFunction('window.__ready === true || window.__error', {timeout: 60000});
  const meta = await page.evaluate(() => ({N: window.__NDRAW, fps: window.__fps, size: window.__size, error: window.__error}));
  ({N, fps, size} = meta);
  if (meta.error || errors.length) throw new Error(meta.error || errors.join('\n'));
  if (!Number.isInteger(N) || N <= 0 || ![12, 24].includes(fps)) throw new Error('Invalid film frame count or fps');
  console.log(`${name}: ${N} frames, ${fps} fps, ${size.w}x${size.h}`);
  if (flags.has('--seq')) { const r = await page.evaluate(() => window.__seqRange || null); if (r) console.log(`Sequence ${flags.get('--seq')} = film frames ${r[0]}..${r[1] - 1}; labels in this preview are local. Render it with --range ${r[0]},${r[1]} (no --seq).`); }
  if (only?.some(i => i >= N) || strip && strip[0] + strip[1] > N || range && range[1] > N) throw new Error(`Requested frames outside film (0..${N - 1})`);
  if (grid) save(path.join(out, `${name}-grid.jpg`), await page.evaluate(n => window.__grid(n), grid));
  if (strip) save(path.join(out, `${name}-strip-${strip[0]}.jpg`), await page.evaluate(([a, b]) => window.__strip(a, b), strip));
  if (crops) save(path.join(out, `${name}-crops.jpg`), await page.evaluate(cropSheet, crops));
  const pad4 = i => String(i).padStart(4, '0');
  let list = grid || strip || crops || assemble ? [] : only || (range ? Array.from({length: range[1] - range[0]}, (_, k) => range[0] + k) : Array.from({length: N}, (_, i) => i));
  if (range && !flags.has('--force')) { const before = list.length; list = list.filter(i => !existsSync(path.join(frames, `${pad4(i)}.png`))); if (before !== list.length) console.log(`Cache: ${before - list.length} frames already rendered (use --force to redo them)`); }
  if (!preview && list.length > 24) {
    const concurrency = Math.min(4, Math.max(1, list.length));
    const pages = [page];
    for (let w = 1; w < concurrency; w++) {
      const p = await browser.newPage();
      p.on('pageerror', e => errors.push(String(e)));
      p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      await p.goto(url.href, {waitUntil: 'load'});
      await p.waitForFunction('window.__ready === true || window.__error', {timeout: 60000});
      pages.push(p);
    }
    let idx = 0, done = 0;
    const worker = async (p) => {
      while (idx < list.length) {
        if (errors.length) break;
        const currentIdx = idx++;
        const i = list[currentIdx];
        const data = await p.evaluate(fn => window.__frame(fn), i);
        save(path.join(frames, `${String(i).padStart(4, '0')}.png`), data);
        done++;
        if (done % 120 === 0 || done === list.length) console.log(`Rendered ${done}/${list.length}`);
      }
    };
    await Promise.all(pages.map(p => worker(p)));
    for (let w = 1; w < pages.length; w++) await pages[w].close();
  } else {
    for (const [k, i] of list.entries()) {
      save(path.join(frames, `${String(i).padStart(4, '0')}.png`), await page.evaluate(i => window.__frame(i), i));
      if (errors.length) throw new Error(`Frame ${i}: ${errors.join('\n')}`);
      if (!preview && ((k + 1) % 120 === 0 || k === list.length - 1)) console.log(`Rendered ${k + 1}/${N}`);
    }
  }
  if (range) {
    // record the code version per frame actually rendered now: new runs replace the parts of older entries they cover
    const m = readManifest(), hash = srcHash(), at = new Date().toISOString(), runs = [];
    for (const i of list) { const r = runs.at(-1); if (r && r.to === i) r.to = i + 1; else runs.push({from: i, to: i + 1}); }
    for (const r of runs) m.ranges = m.ranges.flatMap(o => o.to <= r.from || o.from >= r.to ? [o] : [...(o.from < r.from ? [{...o, to: r.from}] : []), ...(o.to > r.to ? [{...o, from: r.to}] : [])]).concat({...r, hash, at});
    m.N = N; m.fps = fps; m.ranges.sort((x, y) => x.from - y.from); writeFileSync(manifestPath, JSON.stringify(m, null, 2) + '\n');
    console.log(`Cached frames ${range[0]}..${range[1] - 1} in ${cache}. Missing: ${Array.from({length: N}, (_, i) => i).filter(i => !existsSync(path.join(frames, `${pad4(i)}.png`))).length} of ${N}.`); }
  if (!preview && !range) {
    const wav = await page.evaluate(() => window.__wav ? window.__wav() : null);
    if (wav) { writeFileSync(path.join(work, `${name}-score.wav`), Buffer.from(wav, 'base64')); hasAudio = true; }
  }
  if (errors.length) throw new Error(errors.join('\n'));
} catch (e) {
  console.error(`Render failed; diagnostic files: ${work}`); throw e;
} finally { await browser.close(); }
if (assemble) {
  const missing = Array.from({length: N}, (_, i) => i).filter(i => !existsSync(path.join(frames, `${String(i).padStart(4, '0')}.png`)));
  if (missing.length) throw new Error(`--assemble: ${missing.length} of ${N} frames missing in ${cache} (first: ${missing.slice(0, 8).join(', ')}). Render them with --range.`);
  const m = readManifest(), now = srcHash(), stale = (m.ranges || []).filter(r => r.hash !== now);
  if (stale.length) console.warn(`WARNING: ranges rendered from an older version of the film code: ${stale.map(r => `${r.from}-${r.to}`).join(', ')}. Re-render those with --range ... --force if the change affects them.`);
}
if (!preview && !range) {
  const duration = N / fps, outputFrames = N * 24 / fps, mp4 = path.join(work, `${name}.mp4`);
  ff(['-framerate', String(fps), '-i', path.join(frames, '%04d.png'), '-vf', 'fps=24', '-frames:v', String(outputFrames), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', mp4]);
  ff(['-i', mp4, '-vf', `fps=2,scale=240:-2,tile=6x${Math.max(1, Math.ceil(duration * 2 / 6))}`, '-frames:v', '1', path.join(work, `${name}-contact.jpg`)]);
  if (hasAudio) ff(['-i', mp4, '-i', path.join(work, `${name}-score.wav`), '-map', '0:v:0', '-map', '1:a:0', '-af', 'apad', '-t', String(duration), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', path.join(work, `${name}-final.mp4`)]);
  writeFileSync(path.join(work, `${name}-render.json`), JSON.stringify({file: path.resolve(file), fps, frames: N, outputFps: 24, outputFrames, duration, size, look: flags.get('--look') || null, audio: hasAudio}, null, 2) + '\n');
  // Publish only completed outputs; remove stale companions only for this exact film.
  for (const suffix of ['-frames', '.mp4', '-contact.jpg', '-score.wav', '-final.mp4', '-render.json']) {
    if (cached && suffix === '-frames') continue;
    const dest = path.join(out, name + suffix), src = path.join(work, name + suffix);
    if (suffix === '-frames') rmSync(dest, {recursive: true, force: true});
    if (existsSync(src)) renameSync(src, dest); else rmSync(dest, {force: true});
  }
  if (!cached) rmSync(work, {recursive: true, force: true});
  console.log(`Finished: ${path.join(out, name + (hasAudio ? '-final.mp4' : '.mp4'))}`);
} else if (preview) console.log(`Preview: ${out}`);
