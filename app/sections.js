// Lunar target panel, method, validation and sources sections.
// Written with SI assistance (Codex; J36 instrument tables, map gallery, figures, sources table with Claude Code).
// Colour-bar stops are the published matplotlib colour maps (https://matplotlib.org/stable/users/explain/colors/colormaps.html).
import {element, number, withUnit, statList, link, photo, lunarNumber, formatRange, sourceLinks} from './views.js';

const colourMaps = {
  viridis: ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'],
  cividis: ['#00224e', '#434e6c', '#7d7c78', '#bcad6c', '#fee838'],
  inferno: ['#000004', '#57106e', '#bc3754', '#f98e09', '#fcffa4'],
  magma: ['#000004', '#51127c', '#b73779', '#fc8961', '#fcfdbf'],
  gray: ['#000000', '#ffffff'],
  gray_r: ['#ffffff', '#000000'],
};

export function withLink(text) {
  const node = element('span');
  for (const part of String(text).split(/(https?:\/\/[^\s,;)]+)/)) {
    if (/^https?:\/\//.test(part)) node.append(link(part, part));
    else node.append(document.createTextNode(part));
  }
  return node;
}

function colourBar(info) {
  const wrap = element('div', null, 'colour-bar');
  const stops = colourMaps[info?.cmap];
  if (!stops) {
    wrap.append(element('span', 'Colour scale not recorded', 'small'));
    return wrap;
  }
  const bar = element('span', null, 'bar');
  bar.style.background = 'linear-gradient(90deg, ' + stops.join(', ') + ')';
  bar.setAttribute('aria-hidden', 'true');
  const ends = element('span', null, 'ends');
  ends.append(element('span', info.vmin == null ? 'min (stretched)' : number(info.vmin, 3)),
    element('span', info.cmap), element('span', info.vmax == null ? 'max (stretched)' : number(info.vmax, 3)));
  wrap.append(bar, ends);
  return wrap;
}

function statCell(value) {
  if (value == null) return 'Not measured';
  if (typeof value === 'number') return number(value, 4);
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (Array.isArray(value)) return value.map((v) => typeof v === 'number' ? number(v, 4) : String(v)).join(' to ');
  if (typeof value === 'object' && 'median' in value) {
    return 'median ' + number(value.median, 4) + (value.p10 != null ? ' · p10 ' + number(value.p10, 4) + ' · p90 ' + number(value.p90, 4) : '') +
      (value.min != null ? ' · min ' + number(value.min, 4) + ' · max ' + number(value.max, 4) : '');
  }
  if (typeof value === 'string') return value;
  return null;
}

function instrumentTable(region, moon) {
  const details = element('details', null, 'instrument-table');
  details.append(element('summary', 'Full instrument statistics · ' + region.display_name));
  const skip = new Set(['png', 'caveats', 'window_m']);
  for (const [id, values] of Object.entries(region.instruments)) {
    const info = moon.instrument_info[id] || {};
    const block = element('section', null, 'instrument');
    block.append(element('h4', (info.instrument ? info.instrument.toUpperCase() + ' · ' : '') + (info.product || id)));
    if (info.measures) block.append(element('p', info.measures, 'small'));
    block.append(element('p', 'Unit · ' + (info.unit || 'not recorded') + ' · moon.json · regions.' + region.id + '.instruments.' + id, 'small'));
    const wrap = element('div', null, 'table-wrap');
    const table = element('table', null, 'metric-table');
    table.setAttribute('aria-label', id + ' statistics');
    const body = element('tbody');
    for (const [key, value] of Object.entries(values)) {
      if (skip.has(key)) continue;
      const text = statCell(value);
      if (text == null) continue;
      const row = element('tr');
      const th = element('th', key);
      th.scope = 'row';
      row.append(th, element('td', text));
      body.append(row);
    }
    table.append(body);
    wrap.append(table);
    block.append(wrap);
    const caveats = [...new Set([...(values.caveats || []), ...(info.caveats || [])])];
    if (caveats.length) {
      const list = element('ul', null, 'small caveats');
      list.append(...caveats.map((c) => element('li', 'Caveat · ' + c)));
      block.append(list);
    }
    if (info.citation) block.append(element('p', 'Citation · ' + info.citation, 'small'));
    const urls = element('p', null, 'small');
    for (const url of info.urls || []) urls.append(link(url, url), element('span', ' '));
    if (urls.childElementCount) block.append(urls);
    details.append(block);
  }
  return details;
}

