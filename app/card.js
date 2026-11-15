// Site card blocks added by J36 (issue #22). Written with SI assistance (Claude Code).
// Every number shown here is read from app/data/*.json (contract: app/data/SCHEMA.md); none is typed.
import {element, number, withUnit, statList, link, panel, photo} from './views.js';

// Degrees to km on a sphere of the mean Earth radius (the radius app/build_data.py uses for distances).
const EARTH_KM_PER_DEG = Math.PI * 6371.0088 / 180;

const urlPattern = /https?:\/\/[^\s,;)]+/;

function evidenceItem(text) {
  const item = element('li');
  const match = text.match(urlPattern);
  if (!match) {
    item.textContent = text;
    return item;
  }
  const anchor = link(match[0], match[0]);
  anchor.target = '_blank';
  anchor.rel = 'noopener';
  item.append(anchor);
  const rest = text.replace(match[0], '').trim();
  if (rest) item.append(element('span', ' ' + rest, 'small'));
  return item;
}

function sourceNote(text) {
  return element('p', 'Source · ' + text, 'small source-note');
}

function share(value) {
  return Number.isFinite(value) ? number(value * 100, 1) + '%' : 'Not measured';
}

// S04.12 / F-39: literature record, wording of docs/NOVELTY.md section 6 (novelty.json · wording).
export function literatureBlock(site, ctx) {
  const block = panel('Literature record', 'wide literature');
  const record = site.novelty_record;
  const values = ctx.novelty?.values || {};
  if (ctx.novelty?.wording) block.append(element('p', ctx.novelty.wording, 'small wording'));
  if (!record) {
    block.append(element('p', 'No literature check for this site. ' + (values[site.novelty] || ''), 'unavailable-text'));
    return block;
  }
  block.append(element('p', 'Verdict · ' + record.verdict + ' · ' + (values[record.verdict] || ''), 'verdict'));
  const facts = element('dl', null, 'record');
  for (const [label, key] of [['Place', 'place'], ['Terrain', 'terrain'], ['Why it may or may not compare', 'why_moonlike_or_artefact'],
    ['Access', 'access'], ['Protection', 'protection'], ['Searches run', 'searches_run']]) {
    const row = element('div');
    row.append(element('dt', label), element('dd', record[key] || 'Not recorded'));
    facts.append(row);
  }
  block.append(facts, element('h4', 'Evidence'));
  const list = element('ul', null, 'evidence-list');
  list.append(...(record.evidence_url_list || []).map(evidenceItem));
  if (!list.childElementCount) list.append(element('li', 'No evidence recorded.'));
  block.append(list, sourceNote(ctx.siteInfo?.sources?.novelty_record + ' · row ' + record.site_id));
  return block;
}

// S04.13 / F-41: image review of ranks 1 to 30.
export function reviewBlock(review, sourceFile) {
  const block = panel('Satellite image review');
  block.append(element('p', 'Judged from satellite images by an SI model. A person has not confirmed it.', 'small'));
  const verdicts = {no: 'Image review found no terrain concern', unsure: 'Image review inconclusive',
    yes: 'Possible terrain concern'};
  block.append(element('p', 'Artefact verdict · ' + (verdicts[review.looks_like_artefact] || review.looks_like_artefact), 'verdict'));
  block.append(element('h4', 'What it is'), element('p', review.what_it_is), element('h4', 'Reason'), element('p', review.reason));
  if (sourceFile) block.append(sourceNote(sourceFile));
  return block;
}

