// Written with SI assistance (Codex). Source metadata is exported from data/sources.csv.
export function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function number(value, precision = 2) {
  if (!Number.isFinite(value)) return 'Not measured';
  return value.toLocaleString('en-US', {maximumFractionDigits: precision});
}

function withUnit(value, unit = '', precision = 2) {
  if (!Number.isFinite(value)) return 'Not measured';
  if (unit === '°' || unit === '%') return number(value, precision) + unit;
  return [number(value, precision), unit].filter(Boolean).join(' ');
}

function lunarNumber(value, unit) {
  return withUnit(unit === '%' && value != null ? value * 100 : value, unit);
}

function statList(entries) {
  const list = element('dl', null, 'metrics');
  for (const [label, value] of entries) {
    const item = element('div');
    item.append(element('dt', label), element('dd', value));
    list.append(item);
  }
  return list;
}

function link(label, url) {
  const anchor = element('a', label);
  anchor.href = url;
  return anchor;
}

function sourceLinks(text) {
  const urls = text.split(/\s*;\s*/);
  return urls.filter((url) => /^https?:\/\/[^\s]+$/i.test(url));
}

function reference(sources, id, label) {
  const row = sources.find((row) => row.source_id === id);
  const url = sourceLinks(row?.url || '')[0];
  return url ? link(label, url) : element('span', label);
}

export function badges(site) {
  const wrap = element('span', null, 'badges');
  if (site.is_known) wrap.append(element('span', 'Known analog site', 'badge'));
  if (site.dune_like) wrap.append(element('span', 'Dune-like relief (terrain rule)', 'badge flag'));
  if (site.novelty === 'mentioned') wrap.append(element('span', 'Region named as a Mars analog in general terms', 'badge'));
  if (site.novelty === 'unreported') wrap.append(element('span', 'Not found in the catalogues and searches listed', 'badge'));
  return wrap;
}

function photo(file, alt, caption, empty) {
  const figure = element('figure', null, 'site-photo');
  if (!file) {
    figure.append(element('p', empty, 'unavailable'));
    return figure;
  }
  const image = element('img');
  image.alt = alt;
  image.loading = 'lazy';
  image.addEventListener('error', () => image.replaceWith(element('p', 'Image could not be loaded.', 'unavailable')));
  image.src = 'data/img/' + encodeURIComponent(file);
  figure.append(image, element('figcaption', caption));
  return figure;
}

function panel(title, className = '') {
  const card = element('section', null, 'panel ' + className);
  card.append(element('h3', title));
  return card;
}

function compareShape(site, target, featureInfo, shareInfo) {
  const block = panel('Terrain shape');
  block.append(element('p', 'Earth patch • Lunar median | Lunar central range (10th–90th percentile)', 'small'));
  const bars = element('div', null, 'comparison-bars');
  for (const [key, [label, unit]] of Object.entries(featureInfo)) {
    const earth = site.features[key];
    const {p10, median, p90} = target.features[key];
    const row = element('div', null, 'bar-row');
    row.dataset.feature = key;
    const heading = element('div', null, 'bar-caption');
    const inRange = earth == null || (earth >= p10 && earth <= p90);
    heading.append(element('strong', label), element('span',
      'Earth ' + lunarNumber(earth, unit) + ' · Moon ' + lunarNumber(median, unit)));
    row.append(heading);
    const track = element('div', null, 'track');
    track.setAttribute('aria-hidden', 'true');
    const max = Math.max(earth ?? 0, p90, 0.0001) * 1.04;
    const range = element('span', null, 'range');
    range.style.left = 100 * p10 / max + '%';
    range.style.width = 100 * (p90 - p10) / max + '%';
    const midpoint = element('span', null, 'median');
    midpoint.style.left = 100 * median / max + '%';
    track.append(range, midpoint);
    if (earth != null) {
      const dot = element('span', null, 'earth');
      dot.style.left = 100 * earth / max + '%';
      track.append(dot);
    }
    row.append(track, element('span', 'Lunar range ' + lunarNumber(p10, unit) + ' to ' +
      lunarNumber(p90, unit) + (inRange ? '' : ' · Earth outside range'), inRange ? null : 'outside'));
    bars.append(row);
  }
  block.append(bars, element('h4', 'Landing and mobility'));
  block.append(statList(Object.entries(shareInfo).map(([key, label]) => [label,
    'Earth ' + lunarNumber(site.shares[key], '%') + ' / Moon ' + lunarNumber(target.shares[key], '%')])));
  return block;
}