function mapGallery(region, moon) {
  const gallery = element('div', null, 'map-gallery');
  for (const [id, file] of Object.entries(region.maps || {})) {
    const info = moon.instrument_info[id] || {};
    const figure = photo(file, (info.product || id) + ' map of ' + region.display_name,
      (info.instrument ? info.instrument.toUpperCase() + ' · ' : '') + (info.product || id) + ' · ' + (info.unit || 'unit not recorded'),
      'No map stored');
    figure.classList.add('instrument-map');
    figure.append(colourBar(info));
    gallery.append(figure);
  }
  if (!gallery.childElementCount) gallery.append(element('p', 'No map stored.', 'unavailable'));
  return gallery;
}

function featureTable(region, moon) {
  const details = element('details', null, 'instrument-table');
  details.append(element('summary', 'Terrain statistics · ' + region.display_name));
  const wrap = element('div', null, 'table-wrap');
  const table = element('table', null, 'metric-table');
  const head = element('thead');
  const hr = element('tr');
  hr.append(...['Feature', 'Median', '10th percentile', '90th percentile'].map((t) => element('th', t)));
  head.append(hr);
  const body = element('tbody');
  for (const [key, [label, unit]] of Object.entries(moon.feature_info_all || moon.feature_info)) {
    const stats = region.features?.[key] || region.shares_range?.[key];
    const row = element('tr');
    const th = element('th', label);
    th.scope = 'row';
    row.append(th, ...['median', 'p10', 'p90'].map((k) => element('td', lunarNumber(stats?.[k], unit))));
    body.append(row);
  }
  table.append(head, body);
  wrap.append(table);
  details.append(wrap);
  if (region.mean_dep_frac != null) details.append(element('p', 'Mean share of closed depressions · ' + lunarNumber(region.mean_dep_frac, '%'), 'small'));
  return details;
}

function figureBlock(entry, caption) {
  const figure = element('figure', null, 'validation-figure');
  const image = element('img');
  image.loading = 'lazy';
  image.alt = caption + ' (' + entry.source + ')';
  image.src = 'data/' + entry.file;
  image.addEventListener('error', () => image.replaceWith(element('p', 'Figure could not be loaded: ' + entry.file, 'unavailable')));
  const anchor = link('', 'data/' + entry.file);
  anchor.append(image);
  figure.append(anchor, element('figcaption', caption + ' · ' + entry.source + (entry.reencoded ? ' (JPEG copy at the original pixel size)' : '')));
  return figure;
}

