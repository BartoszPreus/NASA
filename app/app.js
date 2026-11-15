// Written with SI assistance (Codex; J36 layers, strict switch and extra data with Claude Code).
// Leaflet 1.9.4: https://leafletjs.com/install.html
import {element, number, badges, showSite, showCriteria} from './views.js';
import {showMoon, showEvidence} from './sections.js';
import {strictSites, strictSiteCard, strictAbout} from './strict.js';

const byId = (id) => document.getElementById(id);
const atlas = byId('atlas');
const status = byId('load-status');
const stops = [[0, 34, 78], [67, 78, 108], [125, 124, 120], [188, 173, 108], [254, 232, 56]];
// Okabe-Ito colours (colour-blind safe) for the known-analog tags; each tag also has its own dash pattern.
const tagStyle = {
  moon: {color: '#56B4E9', dashArray: null},
  mars: {color: '#E69F00', dashArray: '6 4'},
  both: {color: '#CC79A7', dashArray: '2 3'},
};

async function json(path) {
  async function read() {
    const response = await fetch(path, {signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  }
  try {
    try {
      return await read();
    } catch (error) {
      if (error instanceof TypeError || error.name === 'TimeoutError') return await read();
      throw error;
    }
  } catch (error) {
    throw new Error(`${path}: ${error.message}`, {cause: error});
  }
}

// Files the page can work without: a failure is named on the page and the block that needs it says so.
async function optional(paths) {
  const results = await Promise.allSettled(paths.map((path) => json(path)));
  const failed = results.filter((r) => r.status === 'rejected').map((r) => r.reason.message);
  return {values: results.map((r) => r.status === 'fulfilled' ? r.value : null), failed};
}

function leaflet() {
  return new Promise((resolve, reject) => {
    function load(src, integrity) {
      const script = element('script');
      script.src = src;
      if (integrity) {
        script.integrity = integrity;
        script.crossOrigin = 'anonymous';
      }
      script.onload = () => window.L ? resolve(window.L) : reject(Error(`${src} did not expose Leaflet`));
      script.onerror = () => {
        if (integrity) load('vendor/leaflet.js');
        else reject(Error(`${src} could not be loaded`));
      };
      document.head.append(script);
    }
    load('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=');
  });
}

function tileColor(value, max) {
  if (value === null) return '#78878c';
  const scaled = max > 0 ? Math.min(1, value / max) * (stops.length - 1) : 0;
  const lower = Math.floor(scaled);
  const upper = Math.min(lower + 1, stops.length - 1);
  const offset = scaled - lower;
  return `rgb(${stops[lower].map((channel, i) => Math.round(channel + offset * (stops[upper][i] - channel))).join(',')})`;
}

function createMap(L, land, tiles, max) {
  const map = L.map('map', {zoomSnap: 0.25, maxZoom: 13, minZoom: 0.75});
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution('<a href="https://www.naturalearthdata.com/">Natural Earth</a>');
  const reset = () => map.fitBounds([[-61, -179], [84, 179]], {padding: [12, 10], animate: false});
  L.geoJSON(land, {interactive: false, style: {color: '#5b7482', weight: 0.65, fillColor: '#2e4b5b', fillOpacity: 1}}).addTo(map);
  const tileLayer = L.featureGroup().addTo(map);
  for (const t of tiles) {
    const bounds = [[t.lat0, t.lon0], [t.lat0 + 1, t.lon0 + 1]];
    const color = tileColor(t.candidate_share, max);
    const note = t.candidate_share === null ? 'No bare ground' : `${number(t.candidate_share * 100)}% candidate share`;
    const tooltip = element('span', `${t.id} · ${note} · ${number(t.bare)} bare cells · ${number(t.candidate)} candidate cells · ${number(t.sites)} patches`);
    L.rectangle(bounds, {className: 'survey-tile', color: '#74929d', weight: 0.4, fillColor: color, fillOpacity: 0.85})
      .bindTooltip(tooltip).addTo(tileLayer);
  }
  const markers = L.featureGroup().addTo(map);
  const selected = L.featureGroup().addTo(map);
  byId('reset-map').addEventListener('click', reset);
  reset();
  return {map, markers, selected};
}

function knownLayers(L, known) {
  const layers = {};
  for (const tag of Object.keys(tagStyle)) layers[tag] = L.featureGroup();
  for (const row of known?.rows || []) {
    const style = tagStyle[row.analog_for];
    if (!style) continue;
    const label = element('span', `${row.name} · ${row.analog_for_label}${row.operational ? ' · operational station, not counted as a known analog site' : ''}` +
      (row.radius_km == null ? ' · no radius listed' : ` · radius ${number(row.radius_km)} km`));
    const options = {className: 'known-analog', color: style.color, dashArray: style.dashArray, weight: 1.6, fill: false};
    const shape = row.radius_km == null ? L.circleMarker([row.lat, row.lon], {...options, radius: 5}) :
      L.circle([row.lat, row.lon], {...options, radius: row.radius_km * 1000});
    shape.bindTooltip(label).addTo(layers[row.analog_for]);
  }
  return layers;
}

function controlLayer(L, controls) {
  const layer = L.featureGroup();
  for (const t of controls?.tiles || []) {
    const kind = t.control ? 'negative control' : (t.known ? 'pilot tile at a known analog' : 'pilot tile');
    let text = `${t.tile} · ${t.label} · ${kind}`;
    if (t.result) {
      text += ` · with mask ${number(t.result.with_mask.cells, 0)} cells, ${number(t.result.with_mask.sites, 0)} patches` +
        ` · without mask ${number(t.result.without_mask.cells, 0)} cells, ${number(t.result.without_mask.sites, 0)} patches · ${t.result_key}`;
    }
    L.rectangle([[t.lat0, t.lon0], [t.lat0 + 1, t.lon0 + 1]], {className: 'control-tile', color: t.control ? '#ffffff' : '#009E73',
      weight: 2, dashArray: t.control ? '4 3' : null, fill: false}).bindTooltip(element('span', text)).addTo(layer);
  }
  return layer;
}

function siteRow(site, target, selected, onSelect, strict) {
  const row = element('button', null, 'rank-row');
  row.type = 'button';
  row.dataset.site = site.site_id;
  row.setAttribute('aria-pressed', String(site === selected));
  const score = strict ? `Score ${number(site.score, 3)} (pooled target)` : `Terrain score ${number(site.region_scores[target], 3)}`;
  row.append(
    element('span', `#${site.rank}`, 'rank-number'),
    element('strong', site.place || site.country || site.site_id),
    element('span', `${number(site.best_window_km2)} km²`, 'rank-value'),
    element('span', `${[site.country, site.site_id].filter(Boolean).join(' · ')} · ${score}`, 'rank-detail'),
  );
  const tags = badges(site);
  if (tags.childElementCount) row.append(tags);
  row.addEventListener('click', () => onSelect(site));
  return row;
}

function haversine(lat1, lon1, lat2, lon2) {
  const rad = Math.PI / 180;
  const a = Math.sin((lat2 - lat1) * rad / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin((lon2 - lon1) * rad / 2) ** 2;
  return 2 * 6371.0088 * Math.asin(Math.sqrt(a));
}

function init(L, data) {
  const {meta, ranked, flagged, tiles, moon, land, method, evidence, sources} = data;
  const counters = [[meta.counts.tiles, 'Tiles surveyed'], [meta.counts.sites_total, 'Candidate patches'],
    [meta.counts.sites_flagged_total, 'Dune-like patches'], [meta.counts.sites, 'Ranked in atlas']];
  for (const [value, label] of counters) {
    const box = element('div');
    box.append(element('dt', label), element('dd', number(value, 0)));
    byId('stats').append(box);
  }
  byId('ranking-key').textContent = `Ranked by the best ${meta.rank_window_km} × ${meta.rank_window_km} km window, in similarity-weighted km².`;
  byId('scale-max').textContent = `${number(meta.candidate_share_max * 100)}%`;
  byId('flag-count').textContent = ` (${number(meta.counts.sites_flagged, 0)} of ${number(meta.counts.sites_flagged_total, 0)} shown)`;
  const selector = byId('target');
  for (const [key, region] of Object.entries(moon.regions)) {
    const option = element('option', region.display_name);
    option.value = key;
    selector.append(option);
  }
  const strict = strictSites(data.strictFull, data.strict, data.strictReview, data.strictNovelty, data.strictImages);
  const matchKm = data.landcover?.full_run?.match_km;
  const ctx = {
    meta, novelty: data.novelty, radar: data.radar, siteInfo: data.siteInfo, landcover: data.landcover,
    rankConfig: data.rankUncertainty?.configuration,
    strictMatch: strict && Number.isFinite(matchKm) ? (site) => {
      let best = null;
      for (const row of strict.rows) {
        const km = haversine(site.lat, site.lon, row.lat, row.lon);
        if (!best || km < best.km) best = {row, km};
      }
      return best && best.km <= matchKm ? {...best, rule: matchKm} : {row: null, rule: matchKm};
    } : null,
    defaultMatch: Number.isFinite(matchKm) ? (site) => {
      let best = null;
      for (const row of ranked) {
        const km = haversine(site.lat, site.lon, row.lat, row.lon);
        if (!best || km < best.km) best = {site: row, km};
      }
      return best && best.km <= matchKm ? {...best, rule: matchKm, n: ranked.length} : {site: null, rule: matchKm, n: ranked.length};
    } : null,
  };
  const params = new URLSearchParams(location.hash.slice(1));
  const initialTarget = params.get('target');
  let target = Object.hasOwn(moon.regions, initialTarget) ? initialTarget : meta.target;
  selector.value = target;
  let mode = strict && params.get('mask') === 'strict' ? 'strict' : 'default';
  const all = ranked.concat(flagged);
  let active = mode === 'strict' ? strict.rows.find((s) => s.site_id === params.get('site')) || strict.rows[0] :
    all.find((site) => site.site_id === params.get('site')) || ranked[0];
  byId('show-flagged').checked = active?.dune_like ?? false;
  let displayed = [];
  atlas.hidden = false;
  status.hidden = true;
  const {map, markers, selected} = createMap(L, land, tiles, meta.candidate_share_max);

  // Map layers with toggles (F-15, F-16); `layers=moon,mars,both,controls` in the link turns them on.
  const requestedLayers = new Set((params.get('layers') || '').split(','));
  const known = knownLayers(L, data.known);
  for (const [tag, layer] of Object.entries(known)) {
    const box = byId(`layer-${tag}`);
    box.disabled = !data.known;
    box.checked = Boolean(data.known) && requestedLayers.has(tag);
    const sync = () => box.checked ? layer.addTo(map) : layer.remove();
    box.addEventListener('change', sync);
    sync();
    const count = data.known?.counts?.analog_for?.[tag];
    byId(`count-${tag}`).textContent = count == null ? '' : ` (${number(count, 0)})`;
  }
  const controls = controlLayer(L, data.controls);
  const controlBox = byId('layer-controls');
  controlBox.disabled = !data.controls;
  const syncControls = () => controlBox.checked ? controls.addTo(map) : controls.remove();
  controlBox.checked = Boolean(data.controls) && requestedLayers.has('controls');
  controlBox.addEventListener('change', syncControls);
  syncControls();
  if (data.controls) byId('count-controls').textContent = ` (${number(data.controls.n, 0)})`;
  if (data.known?.scope_note) byId('known-scope').textContent = data.known.scope_note;

  // Strict-mask switch (shown only when the strict ranking is loaded).
  const maskSwitch = byId('mask-switch');
  maskSwitch.hidden = !strict;
  if (strict) {
    byId(`mask-${mode}`).checked = true;
    byId('strict-note').textContent = strict.note;
    for (const id of ['mask-default', 'mask-strict']) {
      byId(id).addEventListener('change', () => {
        mode = byId('mask-strict').checked ? 'strict' : 'default';
        active = mode === 'strict' ? strict.rows[0] : ranked[0];
        updateRanking();
        selectSite(active);
        history.replaceState(null, '', permalink());
      });
    }
  }

  function permalink() {
    const link = new URLSearchParams({site: active.site_id, target});
    if (mode === 'strict') link.set('mask', 'strict');
    return `#${link}`;
  }

  function drawOutline() {
    selected.clearLayers();
    if (!active || !displayed.includes(active)) return;
    if (!active.polygon?.length) {
      L.circleMarker([active.lat, active.lon], {radius: 9, color: '#ffc480', weight: 2, fill: false, interactive: false}).addTo(selected);
      return;
    }
    const style = {color: '#ffc480', weight: 2, fillColor: '#ffd597', fillOpacity: 0.17, interactive: false};
    L.polygon(active.polygon, style).addTo(selected);
  }

  function selectSite(site, reveal = false) {
    active = site;
    const link = permalink();
    if (mode === 'strict' && site.full) {
      const files = data.strictFull.source_files || {};
      showSite(byId('site-card'), site, target, moon, sources, link, {...ctx, strictMatch: null,
        siteInfo: {sources: {novelty_record: [files.novelty_record].flat().filter(Boolean).join(' or '), review: files.review}},
        rankConfig: data.strictFull.stability?.configuration, rankSource: files.rank_uncertainty});
      byId('site-card').querySelector('.details-layout').prepend(strictAbout(site, ctx, strict));
    } else if (mode === 'strict') strictSiteCard(byId('site-card'), site, target, moon, sources, link, ctx, strict);
    else showSite(byId('site-card'), site, target, moon, sources, link, ctx);
    drawOutline();
    for (const row of byId('ranking-list').querySelectorAll('button[data-site]')) {
      row.setAttribute('aria-pressed', String(row.dataset.site === active.site_id));
    }
    if (reveal) {
      map.setView([site.lat, site.lon], Math.max(map.getZoom(), 6), {animate: false});
      history.replaceState(null, '', link);
      const title = byId('site-card').querySelector('h3');
      title.scrollIntoView({block: 'start'});
      title.focus({preventScroll: true});
    }
  }

  function updateRanking() {
    const query = byId('search').value.trim().toLowerCase();
    const hideKnown = byId('hide-known').checked;
    const showFlagged = byId('show-flagged').checked && mode === 'default';
    byId('show-flagged').disabled = mode === 'strict';
    const matches = (site) => (!hideKnown || !site.is_known) &&
      [site.site_id, site.country, site.place].some((value) => value?.toLowerCase().includes(query));
    const source = mode === 'strict' ? strict.rows : ranked;
    const regular = source.filter(matches);
    const dune = showFlagged ? flagged.filter(matches) : [];
    displayed = regular.slice(0, meta.list_limit).concat(dune);
    const list = byId('ranking-list');
    list.replaceChildren();
    const onSelect = (site) => selectSite(site, true);
    list.append(...regular.slice(0, meta.list_limit).map((site) => siteRow(site, target, active, onSelect, mode === 'strict')));
    if (dune.length) {
      const [first, last] = meta.flagged_ranks;
      list.append(element('p', `Dune-like relief · ranks ${number(first, 0)}–${number(last, 0)}`, 'rank-group'));
      list.append(...dune.map((site) => siteRow(site, target, active, onSelect, false)));
    }
    if (!regular.length && !dune.length) list.append(element('p', 'No patches match these filters.', 'notice'));
    byId('ranking-title').textContent = mode === 'strict' ? 'Ranked patches · strict mask' : 'Ranked patches · default mask';
    byId('ranking-status').textContent = `${number(Math.min(meta.list_limit, regular.length) + dune.length, 0)} listed · ${number(regular.length + dune.length, 0)} match filters`;
    byId('map-count').textContent = `${number(tiles.length, 0)} survey tiles · ${number(displayed.length, 0)} patches on the map`;
    byId('flag-key').hidden = !showFlagged;
    byId('mask-caption').hidden = mode === 'strict';
    markers.clearLayers();
    for (const site of displayed) {
      const label = element('span', `#${site.rank} · ${site.country || site.site_id}${site.dune_like ? ' · dune-like relief' : ''}${mode === 'strict' ? ' · strict mask' : ''}`);
      const style = site.dune_like ? {color: '#ffbc72', fillOpacity: 0.1, weight: 2, dashArray: '2 2'} :
        mode === 'strict' ? {color: '#0c2637', fillColor: '#F0E442', fillOpacity: .95, weight: 1} :
          {color: '#0c2637', fillColor: '#eff9fa', fillOpacity: .95, weight: 1};
      const marker = L.circleMarker([site.lat, site.lon], {className: 'site-marker', radius: mode === 'strict' ? 5 : 4.5, ...style})
        .bindTooltip(label).on('click', () => selectSite(site, true)).addTo(markers);
      marker.getElement().dataset.site = site.site_id;
    }
    byId('dot-key').textContent = mode === 'strict' ? 'Candidate patch (strict mask)' : 'Candidate patch (default mask)';
    byId('dot-key-icon').className = mode === 'strict' ? 'key dot strict' : 'key dot';
    drawOutline();
  }

  for (const id of ['hide-known', 'show-flagged', 'search']) byId(id).addEventListener('input', updateRanking);
  selector.addEventListener('change', () => {
    target = selector.value;
    updateRanking();
    showMoon(byId('lunar-panel'), moon, target, evidence.figures);
    if (active) {
      selectSite(active);
      history.replaceState(null, '', permalink());
    }
  });
  updateRanking();
  showMoon(byId('lunar-panel'), moon, target, evidence.figures);
  showEvidence(method, evidence, sources, data.methodSections);
  const criteria = byId('criteria');
  let requestedCriteria = false;
  criteria.addEventListener('toggle', async () => {
    if (!criteria.open || requestedCriteria) return;
    const container = byId('criteria-content');
    requestedCriteria = true;
    try {
      showCriteria(container, await json('criteria.json'));
    } catch (error) {
      requestedCriteria = false;
      container.replaceChildren(element('p', error.message, 'notice'));
    }
  });
  if (location.hash === '#criteria') criteria.open = true;
  if (active) selectSite(active, params.has('site'));
}

try {
  const [L, meta, ranked, flagged, tiles] = await Promise.all([
    leaflet(), ...['meta', 'sites', 'sites_flagged', 'tiles'].map((file) => json(`data/${file}.json`)),
  ]);
  const [moon, land, method, evidence, sources] = await Promise.all([
    json('data/moon.json'), json('assets/land.geojson'),
    ...['method', 'validation', 'sources'].map((file) => json(`data/${file}.json`)),
  ]);
  // The strict ranking: data/strict_ranking.json when the export lists it, else the J33 file under validation/.
  // The strict-mask ranking: strict_ranking.json (J42, ranks 1 to 100 with full context) when the export lists it,
  // and the J33 file under validation/ for the ranks beyond it (reduced view).
  const strictFullPath = meta.files?.includes('strict_ranking.json') ? 'data/strict_ranking.json' : null;
  const extra = await optional(['data/novelty.json', 'data/radar.json', 'data/site_info.json', 'data/known_analogs.json',
    'data/controls.json', 'data/method_sections.json', 'data/validation/landcover_sensitivity.json',
    'data/validation/rank_uncertainty.json', 'data/validation/landcover_sensitivity/ranking_bare_strict.json',
    'data/validation/landcover_sensitivity/top30_strict_review.json',
    'data/validation/landcover_sensitivity/novelty_check_strict.json',
    'data/validation/landcover_sensitivity/images/index.json', ...(strictFullPath ? [strictFullPath] : [])]);
  const [novelty, radar, siteInfo, known, controls, methodSections, landcover, rankUncertainty, strict, strictReview,
    strictNovelty, strictImages, strictFull] = extra.values;
  if (extra.failed.length) {
    const notice = byId('partial-status');
    notice.textContent = 'Some data could not load; the blocks that need them say so. ' + extra.failed.join(' · ');
    notice.hidden = false;
  }
  init(L, {meta, ranked, flagged, tiles, moon, land, method, evidence, sources, novelty, radar, siteInfo, known, controls,
    methodSections, landcover, rankUncertainty, strict, strictReview, strictNovelty, strictImages, strictFull});
} catch (error) {
  status.textContent = `The atlas could not load. ${error.message}`;
  status.hidden = false;
  status.setAttribute('role', 'alert');
}