function regionalScores(site, regions) {
  const block = panel('Terrain score by lunar target');
  const list = element('ul', null, 'score-grid');
  for (const [key, region] of Object.entries(regions)) {
    const score = site.region_scores[key];
    const title = region.display_name + (site.best_region === key ? ' (best match)' : '');
    const item = element('li');
    const meter = element('meter');
    meter.min = 0;
    meter.max = 1;
    meter.setAttribute('aria-label', title);
    if (score != null) meter.value = score;
    else meter.hidden = true;
    item.append(element('span', title), meter, element('span', number(score, 3)));
    list.append(item);
  }
  block.append(list);
  return block;
}

function formatRange(values, unit) {
  if (!values) return 'Not measured';
  return lunarNumber(values[0], unit) + ' to ' + lunarNumber(values[1], unit);
}

function difference(night, target) {
  if (!Number.isFinite(night)) return 'Not measured';
  if (target.headline) {
    const moon = target.headline.temp_avg_k;
    return moon == null ? 'Not measured' : withUnit(night - moon, 'K');
  }
  const range = target.headline_range.temp_avg_k;
  return range ? formatRange([night - range[1], night - range[0]], 'K') : 'Not measured';
}

function temperaturePanel(label, data, target, source) {
  const block = element('div');
  block.append(element('h4', label), source);
  if (!data) {
    block.append(element('p', 'Not sampled.'));
    return block;
  }
  const measured = (key, unit, monthsKey) => {
    const value = data[key];
    const suffix = monthsKey && data[monthsKey] > 0 ? ' · ' + number(data[monthsKey], 0) + ' months' : '';
    return withUnit(value, unit) + (value == null ? '' : suffix);
  };
  block.append(statList([
    ['Day mean', measured('day_mean_k', 'K', 'day_months')],
    ['Night mean', measured('night_mean_k', 'K', 'night_months')],
    ['Day minus night', measured('day_night_diff_k', 'K', 'diff_months')],
    ['Coldest monthly night mean', measured('night_min_k', 'K')],
    ['Earth coldest night month minus lunar annual mean', difference(data.night_min_k, target)],
  ]));
  return block;
}

function analogyBreaks(site, lunar, sources) {
  const block = panel('Where the analogy breaks', 'breaks wide');
  const reasons = element('ul');
  reasons.append(...site.breaks.map((reason) => element('li', reason)));
  block.append(reasons, element('h4', 'Surface conditions'));
  const grid = element('div', null, 'context-grid');
  const power = element('div');
  power.append(element('h4', 'Earth climatology (reanalysis)'), reference(sources, 'nasa_power', 'NASA POWER'));
  power.append(statList([
    ['Annual mean skin temperature', withUnit(site.power?.ts_mean_c, '°C')],
    ['Monthly mean skin temperature range', site.power && site.power.ts_min_c != null && site.power.ts_max_c != null
      ? formatRange([site.power.ts_min_c, site.power.ts_max_c], '°C') : 'Not measured'],
  ]));
  const moon = element('div');
  moon.append(element('h4', lunar.display_name), reference(sources, 'diviner_prp', 'NASA LRO Diviner'));
  moon.append(statList(['temp_avg_k', 'temp_max_k'].map((key, i) => [
    i === 0 ? 'Median annual mean' : 'Median maximum',
    lunar.headline ? withUnit(lunar.headline[key], 'K') : formatRange(lunar.headline_range[key], 'K'),
  ])));
  const survey = element('div');
  survey.append(element('h4', 'Soil and permafrost'));
  if (site.partner) {
    survey.append(reference(sources, 'jaxa_gportal_amsr2_smc', 'JAXA AMSR2'), element('span', ' · '),
      reference(sources, 'esa_osc_permafrost', 'ESA CCI Permafrost'));
    survey.append(statList([
      ['Soil moisture', withUnit(site.partner.soil_moisture_pct, '%')],
      ['Permafrost fraction', withUnit(site.partner.permafrost_fraction_pct, '%')],
      ['Ground temperature at 2 m', withUnit(site.partner.ground_temp_c, '°C')],
    ]));
  } else {
    survey.append(element('p', 'Not sampled.'));
  }
  grid.append(power, moon,
    temperaturePanel('Earth satellite temperatures', site.partner?.jaxa_sgli, lunar, reference(sources, 'jaxa_gportal_sgli_lst', 'JAXA GCOM-C / SGLI')),
    temperaturePanel('Earth satellite temperatures', site.partner?.nasa_modis, lunar, reference(sources, 'modis_lst', 'NASA MODIS MOD11C1')),
    survey);
  block.append(grid, element('p', 'Earth and lunar products cover different time periods and use different summaries.', 'small'));
  return block;
}

