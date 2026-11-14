#!/usr/bin/env python3
"""Reproduce Polish lunar report figures from original JPL Horizons CSV rows.

Install: python3 -m pip install numpy matplotlib requests
Run: python3 scripts/make_figures.py (cached CSVs, no network if present)
Refresh: python3 scripts/make_figures.py --refresh
API / data: https://ssd-api.jpl.nasa.gov/doc/horizons.html
Definitions: https://ssd.jpl.nasa.gov/horizons/manual.html
Libraries: https://numpy.org/ https://matplotlib.org/ https://requests.readthedocs.io/
Original code: Apache-2.0. JPL output metadata and original table rows retained
in the CSV comments/body. No local terrain correction or refraction is applied.
"""
import argparse
import csv
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/figures'
API = 'https://ssd.jpl.nasa.gov/api/horizons.api'
NAVY, ORANGE, RED = '#0B3D91', '#F59E0B', '#FC3D21'
START = datetime(2027, 1, 1)
STOP = datetime(2027, 3, 1)
NROWS = int((STOP - START).total_seconds() / 3600) + 1
SITES = {
    'sun_apollo11': ('10', '23.47,0.67,0'),
    'sun_south_pole': ('10', '0,-89.5,0'),
    'earth_south_pole': ('399', '0,-89.5,0'),
}


def load_series(key, refresh=False):
    path = OUT / 'data' / (key + '.csv')
    target, site = SITES[key]
    params = dict(format='json', COMMAND=f"'{target}'", OBJ_DATA="'NO'",
                  MAKE_EPHEM="'YES'", EPHEM_TYPE="'OBSERVER'",
                  CENTER="'coord@301'", COORD_TYPE="'GEODETIC'",
                  SITE_COORD=f"'{site}'", START_TIME="'2027-01-01'",
                  STOP_TIME="'2027-03-01'", STEP_SIZE="'1 h'",
                  QUANTITIES="'4'", CSV_FORMAT="'YES'", TIME_TYPE="'UT'",
                  APPARENT="'AIRLESS'", ELEV_CUT="'-90'")
    if refresh or not path.exists():
        response = requests.get(API, params=params, timeout=120)
        response.raise_for_status()
        payload = response.json()
        result = payload.get('result', '')
        if payload.get('error') or '$$SOE' not in result or '$$EOE' not in result:
            raise RuntimeError(payload.get('error') or result[:2000])
        before, body = result.split('$$SOE', 1)
        body, after = body.split('$$EOE', 1)
        headers = [line for line in before.splitlines() if 'Date__(' in line]
        if len(headers) != 1 or 'Azi_' not in headers[0] or 'Elev_' not in headers[0]:
            raise ValueError('Unexpected Horizons table columns')
        metadata = ['API: ' + API, 'parameters: ' + json.dumps(params),
                    'retrieved_utc: ' + datetime.now(timezone.utc).isoformat(),
                    'signature: ' + json.dumps(payload.get('signature', {}))]
        # Keep original JPL metadata, including model, site, units and definitions.
        comments = '\n'.join('# ' + line for line in metadata +
                             before.splitlines() + after.splitlines())
        candidate = comments + '\n' + headers[0].strip() + '\n' + body.strip() + '\n'
        parse_series(candidate)  # validate before replacing cache
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(candidate, encoding='utf-8')
    return parse_series(path.read_text(encoding='utf-8'))


def parse_series(text):
    lines = '\n'.join(line for line in text.splitlines() if not line.startswith('#'))
    rows = list(csv.reader(io.StringIO(lines)))
    header, data = rows[0], rows[1:]
    azcol = next(i for i, name in enumerate(header) if 'Azi_' in name)
    elcol = next(i for i, name in enumerate(header) if 'Elev_' in name)
    dates = [datetime.strptime(row[0].strip(), '%Y-%b-%d %H:%M') for row in data]
    az = np.array([float(row[azcol]) for row in data])
    el = np.array([float(row[elcol]) for row in data])
    if len(dates) != NROWS or dates[0] != START or dates[-1] != STOP:
        raise ValueError('Incomplete date range')
    if any(b - a != timedelta(hours=1) for a, b in zip(dates, dates[1:])):
        raise ValueError('Non-hourly samples')
    if not (np.isfinite(az).all() and np.isfinite(el).all() and
            ((az >= 0) & (az <= 360)).all() and (np.abs(el) <= 90).all()):
        raise ValueError('Invalid angles')
    days = np.array([(d - START).total_seconds() / 86400 for d in dates])
    return days, az, el


def figure(title, ylabel, footer, height=6.2):
    fig, ax = plt.subplots(figsize=(16 / 2.54, height), dpi=300)
    fig.subplots_adjust(left=.19, right=.96, bottom=.30, top=.66)
    fig.suptitle(title, x=.12, y=.97, ha='left', fontsize=17, weight='bold', color=NAVY)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.grid(alpha=.22)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=14)
    fig.text(.08, .03, footer, fontsize=14, va='bottom', linespacing=1.3)
    return fig, ax


def time_axis(ax):
    ax.set_xlim(0, 59)
    ax.set_xticks([0, 15, 30, 45, 59])
    ax.set_xlabel('Dni od 1 stycznia 2027 (UTC)', fontsize=14)


def horizon(ax):
    ax.axhline(0, color=RED, linewidth=1.2, linestyle='--')
    ax.text(.02, .02, 'horyzont = 0°', transform=ax.get_yaxis_transform(),
            color=RED, fontsize=14, va='bottom')