// S04.17 / F-46: moss-and-lichen check (landcover_strict, ranks 1 to 100).
export function mossBlock(site, ctx) {
  const block = panel('Moss and lichen check');
  const lc = site.landcover_strict;
  const config = ctx.landcover;
  block.append(element('p', 'The default mask counts ESA WorldCover class "moss and lichen" as bare ground. ' +
    'The strict mask keeps class "bare / sparse vegetation" only.', 'small'));
  if (!lc) {
    block.append(element('p', 'Not checked: the check covers ranks 1 to ' + number(config?.top, 0) + '.', 'unavailable-text'));
    return block;
  }
  const core = config ? number(config.min_cells, 0) + '-cell' : 'minimum';
  const kept = lc.strict_passes_cells ? 'Keeps a ' + core + ' core without moss and lichen' :
    'Does not keep a ' + core + ' core without moss and lichen';
  block.append(element('p', kept, 'verdict'));
  const modis = (value) => value == null ? 'Not covered (MODIS check)' : (value ? 'passes' : 'fails');
  block.append(statList([
    ['Bare share, default mask (median of cells)', share(lc.bare_med)],
    ['Bare share, strict mask (median of cells)', share(lc.bare_strict_med)],
    ['Moss and lichen (median of cells)', share(lc.moss_lichen_med)],
    ['Cells kept under the strict mask', number(lc.strict_kept_cells, 0) + ' of ' + number(lc.n_cells, 0)],
    ['Largest connected group kept', number(lc.strict_largest_group, 0) + ' cells'],
    ['Strict median at or above the bare threshold' + (config ? ' (' + number(config.bare_min) + ')' : ''), lc.strict_passes_median ? 'yes' : 'no'],
    ['MODIS bare share (median)', lc.modis_bare_med == null ? 'Not covered (MODIS check)' : share(lc.modis_bare_med)],
    ['MODIS check, cells', modis(lc.modis_passes_cells)],
  ]));
  const strict = ctx.strictMatch?.(site);
  if (strict) {
    block.append(element('p', strict.row ? 'In the strict-mask ranking a site within ' + number(strict.km, 1) +
      ' km (match rule ' + number(strict.rule, 1) + ' km) is rank ' + number(strict.row.rank, 0) + ' (' + strict.row.site_id + ').' :
      'No site of the strict-mask ranking lies within ' + number(strict.rule, 1) + ' km of this site centre.', 'small'));
  }
  block.append(sourceNote(ctx.siteInfo?.sources?.landcover_strict + ' · region ' + lc.region));
  return block;
}

// S04.9 / F-45: rank certainty, shown only when rank_uncertainty exists for the site.
export function certaintyBlock(site, ctx) {
  const ru = site.rank_uncertainty;
  if (!ru) return null;
  const block = panel('Rank certainty');
  const runs = ctx.rankConfig?.n_bootstrap;
  block.append(element('p', 'Bootstrap of the lunar reference cells' + (runs ? ' (' + number(runs, 0) + ' runs)' : '') +
    ' and reruns without one feature group.', 'small'));
  block.append(statList([
    ['Rank interval (5th to 95th percentile)', number(ru.rank_p05, 0) + ' to ' + number(ru.rank_p95, 0)],
    ['Median rank', number(ru.rank_median, 0)],
    ['Share of runs in the top 30', share(ru.top30_share)],
    ['Share of runs in the top 100', share(ru.top100_share)],
    ['Rank without slopes', number(ru.rank_no_slopes, 0)],
    ['Rank without roughness', number(ru.rank_no_roughness, 0)],
    ['Rank without depressions', number(ru.rank_no_depressions, 0)],
    ['Rank with NASADEM', ru.nasadem_tile ? number(ru.rank_nasadem, 0) : 'Not measured (tile not in the NASADEM comparison)'],
  ]));
  block.append(sourceNote('data/sites/rank_uncertainty.csv · ' + ru.site_id ));
  return block;
}

// S04.16 / F-44: RADARSAT-1 quicklook, uncalibrated, texture only.
export function radarBlock(site, ctx) {
  const radar = site.radar;
  if (!radar) return null;
  const block = panel('Radar look (RADARSAT-1)');
  block.append(element('p', 'Uncalibrated C-band image: view it for texture only. ' + (ctx.radar?.caveat || ''), 'small'));
  if (radar.status !== 'saved' || !radar.image) {
    block.append(element('p', ctx.radar?.status_meaning?.[radar.status] || radar.status, 'unavailable-text'));
    if (radar.rejected) block.append(element('p', radar.rejected, 'small'));
  } else {
    block.append(photo(radar.image, 'RADARSAT-1 quicklook of ' + site.site_id,
      ['RADARSAT-1 (CSA)', radar.date, radar.beam, radar.product, radar.pass_direction].filter(Boolean).join(' · '), 'No quicklook stored'));
    block.append(statList([
      ['Scenes over the centre', number(radar.n_scenes, 0)],
      ['Incidence angle', withUnit(radar.incidence_deg, '°', 1)],
      ['Nominal pixel', withUnit(radar.nominal_pixel_m, 'm')],
      ['Usable pixels', share(radar.valid_share)],
      ['Brightness variation (std / mean of DN)', number(radar.cv_dn, 3)],
      ['Texture power at 200 m to 2 km', share(radar.power_share_200m_2km)],
    ]));
  }
  block.append(sourceNote(ctx.siteInfo?.sources?.radar + ' · ' + radar.site_id));
  return block;
}