export function showSite(container, site, target, moon, sources, permalink) {
  const lunar = moon.regions[target];
  const head = element('div', null, 'site-head');
  const titles = element('div');
  const title = element('h3', [site.country, site.site_id].filter(Boolean).join(' · '));
  title.tabIndex = -1;
  titles.append(element('p', 'Rank ' + number(site.rank, 0), 'eyebrow'), title);
  if (site.place) titles.append(element('p', site.place));
  titles.append(badges(site));
  head.append(titles, link('Link to this comparison', permalink));
  const layout = element('div', null, 'details-layout');
  const overview = panel('Earth patch');
  const credit = ['NASA Worldview / GIBS', site.image_date, site.image_layer].filter(Boolean).join(' · ');
  overview.append(photo(site.image, 'Satellite view of candidate patch ' + site.site_id, credit, 'No image stored'));
  overview.append(statList([
    ['Latitude / longitude', withUnit(site.lat, '°', 4) + ' / ' + withUnit(site.lon, '°', 4)],
    ['Patch area', withUnit(site.area_km2, 'km²')],
    ['Candidate cells', number(site.n_cells, 0)],
    ['Median elevation', withUnit(site.elev_med, 'm')],
    ['Similarity-weighted window', withUnit(site.best_window_km2, 'km²')],
  ]));
  const analogTag = {moon: 'lunar analog', mars: 'Mars analog', both: 'lunar and Mars analog'};
  if (site.nearest_known) overview.append(element('p',
    'Nearest listed analog · ' + site.nearest_known + ' (' + (analogTag[site.nearest_known_for] || 'tag unknown') +
    ') · ' + withUnit(site.nearest_known_km, 'km'), 'small'));
  if (site.nearest_lunar_known && site.nearest_known_for !== 'moon' && site.nearest_known_for !== 'both') {
    overview.append(element('p', 'Nearest listed lunar analog (tagged lunar or both) · ' + site.nearest_lunar_known +
      ' · ' + withUnit(site.nearest_lunar_known_km, 'km'), 'small'));
  }
  const shape = compareShape(site, lunar, moon.feature_info, moon.share_info);
  const criteriaLink = link('See which criteria enter the comparison', '#criteria');
  criteriaLink.addEventListener('click', () => { document.getElementById('criteria').open = true; });
  shape.append(criteriaLink);
  layout.append(overview, shape, regionalScores(site, moon.regions));
  if (site.review) {
    const review = panel('Satellite image review');
    review.append(element('p', 'Judged from satellite images by an SI model. A person has not confirmed it.', 'small'));
    const verdicts = {no: 'Image review found no terrain concern', unsure: 'Image review inconclusive',
      yes: 'Possible terrain concern'};
    const verdict = verdicts[site.review.looks_like_artefact];
    if (verdict) review.append(element('p', verdict, 'small'));
    review.append(element('p', site.review.what_it_is), element('p', site.review.reason));
    layout.append(review);
  }
  layout.append(analogyBreaks(site, lunar, sources));
  container.replaceChildren(head, layout);
}

export function showMoon(container, moon, target) {
  const region = moon.regions[target];
  const head = element('h3', region.display_name);
  const description = region.members
    ? 'Pooled regions · ' + region.members.map(key => moon.regions[key].display_name).join(', ')
    : 'Window ' + region.window_km.map(v => number(v)).join(' × ') + ' km · ' +
      withUnit(region.lat, '°', 4) + ' / ' + withUnit(region.lon, '°', 4);
  const context = element('p', description, 'caption');
  const metrics = statList(Object.entries(moon.headline_info).map(([key, [label, unit, instrument]]) => [
    label + ' (' + instrument + ')',
    region.headline ? lunarNumber(region.headline[key], unit) : formatRange(region.headline_range[key], unit),
  ]));
  container.replaceChildren(head, context, metrics);
  container.dataset.target = target;
  if (!region.members) {
    const figures = element('div', null, 'lunar-photos');
    figures.append(photo(region.hillshade, 'Hillshade of ' + region.display_name, 'Hillshade · NASA LRO LOLA', 'No hillshade stored'),
      photo(region.quicklook, 'LROC view of ' + region.display_name, 'Summer illumination mosaic · NASA LROC', 'No quicklook stored'));
    container.append(figures);
  }
}

