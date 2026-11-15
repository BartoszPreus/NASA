// Written with SI assistance (Codex). Leaflet 1.9.4: https://leafletjs.com/install.html
import {element, number, badges, showSite, showMoon, showEvidence, showCriteria} from './views.js';

const byId = (id) => document.getElementById(id);
const atlas = byId('atlas');
const status = byId('load-status');
const stops = [[0, 34, 78], [67, 78, 108], [125, 124, 120], [188, 173, 108], [254, 232, 56]];

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

function siteRow(site, target, selected, onSelect) {
  const row = element('button', null, 'rank-row');
  row.type = 'button';
  row.dataset.site = site.site_id;
  row.setAttribute('aria-pressed', String(site === selected));
  row.append(
    element('span', `#${site.rank}`, 'rank-number'),
    element('strong', site.place || site.country || site.site_id),
    element('span', `${number(site.best_window_km2)} km²`, 'rank-value'),
    element('span', `${[site.country, site.site_id].filter(Boolean).join(' · ')} · Terrain score ${number(site.region_scores[target], 3)}`, 'rank-detail'),
  );
  const tags = badges(site);
  if (tags.childElementCount) row.append(tags);
  row.addEventListener('click', () => onSelect(site));
  return row;
}

function init(L, meta, ranked, flagged, tiles, moon, land, method, evidence, sources) {
  const counters = [[meta.counts.tiles, 'Tiles surveyed'], [meta.counts.sites_total, 'Candidate patches'],
    [meta.counts.sites_flagged_total, 'Dune-like patches'], [meta.counts.sites, 'Ranked in atlas']];
  for (const [value, label] of counters) {
    const box = element('div');
    box.append(element('dt', label), element('dd', number(value, 0)));
    byId('stats').append(box);
  }
  byId('ranking-key').textContent = `Ranked by the best ${meta.rank_window_km} × ${meta.rank_window_km} km window, in similarity-weighted km².`;
  byId('scale-max').textContent = `${number(meta.candidate_share_max * 100)}%`;
  const selector = byId('target');
  for (const [key, region] of Object.entries(moon.regions)) {
    const option = element('option', region.display_name);
    option.value = key;
    selector.append(option);
  }
  const params = new URLSearchParams(location.hash.slice(1));
  const initialTarget = params.get('target');
  let target = Object.hasOwn(moon.regions, initialTarget) ? initialTarget : meta.target;
  selector.value = target;
  const all = ranked.concat(flagged);
  let active = all.find((site) => site.site_id === params.get('site')) || ranked[0];
  byId('show-flagged').checked = active?.dune_like ?? false;
  let displayed = [];
  atlas.hidden = false;
  status.hidden = true;
  const {map, markers, selected} = createMap(L, land, tiles, meta.candidate_share_max);

  function drawOutline() {
    selected.clearLayers();
    if (!active || !displayed.includes(active) || !active.polygon?.length) return;
    const style = {color: '#ffc480', weight: 2, fillColor: '#ffd597', fillOpacity: 0.17, interactive: false};
    L.polygon(active.polygon, style).addTo(selected);
  }

  function selectSite(site, reveal = false) {
    active = site;
    const link = new URLSearchParams({site: active.site_id, target});
    showSite(byId('site-card'), site, target, moon, sources, `#${link}`);
    drawOutline();
    for (const row of byId('ranking-list').querySelectorAll('button[data-site]')) {
      row.setAttribute('aria-pressed', String(row.dataset.site === active.site_id));
    }
    if (reveal) {
      map.setView([site.lat, site.lon], Math.max(map.getZoom(), 6), {animate: false});
      history.replaceState(null, '', `#${link}`);
      const title = byId('site-card').querySelector('h3');
      title.scrollIntoView({block: 'start'});
      title.focus({preventScroll: true});
    }
  }

  function updateRanking() {
    const query = byId('search').value.trim().toLowerCase();
    const hideKnown = byId('hide-known').checked;
    const showFlagged = byId('show-flagged').checked;
    const matches = (site) => (!hideKnown || !site.is_known) &&
      [site.site_id, site.country, site.place].some((value) => value?.toLowerCase().includes(query));
    const regular = ranked.filter(matches);
    const dune = showFlagged ? flagged.filter(matches) : [];
    displayed = regular.concat(dune);
    const list = byId('ranking-list');
    list.replaceChildren();
    const onSelect = (site) => selectSite(site, true);
    list.append(...regular.slice(0, meta.list_limit).map((site) => siteRow(site, target, active, onSelect)));
    if (dune.length) {
      const [first, last] = meta.flagged_ranks;
      list.append(element('p', `Dune-like relief · ranks ${number(first, 0)}–${number(last, 0)}`, 'rank-group'));
      list.append(...dune.map((site) => siteRow(site, target, active, onSelect)));
    }
    if (!displayed.length) list.append(element('p', 'No patches match these filters.', 'notice'));
    byId('ranking-status').textContent = `${number(Math.min(meta.list_limit, regular.length) + dune.length, 0)} listed · ${number(displayed.length, 0)} match filters`;
    byId('map-count').textContent = `${number(tiles.length, 0)} survey tiles · ${number(displayed.length, 0)} patches`;
    byId('flag-key').hidden = !showFlagged;
    markers.clearLayers();
    for (const site of displayed) {
      const label = element('span', `#${site.rank} · ${site.country || site.site_id}${site.dune_like ? ' · dune-like relief' : ''}`);
      const style = site.dune_like ? {color: '#ffbc72', fillOpacity: 0.1, weight: 2, dashArray: '2 2'} :
        {color: '#0c2637', fillColor: '#eff9fa', fillOpacity: .95, weight: 1};
      const marker = L.circleMarker([site.lat, site.lon], {className: 'site-marker', radius: 4.5, ...style})
        .bindTooltip(label).on('click', () => selectSite(site, true)).addTo(markers);
      marker.getElement().dataset.site = site.site_id;
    }
    drawOutline();
  }

  for (const id of ['hide-known', 'show-flagged', 'search']) byId(id).addEventListener('input', updateRanking);
  selector.addEventListener('change', () => {
    target = selector.value;
    updateRanking();
    showMoon(byId('lunar-panel'), moon, target);
    if (active) {
      selectSite(active);
      history.replaceState(null, '', `#${new URLSearchParams({site: active.site_id, target})}`);
    }
  });
  updateRanking();
  showMoon(byId('lunar-panel'), moon, target);
  showEvidence(method, evidence, sources);
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
  const [L, meta, sites, flagged, tiles] = await Promise.all([
    leaflet(), ...['meta', 'sites', 'sites_flagged', 'tiles'].map((file) => json(`data/${file}.json`)),
  ]);
  const [moon, land, method, evidence, sources] = await Promise.all([
    json('data/moon.json'), json('assets/land.geojson'),
    ...['method', 'validation', 'sources'].map((file) => json(`data/${file}.json`)),
  ]);
  init(L, meta, sites, flagged, tiles, moon, land, method, evidence, sources);
} catch (error) {
  status.textContent = `The atlas could not load. ${error.message}`;
  status.hidden = false;
  status.setAttribute('role', 'alert');
}
