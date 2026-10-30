/* Rice-stúdió — interaktív Hyprland dotfile-készítő élő előnézettel.
 * Függőség nélküli, file://-ról fut. Semmit nem ír a gépre a letöltésen kívül,
 * és NEM nyúl az élő confighoz. Hyprland-ÁLTALÁNOS (nem caelestia-specifikus).
 *
 * Modell: egy szűkített, de a dotfile-ok közt mély paraméterkészlet. Minden
 * paraméter tudja a saját Hyprland config-útját (pl. decoration:rounding),
 * így a .conf és .lua export is a valós kulcsokat írja. A vizuális előnézet
 * CSS-változókon keresztül frissül (a --r-* változók a studio.css-ben).
 */
'use strict';
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;

  /* ─────────────────────────────────────────────────────────────────────
   * PARAMÉTER-MODELL
   * Minden mező:
   *   id      egyedi
   *   hy      Hyprland config-út "szakasz:kulcs" (export), vagy null (csak UI)
   *   type    color | range | toggle | select | gradient | font | curve | wallpaper
   *   def     alapérték
   *   css     [cssVar, formázó(v)] — mit állítson az előnézeten (opcionális)
   *   apply   egyedi élő-frissítő (opcionális), a sima css helyett/mellett
   * ─────────────────────────────────────────────────────────────────── */

  const FONTS = ['Inter','Roboto','Cantarell','Noto Sans','Ubuntu','Fira Sans','system-ui',
    'JetBrains Mono','JetBrainsMono Nerd Font','Fira Code','Cascadia Code','monospace'];

  // segéd: hex → "rgb(rrggbb)" (Hyprland szín)
  const hex2hy = h => 'rgb(' + h.replace('#','').slice(0,6) + ')';
  const px = v => v + 'px';

  // színkulcsok, amelyek a palettát és a felületet adják
  const COLORS = [
    ['bg',        'Háttér',            '#1a1b26', '--r-bg',            null],
    ['surface',   'Felület',           '#24283b', '--r-surface',       null],
    ['surface2',  'Felület (magas)',   '#2f3449', '--r-surface2',      null],
    ['fg',        'Szöveg',            '#c0caf5', '--r-fg',            null],
    ['fg2',       'Szöveg (halvány)',  '#9aa5ce', '--r-fg2',           null],
    ['primary',   'Kiemelés',          '#7aa2f7', '--r-primary',       'general:col.active_border'],
    ['accent2',   'Másodlagos',        '#bb9af7', '--r-accent2',       null],
    ['accent3',   'Harmadlagos',       '#7dcfff', '--r-accent3',       null],
    ['error',     'Hiba / piros',      '#f7768e', '--r-error',         null],
  ];

  // A modell. A "group" a fül.
  const M = {
    // kulcs: aktuális érték (a state)
  };
  const DEFS = {};         // alapértékek
  const SPEC = {};         // paraméter-leírók
  const GROUPS = [
    { id:'theme',  title:'Téma & szín' },
    { id:'layout', title:'Elrendezés' },
    { id:'deco',   title:'Díszítés' },
    { id:'anim',   title:'Animáció' },
    { id:'type',   title:'Betűtípus' },
    { id:'wall',   title:'Háttér' },
  ];

  function def(id, spec) {
    SPEC[id] = spec;
    DEFS[id] = spec.def;
    M[id] = spec.def;
  }

  // ── TÉMA / SZÍN ──
  for (const [id, nm, d, cssVar, hy] of COLORS) {
    def('col.' + id, { group:'theme', type:'color', nm, def:d, cssVar, hy,
      cat:'A rendszer alapszínei. A kiemelés egyben az aktív ablak kerete is.' });
  }
  def('col.scheme', { group:'theme', type:'select', nm:'Színséma-generátor (caelestia/matugen)', def:'tonalspot',
    opts:['tonalspot','vibrant','expressive','fidelity','neutral','monochrome','content','rainbow'],
    hy:null, note:true, cat:'Csak megjegyzésként kerül az exportba — a tényleges sémagenerálást a téma-eszközöd (pl. caelestia/matugen) végzi.' });

  // ── ELRENDEZÉS ──
  def('gaps_in',  { group:'layout', type:'range', nm:'Belső rés (gaps_in)',  def:4, min:0, max:40, unit:'px',
    hy:'general:gaps_in', css:['--r-gap', px], cat:'Ablakok közötti és a bar körüli rés.' });
  def('gaps_out', { group:'layout', type:'range', nm:'Külső rés (gaps_out)', def:10, min:0, max:60, unit:'px',
    hy:'general:gaps_out', cat:'A képernyő széle és az ablakok közötti rés. Az előnézetben a belső réssel közösen látszik.' });
  def('border',   { group:'layout', type:'range', nm:'Keretvastagság (border_size)', def:2, min:0, max:12, unit:'px',
    hy:'general:border_size', css:['--r-border', px], cat:'Az ablakkeret vastagsága.' });
  def('layout',   { group:'layout', type:'seg', nm:'Elrendezés', def:'dwindle', opts:['dwindle','master'],
    hy:'general:layout', cat:'A csempézés algoritmusa.' });

  // ── DÍSZÍTÉS ──
  def('rounding',   { group:'deco', type:'range', nm:'Lekerekítés (rounding)', def:10, min:0, max:28, unit:'px',
    hy:'decoration:rounding', css:['--r-round', px], cat:'Az ablaksarkok lekerekítése.' });
  def('active_op',  { group:'deco', type:'range', nm:'Aktív átlátszatlanság', def:1, min:.5, max:1, step:.02,
    hy:'decoration:active_opacity', css:['--r-active-op', String], cat:'Az aktív ablak átlátszatlansága (1 = tömör).' });
  def('inactive_op',{ group:'deco', type:'range', nm:'Inaktív átlátszatlanság', def:.9, min:.4, max:1, step:.02,
    hy:'decoration:inactive_opacity', css:['--r-inactive-op', String], cat:'A háttérben lévő ablakok átlátszatlansága.' });
  def('blur_on',    { group:'deco', type:'toggle', nm:'Blur bekapcsolva', def:true, hy:'decoration:blur:enabled',
    cat:'Az átlátszó felületek mögötti elmosás.' });
  def('blur_size',  { group:'deco', type:'range', nm:'Blur erőssége (size)', def:6, min:1, max:20, unit:'px',
    hy:'decoration:blur:size', css:['--r-blur', px], cat:'A blur sugara. Az előnézet ezt közelíti.' });
  def('blur_passes',{ group:'deco', type:'range', nm:'Blur menetek (passes)', def:2, min:1, max:4,
    hy:'decoration:blur:passes', cat:'Több menet = simább, de drágább blur.' });
  def('shadow_on',  { group:'deco', type:'toggle', nm:'Árnyék bekapcsolva', def:true, hy:'decoration:shadow:enabled',
    cat:'Ablak alatti vetett árnyék.' });
  def('shadow_range',{ group:'deco', type:'range', nm:'Árnyék mérete (range)', def:16, min:0, max:60, unit:'px',
    hy:'decoration:shadow:range', cat:'Az árnyék kiterjedése.' });

  // ── ANIMÁCIÓ ──
  def('anim_on',  { group:'anim', type:'toggle', nm:'Animációk bekapcsolva', def:true, hy:'animations:enabled',
    cat:'A teljes Hyprland animációs motor.' });
  def('anim_speed',{ group:'anim', type:'range', nm:'Sebesség (idő)', def:4.2, min:1, max:10, step:.1, unit:'×100ms',
    hy:null, cat:'A fő animáció időtartama Hyprland-egységben (1 = 100 ms). Az export az animation sorokba írja.' });
  def('anim_curve',{ group:'anim', type:'curve', nm:'Görbe (bezier)', def:'easeOutQuint',
    hy:null, cat:'A mozgás karaktere. A görbe fölé víve a pötty aszerint mozog.' });

  // ── BETŰ ──
  def('font_ui',   { group:'type', type:'font', nm:'Felület betűje', def:'Inter',
    hy:null, css:['--r-font', f=>`'${f}', system-ui, sans-serif`],
    cat:'A bar és a felület betűje (a shell/GTK config használja; megjegyzésként is exportálódik).' });
  def('font_mono', { group:'type', type:'font', nm:'Monospace betű', def:'JetBrainsMono Nerd Font',
    hy:null, css:['--r-font-mono', f=>`'${f}', ui-monospace, monospace`],
    cat:'A terminál és a kód betűje.' });

  // ── HÁTTÉR ──
  def('wall_mode', { group:'wall', type:'seg', nm:'Háttér típusa', def:'gradient', opts:['solid','gradient'],
    hy:null, cat:'Tömör szín vagy kétszínű gradiens az előnézethez. (Képfájlt a wallpaper-eszközöd állít be.)' });
  def('wall_c1',   { group:'wall', type:'color', nm:'Háttér szín 1', def:'#1a1b26', hy:null, cat:'' });
  def('wall_c2',   { group:'wall', type:'color', nm:'Háttér szín 2', def:'#24283b', hy:null, cat:'' });
  def('wall_angle',{ group:'wall', type:'range', nm:'Gradiens szöge', def:135, min:0, max:360, unit:'°', hy:null, cat:'' });
  def('wall_path', { group:'wall', type:'text', nm:'Háttérkép útvonala (opcionális)', def:'', hy:null,
    cat:'Ha megadsz egy képet, az export egy exec-once sorba teszi (swww/hyprpaper). Az előnézet a fenti gradienst/színt mutatja.' });

  /* ─────────────────────────────────────────────────────────────────────
   * BEZIER GÖRBÉK (Hyprland-barát nevek → kontrollpontok)
   * ─────────────────────────────────────────────────────────────────── */
  const CURVES = {
    easeOutQuint:  [.23,1,.32,1],
    easeOutExpo:   [.16,1,.3,1],
    easeInOutCubic:[.65,0,.35,1],
    linear:        [0,0,1,1],
    overshoot:     [.05,.9,.1,1.1],
    snappy:        [.2,.9,.1,1],
    gentle:        [.25,.1,.25,1],
  };

  /* ─────────────────────────────────────────────────────────────────────
   * KIINDULÁSI STÍLUSOK (preset) — NEM Material-3-Expressive, változatos irányok
   * ─────────────────────────────────────────────────────────────────── */
  const PRESETS = {
    tokyonight: { nm:'Tokyo Night', d:'Lágy, kékes, mély kontraszt', vals:{
      'col.bg':'#1a1b26','col.surface':'#24283b','col.surface2':'#2f3449','col.fg':'#c0caf5','col.fg2':'#9aa5ce',
      'col.primary':'#7aa2f7','col.accent2':'#bb9af7','col.accent3':'#7dcfff','col.error':'#f7768e',
      rounding:10,border:2,gaps_in:4,gaps_out:10,blur_on:true,blur_size:7,shadow_on:true,
      wall_mode:'gradient',wall_c1:'#1a1b26',wall_c2:'#2f3449',wall_angle:135,anim_curve:'easeOutQuint' }},
    gruvbox: { nm:'Gruvbox melegház', d:'Retro, meleg, lapos', vals:{
      'col.bg':'#282828','col.surface':'#3c3836','col.surface2':'#504945','col.fg':'#ebdbb2','col.fg2':'#a89984',
      'col.primary':'#fabd2f','col.accent2':'#fe8019','col.accent3':'#8ec07c','col.error':'#fb4934',
      rounding:4,border:3,gaps_in:6,gaps_out:12,blur_on:false,shadow_on:false,
      wall_mode:'solid',wall_c1:'#282828',anim_curve:'gentle',font_ui:'Ubuntu' }},
    nord: { nm:'Nord fagyos', d:'Hideg, visszafogott, letisztult', vals:{
      'col.bg':'#2e3440','col.surface':'#3b4252','col.surface2':'#434c5e','col.fg':'#eceff4','col.fg2':'#d8dee9',
      'col.primary':'#88c0d0','col.accent2':'#81a1c1','col.accent3':'#8fbcbb','col.error':'#bf616a',
      rounding:8,border:1,gaps_in:5,gaps_out:14,blur_on:true,blur_size:5,shadow_on:true,
      wall_mode:'gradient',wall_c1:'#2e3440',wall_c2:'#434c5e',wall_angle:160,anim_curve:'easeInOutCubic' }},
    neon: { nm:'Cyber neon', d:'Sötét, erős neon kiemelés, nagy glow', vals:{
      'col.bg':'#0d0221','col.surface':'#190a38','col.surface2':'#241048','col.fg':'#e6e6ff','col.fg2':'#9a8cff',
      'col.primary':'#ff2e97','col.accent2':'#00f0ff','col.accent3':'#b24bff','col.error':'#ff4365',
      rounding:14,border:2,gaps_in:6,gaps_out:16,blur_on:true,blur_size:12,blur_passes:3,shadow_on:true,shadow_range:30,
      wall_mode:'gradient',wall_c1:'#0d0221','wall_c2':'#2a0a4a',wall_angle:120,anim_curve:'overshoot',anim_speed:5.5 }},
    paper: { nm:'Papír (világos)', d:'Világos, minimál, kevés díszítés', vals:{
      'col.bg':'#f4f1ea','col.surface':'#eae6dc','col.surface2':'#dcd7ca','col.fg':'#2b2b2b','col.fg2':'#6b6b6b',
      'col.primary':'#3b6ea5','col.accent2':'#a5683b','col.accent3':'#3b8a6e','col.error':'#b5443b',
      rounding:6,border:1,gaps_in:6,gaps_out:14,blur_on:false,shadow_on:true,shadow_range:10,
      wall_mode:'solid',wall_c1:'#f4f1ea',anim_curve:'gentle',anim_speed:3.2,font_ui:'Noto Sans' }},
    brutalist: { nm:'Brutalist', d:'Éles sarkok, vastag keret, nulla blur', vals:{
      'col.bg':'#111111','col.surface':'#1c1c1c','col.surface2':'#2a2a2a','col.fg':'#f2f2f2','col.fg2':'#8a8a8a',
      'col.primary':'#e8ff00','col.accent2':'#ff5500','col.accent3':'#00e5ff','col.error':'#ff0033',
      rounding:0,border:4,gaps_in:0,gaps_out:8,blur_on:false,shadow_on:false,active_op:1,inactive_op:1,
      wall_mode:'solid',wall_c1:'#111111',anim_curve:'snappy',anim_speed:2.5,font_ui:'JetBrains Mono' }},
  };

  /* ─────────────────────────────────────────────────────────────────────
   * ÁLLAPOT betöltés/mentés (localStorage; nem kötelező)
   * ─────────────────────────────────────────────────────────────────── */
  const STORE = 'rice-studio/v1';
  function load() {
    try {
      const s = JSON.parse(localStorage.getItem(STORE) || 'null');
      if (s && typeof s === 'object') for (const k of Object.keys(M)) if (k in s) M[k] = s[k];
    } catch (_) {}
  }
  let saveT;
  function save() { clearTimeout(saveT); saveT = setTimeout(() => { try { localStorage.setItem(STORE, JSON.stringify(M)); } catch (_) {} }, 200); }

  /* ─────────────────────────────────────────────────────────────────────
   * ÉLŐ ELŐNÉZET FRISSÍTÉSE
   * ─────────────────────────────────────────────────────────────────── */
  function cur(id) { return M[id]; }
  function isDiff(id) { return JSON.stringify(M[id]) !== JSON.stringify(DEFS[id]); }

  function applyAll() {
    // minden olyan paraméter, amelynek van css/apply utasítása
    for (const id of Object.keys(SPEC)) {
      const sp = SPEC[id];
      if (sp.css) { const [v, fmt] = sp.css; root.style.setProperty(v, fmt(M[id])); }
    }
    // keretszín = kiemelés
    root.style.setProperty('--r-border-active', M['col.primary']);
    root.style.setProperty('--r-border-inactive', M['col.surface2']);
    // paletta-csík
    const pal = $('#palStrip');
    if (pal) pal.innerHTML = ['col.primary','col.accent2','col.accent3','col.error','col.fg','col.surface2']
      .map(k => `<span style="background:${M[k]}"></span>`).join('');
    // blur ki → 0
    root.style.setProperty('--r-blur', M.blur_on ? px(M.blur_size) : '0px');
    // árnyék
    root.style.setProperty('--r-shadow', M.shadow_on
      ? `0 ${Math.round(M.shadow_range/2)}px ${M.shadow_range}px rgba(0,0,0,.5)` : 'none');
    // átlátszatlanság (blur ki esetén is tömör maradjon vizuálisan ne, de opacity marad)
    // háttér
    let wall;
    if (M.wall_mode === 'solid') wall = M.wall_c1;
    else wall = `linear-gradient(${M.wall_angle}deg, ${M.wall_c1}, ${M.wall_c2})`;
    root.style.setProperty('--r-wall', wall);
    $('#wp').style.background = wall;
    // wallpaper címke
    $('#wpTag').textContent = M.wall_path ? M.wall_path.split('/').pop() : (M.wall_mode === 'solid' ? 'tömör szín' : 'gradiens');
    // animáció görbe + idő
    const c = CURVES[M.anim_curve] || CURVES.easeOutQuint;
    const clamp = n => Math.max(-.2, Math.min(1.2, n));
    root.style.setProperty('--r-ease', `cubic-bezier(${c.map(clamp).join(',')})`);
    root.style.setProperty('--r-dur', (M.anim_on ? Math.round(M.anim_speed * 100) : 0) + 'ms');
    // betűminta
    $('#fontSample').style.fontFamily = `'${M.font_ui}', system-ui, sans-serif`;
    $('#fontSample').textContent = 'Árvíztűrő tükörfúrógép ' + M.font_ui;
    // dirty jelző
    const n = Object.keys(SPEC).filter(isDiff).length;
    $('#dirtyHint').textContent = n ? `${n} paraméter eltér az alapértéktől` : 'minden alapértéken';
    save();
  }

  function replay() {
    if (!M.anim_on || !$('#tglLive').checked) return;
    const el = $('#animDemo');
    el.classList.remove('play'); void el.offsetWidth; el.classList.add('play');
    // ablak "újrarajzol" pulzus
    for (const w of ['#winA','#winC']) {
      const e = $(w); e.style.transition='none'; e.style.transform='scale(.985)';
      requestAnimationFrame(()=>{ e.style.transition=''; e.style.transform=''; });
    }
  }

  /* ─────────────────────────────────────────────────────────────────────
   * VEZÉRLŐK RENDERELÉSE
   * ─────────────────────────────────────────────────────────────────── */
  let activeGroup = 'theme';

  function renderTabs() {
    $('#tabs').innerHTML = GROUPS.map(g =>
      `<button data-g="${g.id}" class="${g.id===activeGroup?'on':''}">${g.title}</button>`).join('');
  }

  function ctlRange(id, sp) {
    const v = cur(id), step = sp.step || 1;
    return `<div class="ctl" data-id="${id}">
      <div class="lab"><span class="nm">${sp.nm}</span>
        <span class="vv ${isDiff(id)?'diff':''}">${fmtVal(id)}</span></div>
      <input type="range" min="${sp.min}" max="${sp.max}" step="${step}" value="${v}">
    </div>`;
  }
  function ctlColor(id, sp) {
    return `<div class="ctl" data-id="${id}">
      <div class="colorrow">
        <input type="color" value="${cur(id)}">
        <span class="cnm">${sp.nm}</span>
        <span class="chex">${cur(id)}</span>
      </div></div>`;
  }
  function ctlToggle(id, sp) {
    return `<div class="ctl" data-id="${id}"><div class="toggle">
      <span class="tt">${sp.nm}</span>
      <button class="sw ${cur(id)?'on':''}" role="switch" aria-checked="${cur(id)}"></button>
    </div></div>`;
  }
  function ctlSeg(id, sp) {
    return `<div class="ctl" data-id="${id}">
      <div class="lab"><span class="nm">${sp.nm}</span></div>
      <div class="seg">${sp.opts.map(o=>`<button data-v="${o}" class="${cur(id)===o?'on':''}">${o}</button>`).join('')}</div>
    </div>`;
  }
  function ctlSelect(id, sp) {
    return `<div class="ctl" data-id="${id}">
      <div class="lab"><span class="nm">${sp.nm}</span></div>
      <select>${sp.opts.map(o=>`<option ${cur(id)===o?'selected':''}>${o}</option>`).join('')}</select>
    </div>`;
  }
  function ctlFont(id, sp) {
    return `<div class="ctl" data-id="${id}">
      <div class="lab"><span class="nm">${sp.nm}</span><span class="vv">${cur(id)}</span></div>
      <input type="text" list="dl-fonts" value="${cur(id)}">
    </div>`;
  }
  function ctlText(id, sp) {
    return `<div class="ctl" data-id="${id}">
      <div class="lab"><span class="nm">${sp.nm}</span></div>
      <input type="text" value="${cur(id)}" placeholder="pl. ~/Pictures/wall.png">
    </div>`;
  }
  function ctlCurve(id, sp) {
    const names = Object.keys(CURVES);
    const svg = curveSvg(CURVES[cur(id)] || CURVES.easeOutQuint);
    return `<div class="ctl" data-id="${id}">
      <div class="lab"><span class="nm">${sp.nm}</span><span class="vv">${cur(id)}</span></div>
      <div style="display:flex;gap:12px;align-items:center">
        <span class="curvebox">${svg}</span>
        <select style="flex:1">${names.map(n=>`<option ${cur(id)===n?'selected':''}>${n}</option>`).join('')}</select>
      </div>
    </div>`;
  }
  function curveSvg(c) {
    const W=56,H=56,p=6, X=x=>(p+x*(W-2*p)).toFixed(1), Y=y=>(H-p-y*(H-2*p)).toFixed(1);
    const d=`M ${X(0)} ${Y(0)} C ${X(c[0])} ${Y(c[1])} ${X(c[2])} ${Y(c[3])} ${X(1)} ${Y(1)}`;
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
      <line x1="${X(0)}" y1="${Y(0)}" x2="${X(1)}" y2="${Y(0)}" stroke="var(--ui-line)"/>
      <path d="${d}" fill="none" stroke="var(--ui-acc)" stroke-width="2"/></svg>`;
  }

  function fmtVal(id) {
    const sp = SPEC[id], v = cur(id);
    if (sp.type === 'range') {
      if (sp.unit === 'px') return v + ' px';
      if (sp.unit === '°') return v + '°';
      if (sp.unit) return v + ' ' + sp.unit;
      return String(v);
    }
    return String(v);
  }

  const RENDER = { range:ctlRange, color:ctlColor, toggle:ctlToggle, seg:ctlSeg,
    select:ctlSelect, font:ctlFont, text:ctlText, curve:ctlCurve };

  function renderControls() {
    const ids = Object.keys(SPEC).filter(id => SPEC[id].group === activeGroup);
    const g = GROUPS.find(x => x.id === activeGroup);
    let h = `<div class="sect"><h3>${g.title}</h3>`;
    // csoport-leírás az első paraméterből? inkább fix:
    const GDESC = { theme:'A paletta és a felületek színe. A kiemelés egyben az aktív ablak kerete.',
      layout:'Rések, keret, csempézés — a kompozíció alapja.',
      deco:'Lekerekítés, átlátszóság, blur és árnyék.',
      anim:'A mozgás karaktere és sebessége.',
      type:'A felület és a terminál betűje.',
      wall:'A háttér az előnézethez; képfájl esetén exec-once sor az exportban.' };
    h += `<p class="sh-desc">${GDESC[activeGroup]||''}</p>`;
    for (const id of ids) h += (RENDER[SPEC[id].type] || (()=>''))(id, SPEC[id]);
    h += '</div>';
    $('#controls').innerHTML = h;
  }

  /* ─────────────────────────────────────────────────────────────────────
   * ESEMÉNYEK
   * ─────────────────────────────────────────────────────────────────── */
  function setVal(id, v) { M[id] = v; applyAll(); updateCtl(id); if (SPEC[id].group==='anim') replay(); }

  function updateCtl(id) {
    // frissítsük a kis értékjelzőt és a diff-színt a kártyán
    const el = $(`.ctl[data-id="${CSS.escape(id)}"]`);
    if (!el) return;
    const vv = el.querySelector('.vv'); if (vv) { vv.textContent = fmtVal(id); vv.classList.toggle('diff', isDiff(id)); }
    const chex = el.querySelector('.chex'); if (chex) chex.textContent = cur(id);
  }

  $('#tabs').addEventListener('click', e => {
    const b = e.target.closest('button[data-g]'); if (!b) return;
    activeGroup = b.dataset.g; renderTabs(); renderControls();
  });

  $('#controls').addEventListener('input', e => {
    const el = e.target.closest('.ctl'); if (!el) return;
    const id = el.dataset.id, sp = SPEC[id], t = e.target;
    if (t.type === 'range') setVal(id, sp.step ? parseFloat(t.value) : parseInt(t.value,10));
    else if (t.type === 'color') setVal(id, t.value);
    else if (t.type === 'text') setVal(id, t.value);
    else if (t.tagName === 'SELECT') {
      setVal(id, t.value);
      if (sp.type === 'curve') { el.querySelector('.curvebox').innerHTML = curveSvg(CURVES[t.value]); }
    }
  });
  $('#controls').addEventListener('click', e => {
    const el = e.target.closest('.ctl'); if (!el) return;
    const id = el.dataset.id, sp = SPEC[id];
    if (e.target.classList.contains('sw')) { setVal(id, !cur(id)); e.target.classList.toggle('on', cur(id)); e.target.setAttribute('aria-checked', cur(id)); }
    const seg = e.target.closest('.seg button');
    if (seg) { setVal(id, seg.dataset.v); $$('.seg button', el).forEach(b=>b.classList.toggle('on', b.dataset.v===cur(id))); }
  });

  $('#btnReplay').addEventListener('click', replay);
  $('#tglLive').addEventListener('change', () => { if ($('#tglLive').checked) replay(); });

  $('#btnReset').addEventListener('click', () => {
    if (!confirm('Minden paraméter vissza az alapértékre?')) return;
    for (const k of Object.keys(DEFS)) M[k] = DEFS[k];
    applyAll(); renderControls();
  });

  /* ─────────────────────────────────────────────────────────────────────
   * EXPORT
   * ─────────────────────────────────────────────────────────────────── */
  function changedSpecs(onlyChanged) {
    return Object.keys(SPEC).filter(id => SPEC[id].hy && (!onlyChanged || isDiff(id)));
  }
  // Hyprland "szakasz:kulcs" → fa, hogy conf/lua blokkokba lehessen írni
  function buildTree(ids) {
    const tree = {};
    for (const id of ids) {
      const sp = SPEC[id];
      const path = sp.hy.split(':');       // pl. decoration, blur, size
      let node = tree;
      for (let i = 0; i < path.length - 1; i++) node = (node[path[i]] = node[path[i]] || {});
      node['__leaf_' + path[path.length-1]] = exportVal(id);
    }
    return tree;
  }
  function exportVal(id) {
    const sp = SPEC[id], v = M[id];
    if (sp.type === 'toggle') return { kind:'bool', v: v ? 'true' : 'false' };
    if (sp.type === 'color') {
      if (sp.hy && sp.hy.endsWith('col.active_border')) return { kind:'gradient', v: hex2hy(v) + ' ' + hex2hy(shade(v,-30)) + ' 45deg' };
      return { kind:'color', v: hex2hy(v) };
    }
    if (sp.type === 'range' && (sp.unit === 'px' || !sp.unit)) return { kind:'num', v: v };
    if (sp.type === 'range') return { kind:'num', v: v };
    return { kind:'str', v: v };
  }
  function shade(hex, amt) {
    const n = parseInt(hex.slice(1,7),16);
    const r = Math.max(0,Math.min(255,(n>>16)+amt)), g=Math.max(0,Math.min(255,((n>>8)&255)+amt)), b=Math.max(0,Math.min(255,(n&255)+amt));
    return '#' + ((r<<16)|(g<<8)|b).toString(16).padStart(6,'0');
  }

  function leafVal(leaf) { // leaf = {kind, v}
    return leaf.v;
  }

  function emitConf(tree, indent='') {
    let out = '';
    for (const k of Object.keys(tree)) {
      if (k.startsWith('__leaf_')) {
        const key = k.slice(7); const leaf = tree[k];
        out += `${indent}${key} = ${leafVal(leaf)}\n`;
      }
    }
    for (const k of Object.keys(tree)) {
      if (k.startsWith('__leaf_')) continue;
      out += `${indent}${k} {\n` + emitConf(tree[k], indent + '    ') + `${indent}}\n`;
    }
    return out;
  }

  function animationLines() {
    const ms = Math.round(M.anim_speed * 10) / 10; // Hyprland idő (×100ms) marad
    const c = CURVES[M.anim_curve] || CURVES.easeOutQuint;
    const clamp = n => Math.max(0, Math.min(1, n)); // Hyprland bezier 0..1
    const bez = `bezier = ricecurve, ${c.map(clamp).map(x=>x.toFixed(2)).join(', ')}`;
    const spd = (M.anim_speed).toFixed(1);
    return { bez, lines: [
      `animation = windows, 1, ${spd}, ricecurve`,
      `animation = windowsOut, 1, ${spd}, ricecurve, popin 80%`,
      `animation = fade, 1, ${(M.anim_speed*0.7).toFixed(1)}, ricecurve`,
      `animation = workspaces, 1, ${spd}, ricecurve`,
      `animation = border, 1, ${(M.anim_speed*0.6).toFixed(1)}, ricecurve`,
    ]};
  }

  function buildConf(onlyChanged) {
    const ids = changedSpecs(onlyChanged);
    const tree = buildTree(ids);
    let out = `# Rice-stúdió export — Hyprland .conf\n# Generálva: ${new Date().toISOString()}\n`;
    out += `# Másold a megfelelő helyre (pl. hyprland.conf vagy egy appearance részfájl).\n`;
    out += `# Ez NEM írta felül az élő configot.\n\n`;
    out += emitConf(tree).replace(/\n{3,}/g,'\n\n');
    // animáció
    if (!onlyChanged || isDiff('anim_speed') || isDiff('anim_curve') || isDiff('anim_on')) {
      const a = animationLines();
      out += `\nanimations {\n    enabled = ${M.anim_on?'true':'false'}\n    ${a.bez}\n`;
      for (const l of a.lines) out += `    ${l}\n`;
      out += `}\n`;
    }
    // betű + séma + wallpaper megjegyzésként / exec
    out += commentBlock('#');
    return out.trim() + '\n';
  }

  function commentBlock(c) {
    let out = `\n${c} ── nem Hyprland-kulcsok (a téma-/betű-/háttéreszközöd állítja) ──\n`;
    out += `${c} UI betű:        ${M.font_ui}\n`;
    out += `${c} Monospace betű: ${M.font_mono}\n`;
    out += `${c} Színséma mód:   ${M['col.scheme']}\n`;
    out += `${c} Paletta: primary=${hex2hy(M['col.primary'])} bg=${hex2hy(M['col.bg'])} surface=${hex2hy(M['col.surface'])} fg=${hex2hy(M['col.fg'])}\n`;
    if (M.wall_path) out += `\nexec-once = swww img ${M.wall_path}   ${c} vagy: hyprpaper / a wallpaper-eszközöd\n`;
    return out;
  }

  function buildLua(onlyChanged) {
    const ids = changedSpecs(onlyChanged);
    let out = `-- Rice-stúdió export — Hyprland .lua (hyprlang-lua)\n-- Generálva: ${new Date().toISOString()}\n`;
    out += `-- A hl.* API a hyprlang-lua pluginé. Illeszd a .lua forrásodba.\n`;
    out += `-- Ez NEM írta felül az élő configot.\n\nlocal hl = require("hyprland")\n\n`;
    // keyword-stílusú beállítások: hl.config{ section = { key = value } }
    const tree = buildTree(ids);
    out += 'hl.config({\n' + emitLua(tree, '    ') + '})\n';
    if (!onlyChanged || isDiff('anim_speed') || isDiff('anim_curve') || isDiff('anim_on')) {
      const a = animationLines();
      const c = (CURVES[M.anim_curve]||CURVES.easeOutQuint).map(x=>Math.max(0,Math.min(1,x)).toFixed(2)).join(', ');
      out += `\nhl.bezier({ name = "ricecurve", points = { ${c} } })\n`;
      out += `hl.config({ animations = { enabled = ${M.anim_on?'true':'false'} } })\n`;
      for (const l of a.lines) {
        const m = l.match(/^animation = (.+)$/);
        if (m) out += `hl.animation("${m[1].replace(/"/g,'\\"')}")\n`;
      }
    }
    out += commentBlock('--');
    return out.trim() + '\n';
  }
  function luaVal(leaf) {
    if (leaf.kind === 'bool') return leaf.v;
    if (leaf.kind === 'num') return String(leaf.v);
    return `"${String(leaf.v).replace(/"/g,'\\"')}"`;
  }
  function emitLua(tree, indent) {
    let out = '';
    const leaves = Object.keys(tree).filter(k=>k.startsWith('__leaf_'));
    const subs = Object.keys(tree).filter(k=>!k.startsWith('__leaf_'));
    for (const k of leaves) { const key=k.slice(7); out += `${indent}["${key}"] = ${luaVal(tree[k])},\n`; }
    for (const k of subs) { out += `${indent}${/^[a-zA-Z_]\w*$/.test(k)?k:`["${k}"]`} = {\n` + emitLua(tree[k], indent+'    ') + `${indent}},\n`; }
    return out;
  }

  function buildJson(onlyChanged) {
    const items = {};
    for (const id of Object.keys(SPEC)) {
      if (onlyChanged && !isDiff(id)) continue;
      items[id] = { value:M[id], default:DEFS[id], hy:SPEC[id].hy || null };
    }
    return JSON.stringify({ format:'rice-studio/v1', generated:new Date().toISOString(), items }, null, 2);
  }

  const dlgEx = $('#dlgExport');
  function refreshExport() {
    const fmt = (new FormData($('#dlgExport form')).get('fmt'));
    const only = $('#exOnlyChanged').checked;
    const txt = fmt === 'lua' ? buildLua(only) : fmt === 'json' ? buildJson(only) : buildConf(only);
    $('#exOut').value = txt;
  }
  $('#btnExport').addEventListener('click', () => { dlgEx.showModal(); refreshExport(); });
  dlgEx.addEventListener('change', e => { if (e.target.name==='fmt' || e.target.id==='exOnlyChanged') refreshExport(); });
  $('#btnCopy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('#exOut').value); $('#btnCopy').textContent='Másolva ✓'; setTimeout(()=>$('#btnCopy').textContent='Vágólapra',1200); }
    catch(_){ $('#exOut').select(); document.execCommand('copy'); }
  });
  $('#btnDownload').addEventListener('click', () => {
    const fmt = (new FormData($('#dlgExport form')).get('fmt'));
    const ext = fmt === 'lua' ? 'lua' : fmt === 'json' ? 'json' : 'conf';
    const name = `rice-${stamp()}.${ext}`;
    const blob = new Blob([$('#exOut').value], { type:'text/plain' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href), 1000);
  });
  function stamp() { const d=new Date(),p=n=>String(n).padStart(2,'0'); return `${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`; }

  /* ─────────────────────────────────────────────────────────────────────
   * PRESETEK
   * ─────────────────────────────────────────────────────────────────── */
  function renderPresets() {
    $('#presetGrid').innerHTML = Object.entries(PRESETS).map(([k,p]) => {
      const v = p.vals;
      const sw = ['col.bg','col.primary','col.accent2','col.accent3','col.fg']
        .map(c => `<span style="background:${v[c]||M[c]}"></span>`).join('');
      return `<button type="button" class="preset-card" data-p="${k}">
        <div class="preset-sw">${sw}</div>
        <div class="pc-nm">${p.nm}</div><div class="pc-d">${p.d}</div></button>`;
    }).join('');
  }
  $('#btnPreset').addEventListener('click', () => { renderPresets(); $('#dlgPreset').showModal(); });
  $('#presetGrid').addEventListener('click', e => {
    const b = e.target.closest('.preset-card'); if (!b) return;
    const p = PRESETS[b.dataset.p]; if (!p) return;
    for (const [k,v] of Object.entries(p.vals)) if (k in M) M[k] = v;
    applyAll(); renderControls(); $('#dlgPreset').close(); replay();
  });

  /* ─────────────────────────────────────────────────────────────────────
   * INDÍTÁS
   * ─────────────────────────────────────────────────────────────────── */
  function boot() {
    // font datalist
    const dl = document.createElement('datalist'); dl.id = 'dl-fonts';
    dl.innerHTML = FONTS.map(f=>`<option value="${f}">`).join('');
    document.body.appendChild(dl);
    // óra
    const clk = $('#barClock'); const tick = () => { const d=new Date(); clk.textContent = String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); };
    tick(); setInterval(tick, 30000);
    load();
    renderTabs(); renderControls(); applyAll();
    setTimeout(replay, 300);
    $('#animDemo').addEventListener('click', replay);
  }
  boot();
})();