export function showMoon(container, moon, target, figures) {
  const region = moon.regions[target];
  const head = element('h3', region.display_name);
  const description = region.members
    ? 'Pooled regions · ' + region.members.map(key => moon.regions[key].display_name).join(', ')
    : 'Window ' + region.window_km.map(v => number(v)).join(' × ') + ' km · ' +
      withUnit(region.lat, '°', 4) + ' / ' + withUnit(region.lon, '°', 4) + ' east (lunar latitude / east longitude 0 to 360)';
  const context = element('p', description, 'caption');
  const metrics = statList(Object.entries(moon.headline_info).map(([key, [label, unit, instrument]]) => [
    label + ' (' + instrument + ')',
    region.headline ? lunarNumber(region.headline[key], unit) : formatRange(region.headline_range[key], unit),
  ]));
  container.replaceChildren(head, context, metrics);
  container.dataset.target = target;
  if (region.members) {
    container.append(element('p', 'The pooled target has no window and no instrument values of its own; the values above are the range over its members. ' +
      'Choose one named region for its instrument statistics and maps.', 'small'));
    const thumbs = element('div', null, 'map-gallery');
    for (const key of region.members) {
      const member = moon.regions[key];
      thumbs.append(photo(member.hillshade, 'Hillshade of ' + member.display_name, member.display_name + ' · LOLA hillshade', 'No hillshade stored'));
    }
    container.append(thumbs);
  } else {
    if (region.coord_source) {
      const coords = element('p', 'Coordinates · ' + (region.coord_status || 'status not recorded') + ' · ', 'small');
      coords.append(withLink(region.coord_source));
      container.append(coords);
    }
    if (region.notes) container.append(element('p', region.notes, 'small'));
    const photos = element('div', null, 'lunar-photos');
    photos.append(photo(region.hillshade, 'Hillshade of ' + region.display_name, 'Hillshade · NASA LRO LOLA', 'No hillshade stored'),
      photo(region.quicklook, 'LROC view of ' + region.display_name, 'Summer illumination mosaic · NASA LROC · brightness DN, not a physical value', 'No quicklook stored'));
    container.append(photos, featureTable(region, moon));
    if (region.instruments) {
      container.append(element('h4', 'Instrument maps of this window'), mapGallery(region, moon), instrumentTable(region, moon));
    }
  }
  const diviner = figures?.['diviner_regions_temperature.png'];
  if (diviner) container.append(figureBlock(diviner, 'Diviner temperatures of the lunar regions'));
  if (moon.registry_note) container.append(element('p', moon.registry_note, 'small'));
}

function metricValue(metric) {
  if (typeof metric.value === 'string') return metric.value;
  if (typeof metric.value === 'boolean') return metric.value ? 'yes' : 'no';
  return withUnit(metric.value, metric.unit, 4);
}