def save(fig, name):
    fig.savefig(OUT / name, dpi=300, facecolor='white',
                metadata={'Source': API, 'Description': 'JPL Horizons; no terrain correction'})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Fetch fresh Horizons data')
    args = parser.parse_args()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 14,
                         'axes.labelsize': 14, 'legend.fontsize': 14})
    OUT.mkdir(parents=True, exist_ok=True)
    apollo, polar, earth = [load_series(k, args.refresh) for k in SITES]
    days = polar[0]
    fig, ax = figure('Słońce: równik i biegun',
                     'Wysokość Słońca\nnad horyzontem [°]',
                     '1 stycznia – 1 marca 2027, co godzinę.\nŹródło: JPL Horizons. Bez wpływu gór.')
    ax.plot(days, apollo[2], color=NAVY, label='Apollo 11 (blisko równika)', lw=2)
    ax.plot(days, polar[2], color=ORANGE, label='Okolice bieguna (89,5°S)', lw=2)
    horizon(ax); time_axis(ax)
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), frameon=False)
    save(fig, 'fig_slonce_rownik_vs_biegun.png')

    fig, ax = figure('Mała górka może\nzasłonić Słońce',
                     'Wysokość Słońca\nnad horyzontem [°]',
                     'Pas: przybliżona tarcza Słońca (0,5°).\n89,5°S, 0°E. Źródło: JPL Horizons.\nBez wpływu rzeczywistych gór.')
    ax.fill_between(days, polar[2] - .25, polar[2] + .25, color=ORANGE,
                    alpha=.35, label='Tarcza Słońca (około 0,5°)')
    ax.plot(days, polar[2], color=NAVY, lw=2, label='Środek Słońca')
    ax.set_ylim(-3, 3); horizon(ax); time_axis(ax)
    ax.text(.04, .10, 'Nawet mała górka\nzasłoni Słońce', transform=ax.transAxes,
            fontsize=14, color=NAVY, bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), frameon=False)
    save(fig, 'fig_slonce_biegun_zoom.png')

    fig, ax = figure('Ziemia może znikać\nponiżej horyzontu',
                     'Wysokość Ziemi\nnad horyzontem [°]',
                     'Znak kąta środka Ziemi to uproszczenie.\nBez gór i rozmiaru tarczy; widoczność\nnie gwarantuje łączności. JPL Horizons.', height=6.2)
    visible = earth[2] > 0
    # Vertical intervals classify the center of Earth relative to smooth horizon.
    bounds = np.r_[0, np.flatnonzero(visible[1:] != visible[:-1]) + 1, len(days)]
    for a, b in zip(bounds[:-1], bounds[1:]):
        left = days[a] if a == 0 else (days[a-1] + days[a]) / 2
        right = days[-1] if b == len(days) else (days[b-1] + days[b]) / 2
        ax.axvspan(left, right, color='#D9EAD3' if visible[a] else '#E3E5E8', zorder=0)
    ax.plot(days, earth[2], color=NAVY, lw=2)
    horizon(ax); time_axis(ax)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color='#D9EAD3', label='Ziemia widoczna – łączność możliwa'),
                       Patch(color='#E3E5E8', label='Ziemia poniżej – brak łączności')],
              loc='lower center', bbox_to_anchor=(.5, 1.01), frameon=False, fontsize=14)
    save(fig, 'fig_ziemia_biegun.png')

    fig, ax = figure('Słońce wędruje\nwokół horyzontu',
                     'Wysokość nad\nhoryzontem [°]',
                     'Przykładowe góry – ilustracja, nie dane.\nTor Słońca: JPL Horizons, 89,5°S, 0°E.\nStyczeń 2027. Krzyżyki: zasłonięte\nprzez przykładowe góry.', height=6.8)
    fig.subplots_adjust(bottom=.46, top=.80)
    directions = np.linspace(0, 360, 721)
    def mountains(x):
        return .15 + 1.7*np.exp(-((x-95)/22)**2) + 1.1*np.exp(-((x-245)/34)**2)
    ax.fill_between(directions, -3, mountains(directions), color='#9BA3AD', alpha=.65)
    month = days < 31
    az, el, d = polar[1][month], polar[2][month], days[month]
    dots = ax.scatter(az, el, c=d, cmap='viridis', s=9, zorder=3, vmin=0, vmax=31)
    blocked = el < mountains(az)
    ax.scatter(az[blocked][::8], el[blocked][::8], marker='x', color=RED, s=18, zorder=4)
    ax.axhline(0, color=RED, ls='--', lw=1)
    ax.set(xlim=(0,360), ylim=(-3,3), xticks=[0,90,180,270,360],
           xlabel='Kierunek patrzenia [°]')
    cax = fig.add_axes([.19, .32, .77, .025])
    cb = fig.colorbar(dots, cax=cax, orientation='horizontal', ticks=[0,10,20,30])
    cb.ax.set_xticklabels(['1 I', '11 I', '21 I', '31 I'])
    cb.ax.tick_params(labelsize=14)
    cb.set_label('Data w styczniu 2027 (UTC)', fontsize=14)
    save(fig, 'fig_slonce_dookola_horyzontu.png')
    for key, (_, _, el) in zip(SITES, [apollo, polar, earth]):
        print(f'{key}: {len(el)} rows, elevation {el.min():.3f} .. {el.max():.3f} deg')
    print('Saved 4 PNGs at 300 dpi, width 16 cm; 3 original Horizons CSV tables.')


if __name__ == '__main__':
    main()