function withLink(text) {
  const node = element('span');
  for (const part of text.split(/(https?:\/\/[^\s,;]+)/)) {
    if (/^https?:\/\//.test(part)) node.append(link(part, part));
    else node.append(document.createTextNode(part));
  }
  return node;
}

export function showEvidence(method, validation, sources) {
  const methods = document.getElementById('method');
  for (const step of method) {
    const row = element('li');
    row.append(element('strong', step.name + '. '), element('span', step.description),
      element('div', null, 'small'));
    row.lastElementChild.append(withLink(step.source));
    methods.append(row);
  }
  const value = (key) => validation.items.find((item) => item.key === key)?.value;
  const {native_slope_error, masked_control_cells, control_count} = validation.summary;
  const notes = [
    'Our lunar slope estimate differs from NASA’s map by a median of ' + withUnit(native_slope_error, '°', 4) + ' at the native grid scale.',
    'With the land-cover mask, ' + number(masked_control_cells, 0) + ' candidate cells remained across ' +
      number(control_count, 0) + ' negative controls.',
    'Terrain enrichment was ' + withUnit(value('median_enrichment'), '×') + ' around known sites and ' +
      withUnit(value('random.median_enrichment_median'), '×') + ' in matched random circles, relative to scanned bare cells.',
    'At tile scale the score did not reliably distinguish known analog tiles from background tiles. AUC ' +
      number(value('recovery.auc'), 3) + ' (90% interval ' + number(value('recovery.auc_ci90.0'), 3) + '–' +
      number(value('recovery.auc_ci90.1'), 3) + ').',
    'Rankings depend on the elevation and land-cover sources. Copernicus and NASA inputs shared ' +
      number(value('ranking_nasa_vs_esa.top50_overlap'), 0) + ' tiles in the top 50.',
  ];
  document.getElementById('evidence-summary').append(...notes.map((note) => element('li', note)));
  const table = document.getElementById('validation');
  for (const group of validation.groups) {
    const details = element('details');
    details.append(element('summary', group));
    const metrics = element('table', null, 'metric-table');
    metrics.setAttribute('aria-label', group);
    const body = element('tbody');
    for (const metric of validation.items.filter((item) => item.group === group)) {
      const row = element('tr');
      const label = element('th', metric.label);
      label.scope = 'row';
      const location = metric.file + ' · ' + metric.key;
      label.title = location;
      label.append(element('small', location));
      row.append(label, element('td', withUnit(metric.value, metric.unit, 4)));
      body.append(row);
    }
    metrics.append(body);
    details.append(metrics);
    table.append(details);
  }
  const result = document.getElementById('sources');
  for (const agency of new Set(sources.map((source) => source.agency))) {
    const details = element('details');
    details.append(element('summary', agency));
    const list = element('ul');
    for (const source of sources.filter((source) => source.agency === agency)) {
      const item = element('li');
      item.dataset.source = source.source_id;
      const urls = sourceLinks(source.url);
      item.append(urls.length ? link(source.name, urls[0]) : element('strong', source.name),
        element('div', source.licence_or_citation + ' · ' + source.status, 'small'),
        element('div', 'Use · ' + source.used_by, 'small'));
      for (const url of urls.slice(1)) {
        item.append(element('span', ' '), link(url, url));
      }
      list.append(item);
    }
    details.append(list);
    result.append(details);
  }
  const tools = element('p', 'Application tools · ', 'small');
  tools.append(link('Leaflet (BSD-2-Clause)', 'https://github.com/Leaflet/Leaflet/blob/v1.9.4/LICENSE'),
    element('span', ' · '), link('Natural Earth land (public domain)', 'https://www.naturalearthdata.com/about/terms-of-use/'),
    element('span', ' · System typefaces.'));
  result.append(tools);
}

export function showCriteria(container, data) {
  const label = element('label', 'Filter by use ');
  const filter = element('select');
  const all = element('option', 'All criteria');
  all.value = '';
  filter.append(all);
  for (const [key, title] of Object.entries(data.statuses)) {
    const option = element('option', title);
    option.value = key;
    filter.append(option);
  }
  label.append(filter);
  const groups = element('div');
  container.replaceChildren(label, groups);
  function render() {
    groups.replaceChildren();
    for (const group of data.groups) {
      const items = data.items.filter(row => row.group === group.id && (!filter.value || row.status === filter.value));
      if (!items.length) continue;
      const table = element('table', null, 'metric-table criteria-table');
      const caption = element('caption', group.label);
      const body = element('tbody');
      for (const item of items) {
        const row = element('tr');
        const title = element('th', item.name);
        title.scope = 'row';
        title.append(element('small', item.plain));
        const status = element('td', data.statuses[item.status]);
        status.append(element('small', item.status_note));
        row.append(title, status);
        body.append(row);
      }
      table.append(caption, body);
      groups.append(table);
    }
  }
  filter.addEventListener('change', render);
  render();
}