export function showEvidence(method, validation, sources, methodSections) {
  const methods = document.getElementById('method');
  for (const step of method) {
    const row = element('li');
    row.append(element('strong', step.name + '. '), element('span', step.description),
      element('div', null, 'small'));
    row.lastElementChild.append(withLink(step.source));
    methods.append(row);
  }
  const sections = document.getElementById('method-sections');
  for (const section of methodSections?.sections || []) {
    const block = element('section', null, 'method-section');
    block.append(element('h4', section.title));
    if (section.is_list) {
      const list = element('ul');
      list.append(...section.paragraphs.map((p) => {
        const item = element('li');
        item.append(withLink(p));
        return item;
      }));
      block.append(list);
    } else {
      for (const p of section.paragraphs) {
        const para = element('p');
        para.append(withLink(p));
        block.append(para);
      }
    }
    sections.append(block);
  }
  if (!methodSections) sections.append(element('p', 'Method sections not loaded (data/method_sections.json).', 'notice'));
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
  const files = Object.values(validation.files || {});
  const allFigures = Object.values(validation.figures || {});
  const figureByFile = new Map(allFigures.map((f) => [f.file, f]));
  const placed = new Set();
  for (const group of validation.groups) {
    const items = validation.items.filter((item) => item.group === group);
    const details = element('details');
    details.append(element('summary', group));
    const wrap = element('div', null, 'table-wrap');
    const metrics = element('table', null, 'metric-table');
    metrics.setAttribute('aria-label', group);
    const body = element('tbody');
    for (const metric of items) {
      const row = element('tr');
      const label = element('th', metric.label);
      label.scope = 'row';
      const location = metric.file + ' · ' + metric.key;
      label.title = location;
      label.append(element('small', location));
      if (metric.note) label.append(element('small', metric.note));
      const cell = element('td', metricValue(metric));
      cell.title = location;
      row.append(label, cell);
      body.append(row);
    }
    metrics.append(body);
    wrap.append(metrics);
    details.append(wrap);
    const used = files.filter((f) => items.some((item) => item.file === f.source_file));
    for (const f of used) {
      const stem = f.file.replace(/^validation\//, '').replace(/\.json$/, '');
      const figs = [...f.figures, ...allFigures.filter((x) => x.file.startsWith('fig/' + stem + '.')).map((x) => x.file)];
      for (const file of new Set(figs)) {
        const entry = figureByFile.get(file);
        if (!entry || placed.has(file)) continue;
        placed.add(file);
        details.append(figureBlock(entry, f.title || group));
      }
      const json = element('p', 'File · ', 'small');
      json.append(link(f.source_file, 'data/' + f.file));
      details.append(json);
    }
    table.append(details);
  }
  const rest = allFigures.filter((f) => !placed.has(f.file) && !f.shown_in?.includes('S06'));
  if (rest.length) {
    const details = element('details');
    details.append(element('summary', 'Other figures (image review sheets, radar, first hidden-known test)'));
    for (const entry of rest) details.append(figureBlock(entry, (entry.shown_in || []).join(', ')));
    table.append(details);
  }
  showSources(sources);
}

function showSources(sources) {
  const result = document.getElementById('sources');
  const filters = element('div', null, 'source-filters');
  const statusFilter = element('select');
  const challengeFilter = element('select');
  const option = (select, value, label) => {
    const o = element('option', label);
    o.value = value;
    select.append(o);
  };
  option(statusFilter, '', 'Every status');
  for (const value of new Set(sources.map((s) => s.status))) option(statusFilter, value, value);
  option(challengeFilter, '', 'Every source');
  option(challengeFilter, 'any', 'Challenge links only');
  for (const value of [...new Set(sources.map((s) => s.challenge_link_no).filter((v) => v != null))].sort((a, b) => a - b)) {
    option(challengeFilter, String(value), 'Challenge link ' + value);
  }
  const statusLabel = element('label', 'Status ');
  statusLabel.append(statusFilter);
  const challengeLabel = element('label', 'Challenge link ');
  challengeLabel.append(challengeFilter);
  const count = element('span', null, 'small');
  filters.append(statusLabel, challengeLabel, count);
  const wrap = element('div', null, 'table-wrap');
  const table = element('table', null, 'metric-table source-table');
  const head = element('thead');
  const hr = element('tr');
  hr.append(...['Source', 'Agency', 'Challenge link', 'Status', 'Licence or citation', 'Use'].map((t) => element('th', t)));
  head.append(hr);
  const body = element('tbody');
  table.append(head, body);
  wrap.append(table);
  function render() {
    body.replaceChildren();
    const rows = sources.filter((s) => (!statusFilter.value || s.status === statusFilter.value) &&
      (!challengeFilter.value || (challengeFilter.value === 'any' ? s.challenge_link_no != null :
        String(s.challenge_link_no) === challengeFilter.value)));
    for (const source of rows) {
      const row = element('tr');
      row.dataset.source = source.source_id;
      const urls = source.urls || sourceLinks(source.url);
      const name = element('th');
      name.scope = 'row';
      name.append(urls.length ? link(source.name, urls[0]) : element('strong', source.name));
      for (const url of urls.slice(1)) name.append(element('br'), link(url, url));
      if (source.needs_login) name.append(element('small', 'Login · ' + source.needs_login));
      row.append(name, element('td', source.agency), element('td', source.challenge_link_no == null ? '-' : String(source.challenge_link_no)),
        element('td', source.status), element('td', source.licence_or_citation), element('td', source.used_by));
      body.append(row);
    }
    count.textContent = number(rows.length, 0) + ' of ' + number(sources.length, 0) + ' sources';
  }
  statusFilter.addEventListener('change', render);
  challengeFilter.addEventListener('change', render);
  render();
  const tools = element('p', 'Application tools · ', 'small');
  tools.append(link('Leaflet (BSD-2-Clause)', 'https://github.com/Leaflet/Leaflet/blob/v1.9.4/LICENSE'),
    element('span', ' · '), link('Natural Earth land (public domain)', 'https://www.naturalearthdata.com/about/terms-of-use/'),
    element('span', ' · System typefaces.'));
  result.append(filters, wrap, tools);
}
