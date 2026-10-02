// Film QA: objective numbers for the failure modes that make a film look like a
// tech demo (empty frames, no drawn line, tiny subject, dead or boiling shots).
// It never certifies art; it tells you WHERE to look before the visual review.
//
//   node qa.mjs film.html [--samples 36] [--json out.json]
//
// Exit code: 0 = no FAIL, 2 = at least one FAIL, 1 = the film did not load/render.
import puppeteer from 'puppeteer-core';
import {execFileSync} from 'node:child_process';
import {existsSync, readFileSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const args = process.argv.slice(2);
const file = args.find(a => !a.startsWith('--') && !/^\d+$/.test(a) && !a.endsWith('.json'));
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
if (!file) { console.log('Usage: node qa.mjs film.html [--samples 36] [--json report.json]'); process.exit(1); }
const SAMPLES = Math.max(8, Math.min(120, +opt('--samples', 36)));

// ---------- static checks on the source ----------
const src = readFileSync(file, 'utf8');
const scripts = [...src.matchAll(/<script[^>]*src="([^"]+)"/g)].map(m => m[1]);
const local = scripts.filter(s => !/^(https?:|\/)/.test(s)).map(s => path.resolve(path.dirname(file), s)).filter(existsSync);
const code = [src, ...local.filter(p => !/(^|[\/\\])(core|studio|cels|materials|roto|sand|paper3d)\.js$/.test(p)).map(p => readFileSync(p, 'utf8'))].join('\n');
const count = re => (code.match(re) || []).length;
const findings = [];
const add = (level, id, msg) => findings.push({level, id, msg});

if (count(/Math\.random\s*\(/g)) add('FAIL', 'random', 'Math.random() makes textures boil and breaks seeking. Use rng(seed) / hash(k, seed).');
const marks = count(/\b(wob|crayon|hatch|surface|dotScreen|printPlate|drawCel|drawStroke|formHatch|graphite|pigmentWash|screenFill|selfDraw|brush|pen|doodle)\s*\(/g);
if (!marks) add('FAIL', 'no-marks', 'No hand-drawn mark functions are called (wob/hatch/dotScreen/printPlate/drawCel...). The film is flat vector geometry.');
const prim = count(/\.(ellipse|arc)\s*\(/g), shaped = count(/\b(curvePath|blob|smoothPts|polyPath|compileCel|bezierCurveTo|quadraticCurveTo)\s*\(/g);
if (prim > 8 && prim > shaped * 2) add('WARN', 'primitives', `Mostly circles/ellipses (${prim} arc/ellipse vs ${shaped} designed curves). Characters built from ovals read as a cutout puppet; author silhouettes with curvePath/blob/cels.`);
if (/<script[^>]*src="\/(Users|home)\//.test(src)) add('WARN', 'abs-path', 'Absolute machine paths in <script src>. Copy the assets next to the film or use relative paths.');
if (count(/\b(540|960|1080|1920)\b/g) > 6) add('WARN', 'literals', 'Many literal frame coordinates (540/960/1080/1920). Use CX, CY, W, H so other aspect ratios work.');
// an opacity ramp right before drawing a whole object = fading one drawing into another
const crossfades = count(/globalAlpha\s*=\s*(lerp|1\s*-|\(1\s*-|sm\()[^;]*;[^\n]{0,160}?\bdraw[A-Z]\w*\s*\(/g);
if (crossfades >= 1) add('WARN', 'crossfade', 'Opacity ramps detected. A transformation done by fading one drawing into another reads as a dissolve, not animation; redraw the shape through the change.');

// ---------- render-time measurements ----------
function findChrome() {
  if (process.env.CHROME) return process.env.CHROME;
  const mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'; if (existsSync(mac)) return mac;
  for (const bin of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) { try { return execFileSync('which', [bin], {stdio: ['ignore', 'pipe', 'ignore']}).toString().trim(); } catch {} }
  throw new Error('No Chrome found. Set CHROME=/path/to/chrome');
}
const url = pathToFileURL(path.resolve(file)); url.searchParams.set('bare', '1'); url.searchParams.set('w', '960');
const browser = await puppeteer.launch({executablePath: findChrome(), headless: 'new', args: ['--no-sandbox', '--disable-gpu']});
let report;
try {
  const page = await browser.newPage(), errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url.href, {waitUntil: 'load'});
  await page.waitForFunction('window.__ready === true || window.__error', {timeout: 60000});
  if (errors.length) throw new Error(errors.join('\n'));
  report = await page.evaluate(async SAMPLES => {
    const N = window.__NDRAW, fps = window.__fps, F = window.__FILM, cv = document.getElementById('c');
    const w = 480, h = Math.round(480 * cv.height / cv.width), small = document.createElement('canvas'); small.width = w; small.height = h;
    const g = small.getContext('2d', {willReadFrequently: true});
    let focus = null;
    const grab = i => { window.__focus = null; try { window.__drawFrame(i); } catch (e) { throw new Error(`frame ${i} (t=${(i / fps).toFixed(2)}s, scene ${sceneOf(i)}): ${e.message}\n${(e.stack || '').split('\n').slice(1, 3).join('\n')}`); } const fb = window.__focus; focus = fb ? Math.max((fb[3] - fb[1]) / cv.height, (fb[2] - fb[0]) / cv.width) : null; g.drawImage(cv, 0, 0, w, h); return g.getImageData(0, 0, w, h).data; };
    const sceneOf = i => { let t = i / fps, acc = 0; for (const s of F.timeline) { if (t < acc + s.dur) return s.name; acc += s.dur; } return F.timeline.at(-1).name; };
    function measure(d) {
      const n = w * h, hist = new Map(); let dark = 0, edges = 0;
      const L = new Float32Array(n);
      for (let p = 0; p < n; p++) { const r = d[p * 4], gg = d[p * 4 + 1], b = d[p * 4 + 2]; L[p] = (r * .299 + gg * .587 + b * .114) / 255;
        const key = (r >> 4) << 8 | (gg >> 4) << 4 | (b >> 4); hist.set(key, (hist.get(key) || 0) + 1); }
      // edges = any strong gradient; dark = thin dark RIDGES (a drawn line or dot), not the inside of a fill
      for (let y = 2; y < h - 2; y++) for (let x = 2; x < w - 2; x++) { const p = y * w + x, gx = L[p + 1] - L[p - 1], gy = L[p + w] - L[p - w]; if (gx * gx + gy * gy > .03) edges++;
        const v = L[p]; if ((L[p - 2] - v > .12 && L[p + 2] - v > .12) || (L[p - 2 * w] - v > .12 && L[p + 2 * w] - v > .12)) dark++; }
      // the dominant colour and everything within a small distance of it = "empty"
      let modeKey = 0, modeN = 0; for (const [k, v] of hist) if (v > modeN) { modeN = v; modeKey = k; }
      const mr = (modeKey >> 8 & 15) * 16 + 8, mg = (modeKey >> 4 & 15) * 16 + 8, mb = (modeKey & 15) * 16 + 8;
      let empty = 0, minX = w, minY = h, maxX = 0, maxY = 0;
      for (let p = 0; p < n; p++) { const dr = d[p * 4] - mr, dg = d[p * 4 + 1] - mg, db = d[p * 4 + 2] - mb; if (dr * dr + dg * dg + db * db < 900) empty++; else { const x = p % w, y = p / w | 0; if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; } }
      const lumMean = L.reduce((a, b) => a + b, 0) / n;
      return {dark: dark / n, edges: edges / n, empty: empty / n, lum: lumMean, colors: hist.size, content: maxX > minX ? (maxX - minX) * (maxY - minY) / n : 0};
    }
    const diff = (a, b) => { let s = 0, changed = 0; for (let p = 0; p < a.length; p += 4) { const e = Math.abs(a[p] - b[p]) + Math.abs(a[p + 1] - b[p + 1]) + Math.abs(a[p + 2] - b[p + 2]); s += e; if (e > 30) changed++; } return {mean: s / (a.length / 4) / 765, changed: changed / (a.length / 4)}; };
    const out = [];
    for (let k = 0; k < SAMPLES; k++) {
      const i = Math.round(k * (N - 1) / (SAMPLES - 1)), a = grab(i), m = measure(a), subject = focus;
      const j = Math.min(N - 1, i + 1), b = j !== i ? grab(j) : a, j6 = Math.min(N - 1, i + 6), c6 = j6 !== i ? grab(j6) : a;
      out.push({frame: i, t: +(i / fps).toFixed(2), scene: sceneOf(i), subject, ...m, step: diff(a, b), step6: diff(a, c6)});
      await new Promise(r => setTimeout(r, 0));
    }
    return {N, fps, duration: N / fps, size: window.__size, scenes: F.timeline.map(s => ({name: s.name, dur: s.dur})), samples: out};
  }, SAMPLES);
} catch (e) { console.error('QA could not render the film:', e.message); await browser.close(); process.exit(1); }
await browser.close();

// ---------- interpret ----------
const S = report.samples, avg = (xs, f) => xs.reduce((a, x) => a + f(x), 0) / Math.max(1, xs.length);
const pct = v => (100 * v).toFixed(1) + '%';
const lineFrames = S.filter(s => s.dark < .003).length / S.length;
if (lineFrames > .5) add('FAIL', 'no-line', `${pct(lineFrames)} of sampled frames have almost no drawn line (<0.3% thin dark ridges). Hand-drawn films need a visible contour/ink layer.`);
else if (lineFrames > .2) add('WARN', 'weak-line', `${pct(lineFrames)} of sampled frames have almost no dark line.`);
const emptyFrames = S.filter(s => s.empty > .72).length / S.length;
if (emptyFrames > .5) add('WARN', 'empty', `${pct(emptyFrames)} of frames are >72% one flat colour. Unless the look is deliberately minimal (pencil), fill the frame: setting, depth layers, a subject that occupies 20-60% of the frame height.`);
const pencil = /pencilMinimal|material\s*:\s*'pencil'|graphite\s*\(/.test(code);
const lowDetail = S.filter(s => s.edges < (pencil ? .012 : .05)).length / S.length;
if (lowDetail > .5) add(pencil ? 'WARN' : 'FAIL', 'low-detail', `${pct(lowDetail)} of frames have little drawn detail (edge density <${pencil ? '1.2' : '5'}%; the worked example koi-dragon has 20-50%). Big flat shapes read as clip-art: give the setting line work, hatching/halftone, and secondary objects.`);
// subject size, MEASURED from markFocus() — the single most common failure of weak films
const med = xs => { const v = xs.filter(x => x != null).sort((a, b) => a - b); return v.length ? v[v.length >> 1] : null; };
const subj = med(S.map(s => s.subject));
if (subj == null) add('FAIL', 'no-focus', 'The film never calls markFocus(c, pts) for its protagonist (see examples/koi-dragon.html). Subject size cannot be measured; add it to the main character draw function.');
else {
  if (subj < .12) add('FAIL', 'tiny-subject', `The protagonist's median on-screen extent is ${pct(subj)} of the frame (target 20-60%; koi-dragon is 22-90%). Move the camera closer (zoom), scale the character up, or reframe each shot.`);
  for (const sc of report.scenes) { const v = med(S.filter(s => s.scene === sc.name).map(s => s.subject)); if (v != null && v < .15 && subj >= .12) add('WARN', 'small-subject', `Scene "${sc.name}": protagonist only ${pct(v)} of the frame. Fine for a deliberate establishing shot; otherwise frame closer.`); }
}
const blank = S.filter(s => s.colors < 6 || s.empty > .985);
if (blank.length > S.length * .2) add('FAIL', 'blank', `${blank.length}/${S.length} samples are blank or near-blank (t = ${blank.map(s => s.t + 's').join(', ')}). Something is missing from those shots.`);
else if (blank.length) add('WARN', 'blank', `Near-blank frames at t = ${blank.map(s => s.t + 's').join(', ')}. Fine for a deliberate fade or title card; otherwise a shot is missing its content.`);
for (const sc of report.scenes) {
  const xs = S.filter(s => s.scene === sc.name); if (!xs.length) continue;
  const motion = avg(xs, s => s.step6.changed);
  if (sc.dur >= 2 && motion < .004) add('WARN', 'dead-shot', `Scene "${sc.name}" barely changes (${pct(motion)} pixels change over 6 frames). Is it an intended hold? Otherwise animate the subject, camera or setting.`);
  const jitter = avg(xs, s => s.step.changed), structural = avg(xs, s => s.step6.changed);
  if (jitter > .35 && jitter > structural * .8) add('WARN', 'boil', `Scene "${sc.name}" changes ${pct(jitter)} of the frame between consecutive frames, about as much as over 6 frames: likely noise/boil everywhere instead of motion with intent.`);
  if (sc.dur < 1.2) add('WARN', 'short-scene', `Scene "${sc.name}" lasts ${sc.dur}s; an action needs time to read (usually >= 1.5 s).`);
}
if (report.duration < 6) add('WARN', 'short-film', `Film is ${report.duration.toFixed(1)}s. A finished short with a beginning, action and ending usually needs 12-30 s.`);

const fails = findings.filter(f => f.level === 'FAIL').length, warns = findings.filter(f => f.level === 'WARN').length;
console.log(`\nQA ${path.basename(file)} — ${report.N} frames, ${report.fps} fps, ${report.duration.toFixed(1)} s, ${report.scenes.length} scenes`);
console.log('scene                 subject  dark-line  detail   empty   motion/6f');
for (const sc of report.scenes) { const xs = S.filter(s => s.scene === sc.name); if (!xs.length) continue;
  const sv = med(xs.map(s => s.subject));
  console.log(`${sc.name.padEnd(20).slice(0, 20)}  ${(sv == null ? '—' : pct(sv)).padStart(7)} ${pct(avg(xs, s => s.dark)).padStart(8)} ${pct(avg(xs, s => s.edges)).padStart(7)} ${pct(avg(xs, s => s.empty)).padStart(7)} ${pct(avg(xs, s => s.step6.changed)).padStart(9)}`); }
console.log('');
for (const f of findings) console.log(`${f.level === 'FAIL' ? '✗ FAIL' : '! WARN'} [${f.id}] ${f.msg}`);
console.log(fails ? `\n${fails} FAIL, ${warns} WARN — fix the FAILs, then do the visual review.` : `\nNo FAIL (${warns} WARN). Numbers only: now LOOK at the grid, strips and full-size stills.`);
if (opt('--json')) writeFileSync(opt('--json'), JSON.stringify({file: path.resolve(file), findings, ...report}, null, 2));
process.exit(fails ? 2 : 0);