// S04.7 / F-34, F-31, F-43: score parts and areas.
export function scoreBlock(site) {
  const block = panel('Score parts and areas');
  block.append(element('p', 'The score is the median similarity of the patch cells to the pooled lunar target; it is not a probability of being an analog.', 'small'));
  block.append(statList([
    ['Score (median of cells)', number(site.score, 3)],
    ['Slope and roughness part', number(site.score_amp, 3)],
    ['Depression part', number(site.score_dep, 3)],
    ['Patch area', withUnit(site.area_km2, 'km²')],
    ['Similarity-weighted area', withUnit(site.weighted_area_km2, 'km²')],
    ['Weighted area, capped', withUnit(site.weighted_area_capped_km2, 'km²')],
    ['Best window (ranking key)', withUnit(site.best_window_km2, 'km²')],
    ['Best window centre', site.window ? withUnit(site.window[0], '°', 4) + ' / ' + withUnit(site.window[1], '°', 4) : 'Not measured'],
    ['Tile', site.tile || 'Not measured'],
  ]));
  if (site.dune_like) {
    block.append(element('h4', 'Dune-like relief (terrain rule)'),
      element('p', share(site.artefact_share) + ' of the cells are flagged. ' + (site.artefact_reason || ''), 'small'));
  }
  return block;
}

function niceLength(km) {
  const target = km / 4;
  const power = 10 ** Math.floor(Math.log10(target));
  const step = [5, 2, 1].map((f) => f * power).find((value) => value <= target);
  return step || power;
}

function polygonExtent(polygon) {
  const points = polygon.flat(2);
  if (!points.length) return null;
  const lats = points.map((p) => p[0]);
  const lons = points.map((p) => p[1]);
  return [Math.min(...lats), Math.min(...lons), Math.max(...lats), Math.max(...lons)];
}

function outline(polygon, box, className) {
  const [latMin, lonMin, latMax, lonMax] = box;
  const cos = Math.cos((latMin + latMax) / 2 * Math.PI / 180);
  const width = (lonMax - lonMin) * EARTH_KM_PER_DEG * cos;
  const height = (latMax - latMin) * EARTH_KM_PER_DEG;
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.setAttribute('class', className);
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS(ns, 'path');
  const d = polygon.flatMap((rings) => rings.map((ring) => 'M' + ring.map(([lat, lon]) =>
    ((lon - lonMin) * EARTH_KM_PER_DEG * cos).toFixed(3) + ' ' + ((latMax - lat) * EARTH_KM_PER_DEG).toFixed(3)).join('L') + 'Z'));
  path.setAttribute('d', d.join(' '));
  path.setAttribute('fill-rule', 'evenodd');
  path.setAttribute('vector-effect', 'non-scaling-stroke');
  svg.append(path);
  return {svg, width, height};
}

function scaleFrame(frameX, frameY, boxX, boxY, content, scaleKm, caption) {
  const figure = element('figure', null, 'sbs-figure');
  const frame = element('div', null, 'sbs-frame');
  frame.style.aspectRatio = `${frameX} / ${frameY}`;
  const box = element('div', null, 'sbs-box');
  box.style.width = 100 * boxX / frameX + '%';
  box.style.height = 100 * boxY / frameY + '%';
  box.append(...content);
  const bar = element('div', null, 'scale-bar');
  bar.style.width = 100 * scaleKm / frameX + '%';
  bar.append(element('span', number(scaleKm) + ' km'));
  frame.append(box, bar);
  figure.append(frame, element('figcaption', caption));
  return figure;
}

