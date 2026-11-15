// Strict-mask ranking (ESA WorldCover class 60 only) as a second ranking (J36, issue #22).
// Written with SI assistance (Claude Code). Data: app/data/validation/landcover_sensitivity/ranking_bare_strict.json
// (J33, data/validation/landcover_sensitivity/ranking_bare_strict.csv), or app/data/strict_ranking.json when exported.
import {element, number, withUnit, statList, link, panel, badges} from './views.js';
import {literatureBlock, reviewBlock, scoreBlock, packageButton} from './card.js';

// Sentences of `breaks` are joined with "; " in the CSV, and some sentences hold a "; " themselves
// ("Atmosphere and weather; the Moon has a vacuum"): a new sentence starts with a capital letter.
function splitBreaks(value) {
  if (Array.isArray(value)) return value;
  return value ? value.split(/;\s+(?=[A-Z])/) : [];
}

function record(row, review, novelty) {
  return {
    site_id: row.site_id, rank: row.rank, country: row.country ?? null, place: row.place ?? novelty?.place ?? null,
    lat: row.lat, lon: row.lon, tile: row.tile ?? null,
    best_window_km2: row.best_window_km2, weighted_area_km2: row.weighted_area_km2,
    weighted_area_capped_km2: row.weighted_area_capped_km2, score: row.score, score_amp: row.score_amp, score_dep: row.score_dep,
    dune_like: row.dune_like ?? row.artefact_flag ?? false, artefact_reason: row.artefact_reason ?? null,
    artefact_share: row.artefact_share ?? null, area_km2: row.area_km2, n_cells: row.n_cells, best_region: row.best_region,
    is_known: row.is_known ?? false, nearest_known: row.nearest_known ?? null, nearest_known_km: row.nearest_known_km ?? null,
    novelty: row.novelty ?? 'unchecked', elev_med: row.elev_med ?? row.elev_m ?? null,
    features: row.features || {s240: row.slope_240m_deg, s570: row.slope_570m_deg, r200: row.rough_200m_m,
      r1600: row.rough_1600m_m, dep_frac: row.depression_share},
    shares: row.shares || {}, bare: row.bare ?? row.bare_share ?? null, ice: row.ice ?? row.ice_share ?? null,
    map_url: row.map_url ?? null, breaks: splitBreaks(row.breaks), polygon: row.polygon || null,
    window: row.window ?? null, review: review || null,
    novelty_record: novelty ? {...novelty, evidence_url_list: novelty.evidence_url_list ||
      (novelty.evidence_urls ? novelty.evidence_urls.split(' ; ') : [])} : null,
    ranking_label: 'strict mask (WorldCover class 60 only)', strict: true,
  };
}

export function strictSites(data, review, novelty) {
  const rows = Array.isArray(data) ? data : data?.rows || data?.sites;
  if (!rows?.length) return null;
  const reviews = review?.rows || [];
  const literature = novelty?.rows || [];
  return {
    source: data.source_file || 'app/data/strict_ranking.json',
    note: data.note || '',
    reviewSource: review?.source_file,
    noveltySource: novelty?.source_file,
    rows: rows.map((row) => record(row,
      reviews.find((r) => r.site_id === row.site_id && (r.rank == null || r.rank === row.rank)),
      literature.find((r) => r.site_id === row.site_id))),
  };
}

function shapeTable(site, target, moon) {
  const block = panel('Terrain shape');
  const region = moon.regions[target];
  block.append(element('p', 'Patch medians against the 10th to 90th percentile of ' + region.display_name + '.', 'small'));
  const table = element('table', null, 'metric-table');
  const body = element('tbody');
  for (const [key, [label, unit]] of Object.entries(moon.feature_info)) {
    const scale = unit === '%' ? 100 : 1;
    const fmt = (v) => withUnit(Number.isFinite(v) ? v * scale : v, unit);
    const value = site.features[key];
    const stats = region.features?.[key];
    const row = element('tr');
    row.append(element('th', label), element('td', fmt(value)),
      element('td', stats ? fmt(stats.p10) + ' to ' + fmt(stats.p90) : 'Not measured'));
    body.append(row);
  }
  table.append(body);
  block.append(table);
  return block;
}

export function strictSiteCard(container, site, target, moon, sources, permalink, ctx, strict) {
  const head = element('div', null, 'site-head');
  const titles = element('div');
  const title = element('h3', [site.country, site.site_id].filter(Boolean).join(' · '));
  title.tabIndex = -1;
  titles.append(element('p', 'Strict mask · rank ' + number(site.rank, 0), 'eyebrow'), title);
  if (site.place) titles.append(element('p', site.place));
  titles.append(element('p', withUnit(site.lat, '°', 4) + ' / ' + withUnit(site.lon, '°', 4), 'small'), badges(site));
  const actions = element('div', null, 'site-actions');
  actions.append(link('Link to this comparison', permalink), packageButton(site, () => target, moon, {...ctx, sources}));
  head.append(titles, actions);
  const layout = element('div', null, 'details-layout');
  const about = panel('Strict-mask ranking', 'wide');
  about.append(element('p', 'Moss and lichen do not count as bare ground in this ranking. ' + strict.note, 'small'));
  const match = ctx.defaultMatch?.(site);
  if (match) about.append(element('p', match.site ? 'In the default ranking a site within ' + number(match.km, 1) + ' km (match rule ' +
    number(match.rule, 1) + ' km) is rank ' + number(match.site.rank, 0) + ' (' + match.site.site_id + ').' :
    'No site of the default ranking (' + number(match.n, 0) + ' exported sites) lies within ' + number(match.rule, 1) + ' km of this site centre.', 'small'));
  about.append(element('p', 'This record has no outline and no stored satellite image: the side-by-side view, surface conditions and radar look exist for the default ranking only.', 'small'));
  about.append(element('p', 'Source · ' + strict.source + ' · rank ' + number(site.rank, 0), 'small source-note'));
  const facts = panel('Earth patch');
  facts.append(statList([
    ['Latitude / longitude', withUnit(site.lat, '°', 4) + ' / ' + withUnit(site.lon, '°', 4)],
    ['Candidate cells', number(site.n_cells, 0)],
    ['Median elevation', withUnit(site.elev_med, 'm')],
    ['Bare share (strict)', Number.isFinite(site.bare) ? number(site.bare * 100, 1) + '%' : 'Not measured'],
  ]));
  if (site.nearest_known) facts.append(element('p', 'Nearest listed analog · ' + site.nearest_known + ' · ' +
    withUnit(site.nearest_known_km, 'km'), 'small'));
  layout.append(about, facts, shapeTable(site, target, moon), scoreBlock(site));
  if (site.review) layout.append(reviewBlock(site.review, strict.reviewSource));
  layout.append(literatureBlock(site, {...ctx, siteInfo: {sources: {novelty_record: strict.noveltySource}}}));
  const breaks = panel('Where the analogy breaks', 'breaks wide');
  const list = element('ul');
  list.append(...site.breaks.map((reason) => element('li', reason)));
  for (const [label, key] of [['Access', 'access'], ['Protection', 'protection']]) {
    const item = element('li');
    item.append(element('strong', label + ' · '), document.createTextNode(site.novelty_record?.[key] || 'Not recorded (no literature check for this site)'));
    list.append(item);
  }
  breaks.append(list);
  layout.append(breaks);
  container.replaceChildren(head, layout);
}
