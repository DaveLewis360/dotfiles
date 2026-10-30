/* Rice-konfigurátor — statikus webapp, file://-ról is fut.
 * Adat: data/catalog.js (window.RICE_CATALOG), amit a collect.py generál.
 * Állapot: localStorage ("rice-configurator/v1"); kimenet: Export JSON.
 * Hálózatot nem használ, semmit nem ír a gépre a letöltésen kívül. */
'use strict';
(function () {
  const C = window.RICE_CATALOG;
  const $ = (s, r = document) => r.querySelector(s);
  const main = $('#main');
  if (!C || !Array.isArray(C.entries)) {
    main.innerHTML = '<p class="empty">Hiányzik a <code>data/catalog.js</code>. Futtasd: <code>python3 collect.py</code></p>';
    return;
  }
  const STORE = 'rice-configurator/v1';
  const E = C.entries;
  const byId = new Map(E.map(e => [e.id, e]));
  const catById = new Map(C.categories.map(c => [c.id, c]));
  // betűnév → telepített név; szóköz- és kisbetű-független (GoogleSansFlex = Google Sans Flex)
  const fkey = f => f.toLowerCase().replace(/[\s_-]+/g, '');
  const fontMap = new Map((C.fonts || []).map(f => [fkey(f), f]));
  const GENERIC = new Set(['sans', 'sansserif', 'serif', 'monospace', 'mono', 'systemui', 'cursive', 'fantasy']);
  const installedFont = f => fontMap.get(fkey(f)) || (GENERIC.has(fkey(f)) ? f : null);
  const PRESETS = C.presets || {};

  // ── téma: a jelenlegi caelestia séma színei ───────────────────────────
  const TMAP = { bg: 'background', surface: 'surfaceContainer', surface2: 'surfaceContainerHigh',
    surface3: 'surfaceContainerHighest', fg: 'onSurface', fg2: 'onSurfaceVariant', primary: 'primary',
    'on-primary': 'onPrimary', pcont: 'primaryContainer', 'on-pcont': 'onPrimaryContainer',
    scont: 'secondaryContainer', 'on-scont': 'onSecondaryContainer', tertiary: 'tertiary', error: 'error',
    outline: 'outline', outline2: 'outlineVariant' };
  for (const [v, k] of Object.entries(TMAP)) {
    const c = (C.theme || {})[k];
    if (/^[0-9a-f]{6}$/i.test(c || '')) document.documentElement.style.setProperty('--' + v, '#' + c);
  }

  // ── állapot ──────────────────────────────────────────────────────────
  let storageOk = true;
  function fresh() { return { marks: {}, presetsApplied: [], notes: '' }; }
  function applyPresets(s) {
    const done = new Set(s.presetsApplied);
    for (const [id, p] of Object.entries(PRESETS)) {
      if (done.has(id) || !byId.has(id)) continue;
      if (!s.marks[id]) s.marks[id] = { d: p.decision, p: p.proposed === undefined ? undefined : String(p.proposed), c: '', preset: true };
      s.presetsApplied.push(id);
    }
    return s;
  }
  function load() {
    let s;
    try { s = JSON.parse(localStorage.getItem(STORE) || 'null'); } catch (_) { storageOk = false; }
    s = s && typeof s === 'object' ? s : fresh();
    s.marks = s.marks || {}; s.presetsApplied = s.presetsApplied || []; s.notes = s.notes || '';
    return applyPresets(s);
  }
  let state = load();
  let saveTimer = null;
  function save() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      try { localStorage.setItem(STORE, JSON.stringify(state)); flash('Mentve'); }
      catch (_) { storageOk = false; flash('Nem menthető — exportálj!', true); }
    }, 250);
  }
  function flash(t, bad) {
    const el = $('#saved');
    el.textContent = t; el.style.color = bad ? 'var(--error)' : '';
    clearTimeout(flash.t); if (!bad) flash.t = setTimeout(() => { el.textContent = ''; }, 1500);
  }
  const mark = id => state.marks[id] || {};
  function setMark(id, patch) {
    const m = Object.assign({}, state.marks[id] || {}, patch);
    if ('d' in patch || 'p' in patch) m.preset = false;
    if (!m.d && !m.c && (m.p === undefined || m.p === '')) delete state.marks[id];
    else state.marks[id] = m;
    save();
  }

  // ── formázás ─────────────────────────────────────────────────────────
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const md = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>');
  function fmt(v) {
    if (v === undefined) return '—';
    if (v === null) return 'null';
    if (v === '') return '(üres)';
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
  }
  function valHtml(v) {
    const s = fmt(v);
    if (s.length > 140) {
      const full = typeof v === 'object' ? JSON.stringify(v, null, 1) : s;
      return `<details><summary>${esc(s.slice(0, 90))}…</summary><span class="v">${esc(full)}</span></details>`;
    }
    return `<span class="v">${esc(s)}</span>`;
  }
  function normDeep(v) {
    if (typeof v === 'string') {
      const t = v.trim();
      if (t === 'true' || t === 'yes') return true;
      if (t === 'false' || t === 'no') return false;
      if (t !== '' && !isNaN(Number(t))) return Number(t);
      return t;
    }
    if (typeof v === 'number') return Math.round(v * 1e6) / 1e6;
    if (Array.isArray(v)) return v.map(normDeep);
    if (v && typeof v === 'object') { const o = {}; for (const k of Object.keys(v).sort()) o[k] = normDeep(v[k]); return o; }
    return v;
  }
  const same = (a, b) => JSON.stringify(normDeep(a)) === JSON.stringify(normDeep(b));
  const differs = e => ('def' in e) && e.def !== null && e.def !== undefined && !same(e.cur, e.def);
  const TYPE_HU = { bool: 'logikai (true / false)', int: 'egész szám', float: 'tört szám', string: 'szöveg',
    enum: 'felsorolás', color: 'szín', font: 'betűcsalád', list: 'lista', object: 'objektum',
    bind: 'billentyű → művelet', rule: 'szabály', exec: 'shell-parancs', curve: 'bezier-görbe (2 kontrollpont)',
    'curve-qml': 'QML bezier-görbe (szegmensek: x1,y1,x2,y2,végx,végy)', animation: 'animáció: görbe, sebesség (1 = 100 ms), stílus',
    scheme: 'színséma', palette: 'paletta', path: 'útvonal', gesture: 'gesztus: ujjak, irány, művelet' };

  // ── színek ───────────────────────────────────────────────────────────
  function cssColor(s) {
    if (typeof s !== 'string') return null;
    const t = s.trim(); let m;
    if ((m = t.match(/^rgba?\(\s*([0-9a-f]{6}|[0-9a-f]{8})\s*\)$/i))) return '#' + m[1];
    if ((m = t.match(/^0x([0-9a-f]{2})([0-9a-f]{6})$/i))) return '#' + m[2] + m[1];
    if ((m = t.match(/^#?([0-9a-f]{6})$/i))) return '#' + m[1];
    if ((m = t.match(/^#([0-9a-f]{8})$/i))) return '#' + m[1];
    if (/^[a-z]{3,20}$/i.test(t) && window.CSS && CSS.supports('color', t)) return t.toLowerCase();
    return null;
  }
  function gradient(s) {
    if (typeof s !== 'string' || !s.trim()) return null;
    let angle = 0; const cols = [];
    for (const p of s.trim().split(/\s+/)) {
      let m;
      if ((m = p.match(/^(-?\d+)deg$/))) { angle = +m[1]; continue; }
      if ((m = p.match(/^([0-9a-f]{2})([0-9a-f]{6})$/i))) { cols.push('#' + m[2] + m[1]); continue; }
      const c = cssColor(p); if (!c) return null; cols.push(c);
    }
    if (!cols.length) return null;
    return cols.length === 1 ? cols[0] : `linear-gradient(${angle + 90}deg, ${cols.join(', ')})`;
  }
  const swatch = (css, title, wide) => `<span class="sw${wide ? ' wide' : ''}" title="${esc(title || '')}"><i style="background:${css}"></i></span>`;

  // ── betűk ────────────────────────────────────────────────────────────
  function fontFamily(v) {
    if (Array.isArray(v)) v = v[0];
    if (typeof v !== 'string' || !v.trim() || v.trim().startsWith('<')) return null;
    return v.split(':')[0].replace(/\s+\d+(\.\d+)?$/, '').trim();
  }
  const SAMPLE = 'Árvíztűrő tükörfúrógép · The quick brown fox · 0123456789 {}[]() => != ';
  function fontPreview(v) {
    const f = fontFamily(v); if (!f) return '';
    const inst = installedFont(f);
    const safe = (inst || f).replace(/[^\w \-.]/g, '');
    return `<span class="fontprev" style="font-family:'${safe}', var(--mono)">${esc(SAMPLE)}` +
      `<small>${esc(f)}${inst ? (inst !== f ? ` (telepítve: ${esc(inst)})` : '')
        : ' — nincs a telepített betűk között (fc-list), helyettesítő betű látszik'}</small></span>`;
  }
  const fontMissing = e => e.type === 'font' && !!fontFamily(e.cur) && !installedFont(fontFamily(e.cur));

  // ── görbék ───────────────────────────────────────────────────────────
  function segments(v) {
    if (!Array.isArray(v)) return null;
    if (v.length === 2 && Array.isArray(v[0]) && Array.isArray(v[1])) return [[v[0][0], v[0][1], v[1][0], v[1][1], 1, 1]];
    if (v.length && typeof v[0] === 'number' && v.length % 6 === 0) {
      const s = []; for (let i = 0; i < v.length; i += 6) s.push(v.slice(i, i + 6)); return s;
    }
    return null;
  }
  const bez = (a, b, c, d, t) => { const u = 1 - t; return u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d; };
  function samplePts(segs, n = 40) {
    let x0 = 0, y0 = 0; const pts = [[0, 0]];
    for (const s of segs) {
      for (let i = 1; i <= n; i++) { const t = i / n; pts.push([bez(x0, s[0], s[2], s[4], t), bez(y0, s[1], s[3], s[5], t)]); }
      x0 = s[4]; y0 = s[5];
    }
    return pts;
  }
  function curvePreview(segs, durMs, caption) {
    const pts = samplePts(segs);
    const ys = pts.map(p => p[1]);
    const ymin = Math.min(0, ...ys), ymax = Math.max(1, ...ys);
    const W = 110, H = 70, pad = 6;
    const sx = x => (pad + x * (W - 2 * pad)).toFixed(1);
    const sy = y => (H - pad - (y - ymin) / (ymax - ymin) * (H - 2 * pad)).toFixed(1);
    const d = pts.map((p, i) => (i ? 'L' : 'M') + sx(p[0]) + ' ' + sy(p[1])).join(' ');
    const mono = []; let last = -1;
    for (const p of pts) if (p[0] > last + 1e-4) { mono.push(p); last = p[0]; }
    const lin = 'linear(' + mono.map(p => `${p[1].toFixed(3)} ${(Math.min(1, p[0]) * 100).toFixed(1)}%`).join(', ') + ')';
    let ease = 'ease';
    if (window.CSS && CSS.supports('animation-timing-function', lin)) ease = lin;
    else if (segs.length === 1) ease = `cubic-bezier(${segs[0].slice(0, 4).map(x => Math.max(0, Math.min(1, x))).join(',')})`;
    const dur = Math.max(80, Math.min(4000, durMs || 600));
    return `<span class="curve" title="Vidd fölé az egeret: a pötty a görbe szerint mozog (${dur} ms)">` +
      `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
      `<line x1="${sx(0)}" y1="${sy(0)}" x2="${sx(1)}" y2="${sy(0)}" stroke="currentColor" stroke-opacity=".25"/>` +
      `<line x1="${sx(0)}" y1="${sy(1)}" x2="${sx(1)}" y2="${sy(1)}" stroke="currentColor" stroke-opacity=".25" stroke-dasharray="3 3"/>` +
      `<path d="${d}" fill="none" stroke="var(--primary)" stroke-width="2"/></svg>` +
      `<span class="track"><span class="dot" style="--ease:${ease};--dur:${dur}ms"></span></span>` +
      `<span class="cap">${esc(caption || '')}</span></span>`;
  }
  function durFor(name) {
    const d = byId.get('tokens:appearance.animDurations.' + name);
    return d ? Number(d.cur) : 400;
  }

  // ── előnézet egy bejegyzéshez ────────────────────────────────────────
  function preview(e) {
    const v = e.cur;
    if (e.type === 'font' || e.prev === 'font') return fontPreview(v);
    if (e.type === 'color' || e.prev === 'color') {
      const g = gradient(typeof v === 'string' ? v : '');
      return g ? swatch(g, String(v), g.startsWith('linear')) : '';
    }
    if (e.prev === 'swatches' && Array.isArray(v)) {
      return '<span class="swrow">' + v.map(x => { const m = String(x).match(/^(\d+)=(.+)$/); const c = m && cssColor(m[2]); return c ? swatch(c, x) : ''; }).join('') + '</span>';
    }
    if (e.prev === 'swatches' && v && typeof v === 'object') {
      return '<span class="swrow">' + Object.entries(v).map(([k, c]) => cssColor(c) ? swatch(cssColor(c), k + ' #' + c) : '').join('') + '</span>';
    }
    if (e.prev === 'palette' && v && typeof v === 'object') {
      return '<span class="palette">' + Object.entries(v).map(([k, c]) => cssColor(c) ? `<span>${swatch(cssColor(c), k)}${esc(k)} <span class="mono">#${esc(c)}</span></span>` : '').join('') + '</span>';
    }
    if (e.type === 'curve' || e.type === 'curve-qml') {
      const s = segments(v); if (!s) return '';
      return curvePreview(s, e.type === 'curve-qml' ? durFor(e.key.split('.').pop()) : 600, e.type === 'curve' ? 'előnézet: 600 ms' : `előnézet: ${durFor(e.key.split('.').pop())} ms`);
    }
    if (e.type === 'animation' && v) {
      const s = segments(v.curve);
      const ms = Math.round((Number(v.speed) || 0) * 100);
      const cap = `${v.bezier} · ${ms} ms${v.style ? ' · ' + v.style : ''}${v.enabled === false ? ' · KIKAPCSOLVA' : ''}`;
      return s ? curvePreview(s, ms, cap) : `<span class="cap">${esc(cap)}</span>`;
    }
    if (e.prev === 'duration') {
      const ms = Number(v) || 0;
      return `<span><span class="durbar" style="width:${Math.min(400, ms / 4)}px"></span><span class="cap">${ms} ms</span></span>`;
    }
    return '';
  }
  function keysHtml(combo) {
    return String(combo).split(/\s*\+\s*/).filter(Boolean).map(k => `<kbd>${esc(k)}</kbd>`).join('+');
  }
  function possible(e) {
    const parts = [];
    if (e.opts && e.opts.length) {
      const cur = normDeep(e.cur);
      parts.push(e.opts.slice(0, 60).map(o => {
        const val = Array.isArray(o) ? o[0] : o;
        const lab = Array.isArray(o) ? `${o[0]} = ${o[1]}` : o;
        const on = JSON.stringify(normDeep(val)) === JSON.stringify(cur);
        return `<span class="opt${on ? ' cur' : ''}">${esc(lab)}</span>`;
      }).join('') + (e.opts.length > 60 ? ` <span class="cap">… (+${e.opts.length - 60})</span>` : ''));
    }
    if (e.min !== undefined || e.max !== undefined) parts.push(`tartomány: <span class="v">${esc(fmt(e.min))} – ${esc(fmt(e.max))}</span>`);
    if (e.type === 'color' && e.id.startsWith('hypr:')) parts.push('szín: <code>rgb(rrggbb)</code>, <code>rgba(rrggbbaa)</code>, <code>0xAARRGGBB</code>; gradiens: több szín + szög, pl. <code>rgba(…) rgba(…) 45deg</code>');
    else if (!parts.length || e.type !== 'enum') parts.push(esc(TYPE_HU[e.type] || e.type));
    if (e.x && e.x.fields && e.x.fields.length) parts.push('elemek mezői: ' + e.x.fields.map(f => `<code>${esc(f)}</code>`).join(' '));
    return parts.join(' · ');
  }

  // ── egy kártya ───────────────────────────────────────────────────────
  let dlCounter = 0;
  function proposedInput(e, m) {
    const val = m.p === undefined || m.p === null ? '' : String(m.p);
    if (e.type === 'bool') {
      return `<select data-f="p"><option value="">— javasolt érték —</option>` +
        ['true', 'false'].map(o => `<option${val === o ? ' selected' : ''}>${o}</option>`).join('') + '</select>';
    }
    let dl = '', list = '';
    if (e.type === 'font') dl = 'dl-fonts';
    else if (e.opts && e.opts.length) {
      dl = 'dl-' + (++dlCounter);
      list = `<datalist id="${dl}">` + e.opts.map(o => Array.isArray(o)
        ? `<option value="${esc(o[0])}">${esc(o[1])}</option>` : `<option value="${esc(o)}"></option>`).join('') + '</datalist>';
    }
    const ph = e.min !== undefined ? `javasolt érték (${fmt(e.min)} – ${fmt(e.max)})` : 'javasolt érték';
    return `<input type="text" data-f="p" value="${esc(val)}" placeholder="${esc(ph)}"${dl ? ` list="${dl}"` : ''}>${list}`;
  }
  function card(e, showCat) {
    const m = mark(e.id);
    const cls = ['item'];
    if (m.d) cls.push('d-' + m.d);
    if (m.c && card.open.has(e.id)) cls.push('c-open');
    const b = [];
    if (e.set) b.push('<span class="badge set" title="A configban kifejezetten be van állítva">config</span>');
    if (differs(e)) b.push('<span class="badge diff" title="Eltér az alapértéktől">≠ alap</span>');
    if ('live' in e) b.push(`<span class="badge live" title="A futó Hyprland ezt az értéket mutatja">élő: ${esc(fmt(e.live))}</span>`);
    if (fontMissing(e)) b.push('<span class="badge warn">nincs telepítve</span>');
    if (m.preset) b.push('<span class="badge preset" title="Abból jelöltük elő, amit már tudunk rólad">előjelölve</span>');
    const p = PRESETS[e.id];
    const cat = catById.get(e.cat);
    const isBind = e.type === 'bind' || e.prev === 'keys';
    const pv = preview(e);
    const rows = [['Jelenlegi', valHtml(e.cur) + (pv ? '<br>' + pv : '')]];
    if ('def' in e) rows.push(['Alapérték', valHtml(e.def)]);
    rows.push(['Lehetséges', possible(e)]);
    if (e.file) rows.push(['Fájl', `<code>${esc(e.file)}</code>`]);
    const D = [['keep', 'Tartsd'], ['change', 'Változtasd'], ['ignore', 'Nem érdekel']];
    return `<article class="${cls.join(' ')}" data-id="${esc(e.id)}">` +
      `<div class="head">${isBind ? keysHtml(e.key) : `<code class="key">${esc(e.key)}</code>`}` +
      (e.label ? `<span class="label">${esc(e.label)}</span>` : '') +
      (showCat && cat ? `<span class="catname">${esc(groupTitle(cat.group))} › ${esc(cat.title)}</span>` : '') +
      b.join('') + '</div>' +
      (e.desc ? `<p class="desc">${md(e.desc)}</p>` : '') +
      '<dl class="vals">' + rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('') + '</dl>' +
      (e.note ? `<p class="note">${md(e.note)}</p>` : '') +
      (p && p.reason ? `<p class="reason">Amit tudunk: ${esc(p.reason)}</p>` : '') +
      '<div class="decide"><span class="seg">' +
      D.map(([d, t]) => `<button type="button" data-d="${d}" class="${m.d === d ? 'on' : ''}">${t}</button>`).join('') +
      `</span><span class="proposed">${proposedInput(e, m)}</span>` +
      `<button type="button" class="ctoggle${m.c ? ' has' : ''}">Megjegyzés${m.c ? ' ✓' : ''}</button></div>` +
      `<textarea class="comment" rows="2" placeholder="Megjegyzés ehhez a paraméterhez…">${esc(m.c || '')}</textarea>` +
      '</article>';
  }
  card.open = new Set();

  // ── nézetek, szűrés ──────────────────────────────────────────────────
  const groupTitle = g => (C.groups.find(x => x.id === g) || { title: g }).title;
  const isMarked = e => { const m = state.marks[e.id]; return !!(m && (m.d || m.c)); };
  const VIEWS = [
    { id: 'overview', title: 'Áttekintés és súgó' },
    { id: 'presets', title: 'Előjelöltek', f: e => !!PRESETS[e.id] },
    { id: 'fonts', title: 'Betűk', f: e => e.type === 'font' || (/font/i.test(e.key) && !/^ghostty:font-(feature|codepoint|variation|synthetic|thicken)/.test(e.id)) },
    { id: 'colors', title: 'Színek', f: e => ['color', 'palette', 'scheme'].includes(e.type) || e.prev === 'swatches' },
    { id: 'anim', title: 'Animációk', f: e => ['curve', 'curve-qml', 'animation'].includes(e.type) || e.prev === 'duration' || /(^|\.)anim/i.test(e.key) },
    { id: 'changed', title: 'Eltér az alapértéktől', f: e => e.set && differs(e) },
    { id: 'marked', title: 'Jelöltek', f: isMarked },
  ];
  const hayCache = new Map();
  function hay(e) {
    let h = hayCache.get(e.id);
    if (!h) {
      const c = catById.get(e.cat);
      h = [e.key, e.label, e.desc, e.group, e.note, fmt(e.cur), c && c.title].filter(Boolean).join(' \u0001 ').toLowerCase();
      hayCache.set(e.id, h);
    }
    return h;
  }
  function filtered(list) {
    const q = $('#search').value.trim().toLowerCase();
    const toks = q ? q.split(/\s+/) : [];
    const st = $('#fltState').value, onlySet = $('#fltSet').checked, onlyDiff = $('#fltDiff').checked;
    return list.filter(e => {
      if (onlySet && !e.set) return false;
      if (onlyDiff && !differs(e)) return false;
      if (st) {
        const m = state.marks[e.id] || {};
        if (st === 'none' && (m.d || m.c)) return false;
        if (st === 'any' && !(m.d || m.c)) return false;
        if (st === 'comment' && !m.c) return false;
        if (['keep', 'change', 'ignore'].includes(st) && m.d !== st) return false;
      }
      if (toks.length) { const h = hay(e); for (const t of toks) if (!h.includes(t)) return false; }
      return true;
    });
  }

  // ── navigáció ────────────────────────────────────────────────────────
  let route = parseHash();
  function parseHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    const m = h.match(/^(c|v)=(.+)$/);
    if (m && m[1] === 'c' && catById.has(m[2])) return { c: m[2] };
    if (m && m[1] === 'v' && VIEWS.some(v => v.id === m[2])) return { v: m[2] };
    return { v: 'overview' };
  }
  function counts(list) { let n = 0; for (const e of list) if (isMarked(e)) n++; return n; }
  function renderNav() {
    const byCat = new Map();
    for (const e of E) { if (!byCat.has(e.cat)) byCat.set(e.cat, []); byCat.get(e.cat).push(e); }
    let h = '<h3>Nézetek</h3>';
    for (const v of VIEWS) {
      const list = v.f ? E.filter(v.f) : null;
      h += `<a href="#v=${v.id}" class="${route.v === v.id ? 'active' : ''}"><span>${esc(v.title)}</span>` +
        (list ? `<span class="n">${list.length}</span>` : '') + '</a>';
    }
    for (const g of C.groups) {
      h += `<h3>${esc(g.title)}</h3>`;
      for (const c of C.categories.filter(c => c.group === g.id)) {
        const list = byCat.get(c.id) || [];
        const n = counts(list);
        h += `<a href="#c=${esc(c.id)}" class="${route.c === c.id ? 'active' : ''}" title="${esc(c.desc)}">` +
          `<span>${esc(c.title)}</span><span class="n${n === list.length ? ' done' : ''}">${n}/${list.length}</span></a>`;
      }
    }
    $('#nav').innerHTML = h;
  }
  function renderStats() {
    let k = 0, c = 0, i = 0, cm = 0;
    for (const e of E) {
      const m = state.marks[e.id]; if (!m) continue;
      if (m.d === 'keep') k++; else if (m.d === 'change') c++; else if (m.d === 'ignore') i++;
      if (m.c) cm++;
    }
    $('#stats').innerHTML = `<b class="k">✔ ${k}</b> tartsd · <b class="c">✎ ${c}</b> változtasd · <b class="i">⊘ ${i}</b> nem érdekel · ` +
      `${E.length - k - c - i} jelöletlen${cm ? ` · ${cm} megjegyzés` : ''}`;
  }

  const LIMIT = 400;
  let shown = [];
  // nézetekben és keresésben kategóriánként egyben maradjanak a tételek (stabil rendezés)
  const catOrder = new Map(C.categories.map((c, i) => [c.id, i]));
  const byCatOrder = list => list.map((e, i) => [e, i])
    .sort((a, b) => (catOrder.get(a[0].cat) - catOrder.get(b[0].cat)) || (a[1] - b[1])).map(x => x[0]);
  function renderMain() {
    dlCounter = 0;
    const q = $('#search').value.trim();
    let title, desc, list, showCat = false, groupBy = e => e.group || '';
    if (q) {
      title = `Keresés: „${q}”`; desc = 'Találatok az összes kategóriában.';
      list = byCatOrder(filtered(E)); showCat = true;
      groupBy = e => { const c = catById.get(e.cat); return c ? groupTitle(c.group) + ' › ' + c.title : e.cat; };
    } else if (route.c) {
      const c = catById.get(route.c);
      title = `${groupTitle(c.group)} › ${c.title}`; desc = c.desc;
      list = filtered(E.filter(e => e.cat === route.c));
    } else {
      const v = VIEWS.find(x => x.id === route.v) || VIEWS[0];
      title = v.title;
      if (v.id === 'overview') { renderOverview(); return; }
      list = byCatOrder(filtered(E.filter(v.f))); showCat = true;
      groupBy = e => { const c = catById.get(e.cat); return c ? groupTitle(c.group) + ' › ' + c.title : e.cat; };
      desc = { presets: 'Amit már tudunk rólad; a jelölések ebből jönnek. Bármelyik átírható.',
        fonts: 'Minden betűvel kapcsolatos paraméter, mintaszöveggel. A minta a böngészőben telepített betűvel rajzol.',
        colors: 'Minden szín, színminta és séma egy helyen.',
        anim: 'Görbék és animációk. A görbe fölé víve az egeret a pötty a görbe szerint mozog.',
        changed: 'Ami a configban be van állítva és eltér az alapértéktől: ezek a mostani testreszabásaid.',
        marked: 'Amit eddig jelöltél vagy megjegyzéssel láttál el.' }[v.id] || '';
    }
    shown = list;
    const unmarked = list.filter(e => !(state.marks[e.id] || {}).d).length;
    let h = `<div class="cathead"><h2>${esc(title)}</h2><p>${md(desc || '')}</p></div>` +
      `<div class="bulk"><span>${list.length} paraméter látszik, ebből ${unmarked} jelöletlen.</span>` +
      (unmarked ? `<button type="button" data-bulk="keep">A látható jelöletlenek: Tartsd</button><button type="button" data-bulk="ignore">A látható jelöletlenek: Nem érdekel</button>` : '') + '</div>';
    if (!list.length) h += '<p class="empty">Nincs találat a szűrőkkel.</p>';
    let lastG = null;
    for (const e of list.slice(0, LIMIT)) {
      const g = groupBy(e);
      if (g !== lastG) { h += `<h4 class="groupname">${esc(g)}</h4>`; lastG = g; }
      h += card(e, showCat);
    }
    if (list.length > LIMIT) h += `<p class="more">… és még ${list.length - LIMIT}. Szűkítsd a keresést vagy válassz kategóriát.</p>`;
    main.innerHTML = h;
  }
  function renderOverview() {
    shown = [];
    const tpl = $('#help').content.cloneNode(true);
    main.innerHTML = '';
    const head = document.createElement('div');
    head.className = 'cathead';
    const src = C.sources || {};
    const hy = src.hyprland || {};
    head.innerHTML = `<h2>Áttekintés</h2><p>Profil: <code>${esc(C.profile)}</code> · generálva: ${esc(C.generated)} · ` +
      `${E.length} paraméter, ${C.categories.length} kategória · Hyprland ${esc(hy.version || '?')} (${esc(hy.live_source || '')})` +
      (storageOk ? '' : ' · <b style="color:var(--error)">a böngésző nem enged helyi mentést: exportálj gyakran!</b>') + '</p>';
    main.appendChild(head);
    main.appendChild(tpl);
    const notes = $('#globalNotes');
    notes.value = state.notes || '';
    notes.addEventListener('input', () => { state.notes = notes.value; save(); });
    const t = document.createElement('div');
    let h = '<h4 class="groupname">Kategóriák</h4><dl class="vals">';
    for (const g of C.groups) {
      const cats = C.categories.filter(c => c.group === g.id);
      const tot = cats.reduce((a, c) => a + c.count, 0);
      h += `<dt>${esc(g.title)}</dt><dd>${tot} — ` + cats.map(c => `<a href="#c=${esc(c.id)}">${esc(c.title)}</a> ${c.count}`).join(', ') + '</dd>';
    }
    h += '</dl>';
    t.innerHTML = h;
    main.appendChild(t);
  }
  function renderAll() { renderNav(); renderStats(); renderMain(); fitTop(); }
  // a fejléc magassága változhat (tördelés): ehhez igazodik a ragadós oldalsáv
  function fitTop() { document.documentElement.style.setProperty('--top', $('header.top').offsetHeight + 'px'); }
  window.addEventListener('resize', fitTop);

  function refreshCard(id, focusSel) {
    const el = main.querySelector(`article[data-id="${CSS.escape(id)}"]`);
    if (!el) return;
    const e = byId.get(id);
    const tmp = document.createElement('div');
    tmp.innerHTML = card(e, !!el.querySelector('.catname'));
    const nu = tmp.firstElementChild;
    if (el.classList.contains('c-open')) nu.classList.add('c-open');
    el.replaceWith(nu);
    if (focusSel) { const f = nu.querySelector(focusSel); if (f) f.focus(); }
  }

  // ── események ────────────────────────────────────────────────────────
  main.addEventListener('click', ev => {
    const bulk = ev.target.closest('[data-bulk]');
    if (bulk) {
      const d = bulk.dataset.bulk;
      const targets = shown.filter(e => !(state.marks[e.id] || {}).d);
      const label = d === 'keep' ? 'Tartsd' : 'Nem érdekel';
      if (!targets.length || !confirm(`${targets.length} látható, jelöletlen paraméter → „${label}”. Mehet?`)) return;
      for (const e of targets) setMark(e.id, { d });
      renderAll();
      return;
    }
    const art = ev.target.closest('article.item');
    if (!art) return;
    const id = art.dataset.id;
    const btn = ev.target.closest('button[data-d]');
    if (btn) {
      const d = btn.dataset.d;
      const cur = mark(id).d;
      setMark(id, { d: cur === d ? undefined : d });
      refreshCard(id, d === 'change' && cur !== d ? '[data-f=p]' : null);
      renderNav(); renderStats();
      return;
    }
    if (ev.target.closest('.ctoggle')) {
      art.classList.toggle('c-open');
      if (art.classList.contains('c-open')) { card.open.add(id); art.querySelector('textarea.comment').focus(); }
      else card.open.delete(id);
    }
  });
  main.addEventListener('input', ev => {
    const art = ev.target.closest('article.item');
    if (!art) return;
    const id = art.dataset.id;
    if (ev.target.matches('[data-f=p]')) { setMark(id, { p: ev.target.value }); }
    else if (ev.target.matches('textarea.comment')) {
      setMark(id, { c: ev.target.value });
      const t = art.querySelector('.ctoggle');
      t.classList.toggle('has', !!ev.target.value);
      t.textContent = 'Megjegyzés' + (ev.target.value ? ' ✓' : '');
      renderStats();
    }
  });
  main.addEventListener('change', ev => {
    if (ev.target.matches('select[data-f=p]')) setMark(ev.target.closest('article.item').dataset.id, { p: ev.target.value });
  });
  window.addEventListener('hashchange', () => { route = parseHash(); $('#search').value = ''; renderAll(); window.scrollTo(0, 0); });
  let qTimer;
  $('#search').addEventListener('input', () => { clearTimeout(qTimer); qTimer = setTimeout(renderMain, 150); });
  for (const id of ['#fltState', '#fltSet', '#fltDiff']) $(id).addEventListener('change', renderMain);
  document.addEventListener('keydown', ev => {
    if (ev.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { ev.preventDefault(); $('#search').focus(); }
  });

  // ── export / import / törlés ─────────────────────────────────────────
  function coerce(e, p) {
    if (p === undefined || p === null || p === '') return undefined;
    if (typeof p !== 'string') return p;
    const t = p.trim();
    if (e.type === 'bool') return t === 'true' ? true : t === 'false' ? false : t;
    if ((e.type === 'int' || e.type === 'float') && t !== '' && !isNaN(Number(t))) return Number(t);
    if (e.type === 'enum' && e.opts && Array.isArray(e.opts[0]) && t !== '' && !isNaN(Number(t))) return Number(t);
    if (['list', 'object', 'animation', 'curve', 'curve-qml', 'rule'].includes(e.type)) { try { return JSON.parse(t); } catch (_) { return t; } }
    return t;
  }
  function exportJson() {
    const items = [];
    const n = { keep: 0, change: 0, ignore: 0, commented: 0 };
    for (const e of E) {
      const m = state.marks[e.id];
      if (!m || (!m.d && !m.c)) continue;
      if (m.d) n[m.d]++;
      if (m.c) n.commented++;
      const c = catById.get(e.cat);
      const it = { id: e.id, source: e.id.split(':')[0], category: c ? `${groupTitle(c.group)} › ${c.title}` : e.cat,
        key: e.key, label: e.label || undefined, file: e.file || undefined, current: e.cur,
        default: 'def' in e ? e.def : undefined, decision: m.d || null };
      if (m.d === 'change') it.proposed = coerce(e, m.p) ?? null;
      if (m.c) it.comment = m.c;
      if (m.preset) it.preset = true;
      items.push(it);
    }
    const out = { format: 'rice-configurator/export-v1', exported: new Date().toISOString(),
      catalog: { generated: C.generated, hash: C.hash, profile: C.profile, total: E.length },
      counts: Object.assign(n, { unmarked: E.length - n.keep - n.change - n.ignore }),
      notes: state.notes || '', items };
    const blob = new Blob([JSON.stringify(out, null, 2) + '\n'], { type: 'application/json' });
    const a = document.createElement('a');
    const d = new Date(), pad = x => String(x).padStart(2, '0');
    a.href = URL.createObjectURL(blob);
    a.download = `rice-preferences-${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}.json`;
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
    flash(`Letöltve: ${items.length} tétel`);
  }
  async function importJson(file) {
    let data;
    try { data = JSON.parse(await file.text()); } catch (_) { alert('Nem érvényes JSON.'); return; }
    if (!data || data.format !== 'rice-configurator/export-v1' || !Array.isArray(data.items)) { alert('Ez nem rice-configurator export.'); return; }
    let ok = 0, unknown = 0;
    for (const it of data.items) {
      if (!byId.has(it.id)) { unknown++; continue; }
      const p = it.proposed === undefined || it.proposed === null ? undefined : (typeof it.proposed === 'string' ? it.proposed : JSON.stringify(it.proposed));
      state.marks[it.id] = { d: it.decision || undefined, p, c: it.comment || '', preset: !!it.preset };
      ok++;
    }
    if (data.notes) state.notes = data.notes;
    save(); renderAll();
    alert(`Betöltve: ${ok} tétel.` + (unknown ? ` ${unknown} azonosító már nincs a katalógusban, kimaradt.` : ''));
  }
  $('#btnExport').addEventListener('click', exportJson);
  $('#btnImport').addEventListener('click', () => $('#fileImport').click());
  $('#fileImport').addEventListener('change', ev => { const f = ev.target.files[0]; if (f) importJson(f); ev.target.value = ''; });
  $('#btnReset').addEventListener('click', () => {
    if (!confirm('Minden jelölés és megjegyzés törlődik ebből a böngészőből (az előjelölések visszaállnak). Előtte érdemes exportálni. Mehet?')) return;
    state = applyPresets(fresh()); save(); renderAll();
  });

  // ── indulás ──────────────────────────────────────────────────────────
  const dlf = document.createElement('datalist');
  dlf.id = 'dl-fonts';
  dlf.innerHTML = (C.fonts || []).map(f => `<option value="${esc(f)}"></option>`).join('');
  document.body.appendChild(dlf);
  $('#meta').textContent = `profil: ${C.profile} · ${E.length} paraméter · generálva ${C.generated.replace('T', ' ').replace('+00:00', ' UTC')}`;
  if (!storageOk) flash('Helyi mentés nem elérhető — exportálj!', true);
  save();
  renderAll();
})();