// S05 / F-48 to F-50 (issue #22 step 1): Earth and Moon at one ground scale.
export function sideBySide(site, target, moon) {
  const block = panel('Side by side · terrain shape at 200 m to 1.6 km', 'wide side-by-side');
  let key = target;
  if (!moon.regions[key]?.window_km) {
    key = site.best_region;
    block.append(element('p', 'The pooled target has no single window; the panel shows this patch’s best matching region, ' +
      (moon.regions[key]?.display_name || key) + '.', 'small'));
  }
  const region = moon.regions[key];
  const extent = site.image_bbox || (site.polygon?.length ? polygonExtent(site.polygon) : null);
  if (!region?.window_km || !extent) {
    block.append(element('p', 'Not measured: no ground extent for one of the two panels.', 'unavailable-text'));
    return block;
  }
  const cos = Math.cos((extent[0] + extent[2]) / 2 * Math.PI / 180);
  const ex = (extent[3] - extent[1]) * EARTH_KM_PER_DEG * cos;
  const ey = (extent[2] - extent[0]) * EARTH_KM_PER_DEG;
  const [mx, my] = region.window_km;
  const fx = Math.max(ex, mx);
  const fy = Math.max(ey, my);
  const scaleKm = niceLength(fx);
  const earth = [];
  if (site.image && site.image_bbox) {
    const image = element('img');
    image.alt = 'Satellite image of ' + site.site_id + ' at true ground proportions';
    image.src = 'data/img/' + encodeURIComponent(site.image);
    image.addEventListener('error', () => image.replaceWith(element('p', 'Image could not be loaded.', 'unavailable')));
    earth.push(image);
  }
  if (site.polygon?.length) earth.push(outline(site.polygon, extent, 'sbs-outline').svg);
  const earthCaption = (site.image ? 'Earth · NASA Worldview / GIBS ' + (site.image_date || '') + ' · image extent ' :
    'Earth · no image stored: patch outline only · outline extent ') + number(ex, 1) + ' × ' + number(ey, 1) + ' km';
  const moonImage = element('img');
  moonImage.alt = 'Hillshade of ' + region.display_name;
  moonImage.src = 'data/img/' + encodeURIComponent(region.hillshade);
  moonImage.addEventListener('error', () => moonImage.replaceWith(element('p', 'Hillshade could not be loaded.', 'unavailable')));
  const pair = element('div', null, 'sbs-pair');
  pair.append(
    scaleFrame(fx, fy, ex, ey, earth, scaleKm, earthCaption),
    scaleFrame(fx, fy, mx, my, [moonImage], scaleKm,
      'Moon · ' + region.display_name + ' · LOLA hillshade of the ' + number(mx) + ' × ' + number(my) + ' km window (polar stereographic)'),
  );
  block.append(pair, element('p', 'Both panels use one ground scale; the bar has the same length on each. The comparison is of terrain shape ' +
    '(slope and roughness statistics), not of colour, rock or surface.', 'small'));
  const table = element('table', null, 'metric-table');
  table.setAttribute('aria-label', 'Terrain values of the patch against ' + region.display_name);
  const head = element('thead');
  const hr = element('tr');
  hr.append(...['Feature', 'Earth patch', region.display_name + ' 10th to 90th percentile', 'Inside'].map((t) => element('th', t)));
  head.append(hr);
  const body = element('tbody');
  for (const [feature, [label, unit]] of Object.entries(moon.feature_info)) {
    const value = site.features?.[feature];
    const stats = region.features?.[feature];
    const scale = unit === '%' ? 100 : 1;
    const fmt = (v) => withUnit(Number.isFinite(v) ? v * scale : v, unit);
    const row = element('tr');
    const inside = Number.isFinite(value) && stats ? (value >= stats.p10 && value <= stats.p90 ? 'yes' : 'no') : 'Not measured';
    row.append(element('th', label), element('td', fmt(value)),
      element('td', stats ? fmt(stats.p10) + ' to ' + fmt(stats.p90) : 'Not measured'), element('td', inside));
    body.append(row);
  }
  table.append(head, body);
  block.append(table);
  return block;
}

const packageSourceIds = ['copernicus_dem', 'esa_worldcover', 'worldview_gibs', 'pgda90_lola_20m', 'nasa_power',
  'modis_lst', 'jaxa_gportal_sgli_lst', 'jaxa_gportal_amsr2_smc', 'esa_osc_permafrost', 'csa_radarsat1', 'diviner_prp'];

function sourceRow(sources, id) {
  const row = sources.find((s) => s.source_id === id);
  return row ? {source_id: row.source_id, name: row.name, urls: row.urls, licence_or_citation: row.licence_or_citation,
    status: row.status} : null;
}

// F-40 (issue #22 step 3): one JSON per site, built in the browser from the loaded data.
export function sitePackage(site, target, moon, ctx) {
  const key = moon.regions[target]?.window_km ? target : site.best_region;
  const region = moon.regions[key];
  const copStem = site.tile ? 'Copernicus_DSM_COG_10_' + site.tile.slice(0, 3) + '_00_' + site.tile.slice(3) + '_00_DEM' : null;
  return {
    package: 'Zodiak site package',
    built_from_commit: ctx.meta?.commit || null,
    data_contract: 'app/data/SCHEMA.md',
    site_id: site.site_id,
    ranking: site.ranking_label || (site.dune_like ? 'dune-like group (sites_flagged.json)' : 'default mask (sites.json)'),
    rank: site.rank,
    published_rank: site.published_rank ?? null,
    rank_interval_p05_p95: site.rank_uncertainty ? [site.rank_uncertainty.rank_p05, site.rank_uncertainty.rank_p95] : null,
    rank_uncertainty: site.rank_uncertainty || null,
    country: site.country ?? null,
    place: site.place ?? null,
    lat: site.lat,
    lon: site.lon,
    coordinates_note: 'degrees, WGS84, east positive',
    polygon: site.polygon || null,
    polygon_note: '[polygon][ring][point][lat, lon]',
    tile: site.tile ?? null,
    area_km2: site.area_km2 ?? null,
    best_window_km2: site.best_window_km2 ?? null,
    window_centre: site.window ?? null,
    score: {score: site.score ?? null, score_amp: site.score_amp ?? null, score_dep: site.score_dep ?? null},
    features: site.features || null,
    feature_info: moon.feature_info,
    shares: site.shares || null,
    lunar_region_compared: region ? {
      id: key, name: region.display_name, selected_target: target, lat: region.lat, lon_east: region.lon,
      window_km: region.window_km, features: region.features, shares: region.shares,
    } : null,
    region_scores: site.region_scores || null,
    best_region: site.best_region ?? null,
    breaks: site.breaks || [],
    access: site.novelty_record?.access ?? null,
    protection: site.novelty_record?.protection ?? null,
    literature: {
      novelty: site.novelty, meaning: ctx.novelty?.values?.[site.novelty] ?? null, wording: ctx.novelty?.wording ?? null,
      record: site.novelty_record || null,
    },
    known_match: site.known_match ?? null,
    nearest_known: site.nearest_known ? {name: site.nearest_known, km: site.nearest_known_km, analog_for: site.nearest_known_for,
      url: site.nearest_known_url ?? null} : null,
    strict_mask_check: site.landcover_strict || null,
    image_review: site.review ? {...site.review, judged_by: 'an SI model; a person has not confirmed it'} : null,
    surface: {power: site.power || null, partner: site.partner || null},
    radar: site.radar || null,
    image: site.image ? {file: 'app/data/img/' + site.image, date: site.image_date, layer: site.image_layer,
      bbox_lat_min_lon_min_lat_max_lon_max: site.image_bbox, source: sourceRow(ctx.sources, 'worldview_gibs')} : null,
    elevation: {
      tile: site.tile ?? null,
      copernicus_dem_tile_url: copStem ? 'https://copernicus-dem-30m.s3.amazonaws.com/' + copStem + '/' + copStem + '.tif' : null,
      url_rule: 'pipeline/io_earth.py COP_URL',
      source: sourceRow(ctx.sources, 'copernicus_dem'),
    },
    sources: packageSourceIds.map((id) => sourceRow(ctx.sources, id)).filter(Boolean),
    null_means: 'not measured or not sampled (never zero)',
  };
}

export function packageButton(site, getTarget, moon, ctx) {
  const button = element('button', 'Download site package', 'action');
  button.type = 'button';
  button.addEventListener('click', () => {
    const data = sitePackage(site, getTarget(), moon, ctx);
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const anchor = element('a');
    anchor.href = url;
    anchor.download = 'zodiak_site_' + site.site_id + '.json';
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  return button;
}
