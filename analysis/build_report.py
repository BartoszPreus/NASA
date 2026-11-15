"""Builds the internal team report docs/RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf from the analysis results.
The committed PDF was built on 14 Nov 2026 from the Polish version of this script and is in Polish; the texts below
were translated to English on 15 Nov 2026 (issue #27), so a rerun writes an English report over it.
Run: .venv/Scripts/python analysis/build_report.py      (needs reportlab, matplotlib; Arial from Windows fonts)
Written with SI assistance (Claude Code).
"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image,
                                ListFlowable, ListItem, KeepTogether)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf")
FIG = os.path.join(ROOT, "scratch", "figs")
os.makedirs(FIG, exist_ok=True)

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")
plt.rcParams["font.family"] = "Arial"

NAVY, BLUE, ORANGE, GREY, LIGHT = "#1f2a44", "#2f6db5", "#d9822b", "#8a8f98", "#eef2f7"
P = ParagraphStyle("p", fontName="Arial", fontSize=9.5, leading=13.5, spaceAfter=5)
SMALL = ParagraphStyle("small", parent=P, fontSize=8, leading=10.5, textColor=colors.HexColor("#444444"))
CELL = ParagraphStyle("cell", parent=P, fontSize=8, leading=10, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Arial-Bold")
H1 = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=15, leading=19, textColor=colors.HexColor(NAVY), spaceBefore=10, spaceAfter=7)
H2 = ParagraphStyle("h2", fontName="Arial-Bold", fontSize=11.5, leading=15, textColor=colors.HexColor(BLUE), spaceBefore=8, spaceAfter=4)
TITLE = ParagraphStyle("title", fontName="Arial-Bold", fontSize=24, leading=29, textColor=colors.HexColor(NAVY), spaceAfter=8)
SUB = ParagraphStyle("sub", fontName="Arial", fontSize=12, leading=16, textColor=colors.HexColor("#444444"), spaceAfter=4)
BOX = ParagraphStyle("box", parent=P, backColor=colors.HexColor(LIGHT), borderPadding=7, leading=14, spaceBefore=4, spaceAfter=10)


def para(t, s=P):
    return Paragraph(t, s)


def bullets(items):
    return ListFlowable([ListItem(para(i), leftIndent=12) for i in items], bulletType="bullet", bulletFontSize=6, leftIndent=12, bulletOffsetY=-2)


def table(rows, widths, header=True, align_num_from=None):
    data = [[Paragraph(str(c), CELLB if (header and i == 0) else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c8ced6")),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(LIGHT)))
    t.setStyle(TableStyle(st))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 7.5); canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18 * mm, 10 * mm, "Zodiak · NASA Space Apps 2026 · internal report · prepared with SI assistance (Claude Code), not reviewed")
    canvas.drawRightString(192 * mm, 10 * mm, "%d" % doc.page)
    canvas.restoreState()


def fnum(x, d=2):
    return ("%." + str(d) + "f") % x


# ---------------------------------------------------------------- data
pilot = json.load(open(os.path.join(HERE, "pilot_scan_results.json")))["tiles"]
disc_path = os.path.join(HERE, "discovery_test_results.json")
disc = json.load(open(disc_path)) if os.path.exists(disc_path) else None

# ---------------------------------------------------------------- figures
def fig_profile():
    b = [57, 225, 560]
    rows = [("Connecting Ridge (Moon)", [8.14, 7.74, 7.36], NAVY, "-"), ("Meteor Crater", [2.40, 2.27, 2.37], ORANGE, "-"),
            ("Morasko (forest)", [1.88, 1.47, 1.32], "#4a9a5b", "--"), ("Farm field (control)", [0.29, 0.18, 0.14], GREY, "--")]
    fig, ax = plt.subplots(figsize=(6.3, 2.9), dpi=200)
    for n, v, c, ls in rows:
        ax.plot(b, v, marker="o", color=c, ls=ls, lw=1.8, ms=4)
        ax.annotate(n, (b[-1], v[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=c)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(b); ax.set_xticklabels(["57 m", "225 m", "560 m"])
    ax.set_yticks([0.1, 0.3, 1, 3, 10]); ax.set_yticklabels(["0.1°", "0.3°", "1°", "3°", "10°"]); ax.set_xlim(50, 2600)
    ax.set_xlabel("slope baseline", fontsize=8); ax.set_ylabel("median slope", fontsize=8)
    ax.tick_params(labelsize=8); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", lw=0.3, alpha=0.5)
    p = os.path.join(FIG, "profile.png"); fig.tight_layout(); fig.savefig(p); plt.close(fig); return p


def fig_pilot():
    rows = [r for r in pilot if r["moonlike_bare"] is not None]
    rows.sort(key=lambda r: r["moonlike_bare"])
    fig, ax = plt.subplots(figsize=(6.3, 5.4), dpi=200)
    y = range(len(rows))
    ax.barh(y, [100 * r["moonlike"] for r in rows], color="#cfd6e0", height=0.75, label="lunar (slopes only)")
    ax.barh(y, [100 * r["moonlike_bare"] for r in rows], color=[ORANGE if r["known"] else BLUE for r in rows], height=0.45,
            label="lunar and bare ground")
    ax.set_yticks(list(y)); ax.set_yticklabels([("* " if r["known"] else "") + r["label"] for r in rows], fontsize=7)
    ax.set_xlabel("share of 2 km cells in the tile, %", fontsize=8); ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.legend(fontsize=7, loc="lower right", frameon=False)
    p = os.path.join(FIG, "pilot.png"); fig.tight_layout(); fig.savefig(p); plt.close(fig); return p


def fig_disc():
    rows = [r for r in disc["tiles"] if r["amp_all"] is not None and r["land"] > 200]
    rows.sort(key=lambda r: r["amp_all"])
    fig, ax = plt.subplots(figsize=(6.3, 5.4), dpi=200)
    y = list(range(len(rows)))
    ax.barh([i + 0.2 for i in y], [100 * r["amp_all"] for r in rows], color="#cfd6e0", height=0.4, label="amplitude only (slope + roughness)")
    ax.barh([i - 0.2 for i in y], [100 * r["full_all"] for r in rows], color=BLUE, height=0.4, label="amplitude + closed depressions + coherence")
    ax.set_yticks(y); ax.set_yticklabels([("* " if r["known"] else "") + r["label"] for r in rows], fontsize=7)
    ax.set_xlabel("share of land cells inside the 90% envelope of the Moon, % (no land-cover mask)", fontsize=8)
    ax.tick_params(axis="x", labelsize=8); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.legend(fontsize=7, loc="lower right", frameon=False)
    p = os.path.join(FIG, "disc.png"); fig.tight_layout(); fig.savefig(p); plt.close(fig); return p


def img(path, width_mm):
    from PIL import Image as PI
    w, h = PI.open(path).size
    return Image(path, width=width_mm * mm, height=width_mm * mm * h / w)


# ---------------------------------------------------------------- story
S = []
S += [Spacer(1, 40 * mm), para("Moon analogs on Earth", TITLE),
      para("Report on the validation of the idea, the choice of criteria and the effectiveness of the search", SUB),
      para("Team Zodiak · NASA Space Apps Challenge 2026 · Poznań", SUB), Spacer(1, 6 * mm),
      para("State on Saturday 14 Nov 2026, about 17:15. Submission deadline: Sunday 15 Nov 2026, 13:30.", P),
      para("Challenge: <i>Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars</i>. "
           "Version of 15 Nov 2026: the description of the second, abandoned project track was removed; the other numbers are as of 14 Nov.", P),
      Spacer(1, 8 * mm),
      para("<b>How to read this report.</b> The numbers in chapters 2, 3 and 6 come from scripts run on data "
           "(folder <font face='Arial-Bold'>analysis/</font> in the repository). Chapter 4 summarises the review of literature and documentation; "
           "its full version with the verification status of every source is in the file "
           "<font face='Arial-Bold'>docs/moon-analogs/KRYTERIA-DEEP-RESEARCH.md</font>. The report was prepared by Wiktor with SI assistance (Claude Code); "
           "it was not reviewed by a second person.", BOX),
      PageBreak()]

# 1
S += [para("1. Summary and recommendation", H1),
      para("<b>The idea works, with caveats.</b> NASA and partner data download without an account, the same code computes terrain features "
           "for the Moon and Earth, and in the pilot scan known analogs come out high and flat controls low. "
           "Terrain steepness alone is not enough to point to new places: it lets ordinary mountains through.", BOX),
      para("Key findings", H2),
      bullets([
          "<b>Data access:</b> lunar roughness maps (PGDA 70, 108 MB), the 20 m south-pole elevation model (PGDA 90), "
          "Copernicus DEM 30 m and ESA WorldCover land cover work anonymously.",
          "<b>Separating terrains:</b> Meteor Crater lies closer to the Moon than a farm field (distance 2.07 vs 6.37), "
          "but is still 3.4 times less steep than Connecting Ridge.",
          "<b>Scan of 38 tiles:</b> Devon Island 51%, Atacama 32% \"lunar and bare\" cells; Wielkopolska 0%, Sahara dunes 2%. "
          "The Tatras and the Alps have 36% and 34% before the bare-ground mask is applied.",
          "<b>Criteria:</b> the reference for the pole should be the gridded PGDA 90 product (baselines 200-1600 m), not the 57/225/560 m maps. "
          "Temperature and rock abundance are not suitable for scoring.",
          "<b>Effectiveness:</b> adding closed depressions removes false hits. Tassili n'Ajjer, the best \"new\" candidate of the pilot, "
          "drops from 15% to 1%; volcanic and polar terrain remain.",
          "<b>Novelty:</b> in the peer-reviewed literature we found no global search for Moon analogs by elevation model. "
          "Other Space Apps 2026 teams compute similar features, though, so slopes alone are not a distinguishing feature.",
      ]),
      para("Recommendation", H2),
      para("We go for Moon analogs. Conditions: the team switches the challenge in the portal (the team owner does this) "
           "and one person takes responsibility for the scientific part."),
      para("What is still open", H2),
      bullets([
          "The novelty of the candidates that remained after the test (Ellesmere, Kunlun, Altiplano, Gobi Altai) was not checked in the literature.",
          "The agreement test of our code with a ready NASA map (chapter 5, test T1) has not been done yet; there is only a rough cross-check with PGDA 70.",
          "We know the status of the Artemis programme after the changes of early 2026 only from secondary sources.",
      ]),
      PageBreak()]

# 2
S += [para("2. State of the project at the time of the report", H1),
      table([["", "Moon analogs"],
             ["Challenge", "open: find and characterise new analogs, \"surprise us\""],
             ["Data", "PGDA 108 MB + DEM tiles about 35 MB, no account"],
             ["What already works", "terrain features, scan of 38 tiles, ranking, land-cover mask"],
             ["To do", "larger scan, topological features, map with site cards, novelty filter"],
             ["Biggest risk", "jury questions about the credibility of the method; change of challenge in the portal"],
             ["Strong jury criteria", "Creativity, Relevance"]], [36, 138]),
      PageBreak()]

# 3
S += [para("3. Moon: validation of the idea on data", H1),
      para("3.1. Data access", H2),
      table([["Source", "Format", "Size", "Account"],
             ["NASA PGDA 70: slopes 57/225/560 m + Hurst (LOLA)", "PDS3 IMG, int16, global grid", "108 MB", "no"],
             ["NASA PGDA 90: 20 m south-pole elevation model (LOLA)", "GeoTIFF COG, polar projection", "2.6 GB; read in windows", "no"],
             ["Copernicus DEM GLO-30 (AWS Open Data)", "GeoTIFF, 1° tiles", "2.5-46 MB per tile", "no"],
             ["ESA WorldCover 2021", "GeoTIFF COG, read remotely", "no download", "no"]], [78, 46, 34, 16]),
      para("3.2. Does the method separate terrains", H2),
      para("Median slope in a 2 × 2 km window, i.e. at the scale of one pixel of the lunar map. The distance is the Euclidean norm "
           "in the space of the logarithms of the three slopes."),
      table([["Place", "57 m", "225 m", "560 m", "560/57", "Distance"],
             ["Connecting Ridge, Moon 89.45°S", "8.14°", "7.74°", "7.36°", "0.90", "0"],
             ["Meteor Crater", "2.40°", "2.27°", "2.37°", "0.99", "2.07"],
             ["Morasko (55% forest)", "1.88°", "1.47°", "1.32°", "0.70", "2.80"],
             ["Farm field 52.30°N 16.52°E", "0.29°", "0.18°", "0.14°", "0.49", "6.37"]], [64, 20, 20, 20, 22, 28]),
      Spacer(1, 2 * mm), img(fig_profile(), 150),
      para("Fig. 1. The lunar profile hardly depends on scale, like Meteor Crater; on the field the slope halves with the baseline.", SMALL),
      bullets([
          "<b>The Hurst exponent is out:</b> for Meteor Crater it comes out as 0.40 or 0.83 depending on the window, and at the lunar pole it has a median of 0.98.",
          "<b>The result depends on the window:</b> at 4 × 4 km Meteor Crater drops to 0.76° at the 57 m baseline.",
          "<b>Copernicus measures tree crowns</b>, so Morasko is overestimated. The noise floor on flat terrain is 0.3-0.4° at 57 m.",
      ]),
      PageBreak(),
      para("3.3. Pilot scan: 38 Earth tiles", H2),
      para("A cell of about 2 km is \"lunar\" when its three slopes lie inside the 90% ellipsoid of the distribution of lunar pixels "
           "south of 80°S (median 5.09° / 4.89° / 4.67°). Colour marks cells that are at the same time more than 80% bare ground. "
           "An asterisk (*) and orange mark known analogs."),
      img(fig_pilot(), 150),
      para("Fig. 2. Share of lunar cells in the tile. Grey bar: slopes only. Coloured: after the bare-ground mask.", SMALL),
      bullets([
          "Known analogs are at the top, flat controls at the bottom: the method passes the common-sense test.",
          "The grey bars for the Tatras, the Alps and Tenerife show that slopes alone let forested mountains through.",
          "The tiles were chosen by hand (38 of about 26 thousand), so this is a pilot, not a global ranking.",
      ]),
      PageBreak()]

# 4
S += [para("4. Criteria for comparing places", H1),
      para("Selection rule: a feature enters the ranking only if it can be computed with the same code on both bodies, "
           "at a baseline above the noise floor of both sources. The rest goes on the site card as description or as \"here the analogy breaks down\"."),
      para("4.1. Two lunar references that must not be mixed", H2),
      table([["", "PGDA 70 (Rosenburg 2011)", "PGDA 90 (Barker 2023)"],
             ["What it measures", "point-to-point slope along the laser tracks", "slope and roughness from a plane fit on the 20 m grid"],
             ["Baselines", "57, 225, 560 m", "100, 200, 400, 800, 1600 m"],
             ["Coverage and grid", "global, 16 pixels per degree (coarse at the pole)", "south pole, 20-50 m"],
             ["Counterpart on Earth", "only ICESat-2 profiles", "any good elevation model"],
             ["Role for us", "auxiliary feature", "main reference"]], [34, 70, 70]),
      Spacer(1, 2 * mm),
      para("A 20 m pixel in the lunar model is not the resolution: only 15-75% of the pixels contain an actual laser measurement. "
           "Copernicus is reliable from a baseline of about 200 m and only on bare ground.", SMALL),
      para("4.2. Catalogue of parameters", H2),
      para("Order from the most important. The \"Status\" column says whether we checked the criterion on data.", P),
      table([["No.", "Criterion", "Role", "Data (Moon / Earth)", "Status"],
             ["1", "Bare ground: no vegetation, buildings, water", "hard filter", "not applicable / ESA WorldCover", "checked; without it the ranking is useless"],
             ["2", "Slope and roughness at baselines 200-1600 m", "scored, core", "PGDA 90 / Copernicus 30 m", "checked (ch. 6)"],
             ["3", "Closed depressions: area share and depth", "scored, core", "20 m model / same algorithm", "checked: Moon 1.8%, Earth usually below 0.4%"],
             ["4", "No ice and snow", "hard filter", "not applicable / WorldCover, MODIS", "to do; glaciers inflate the score"],
             ["5", "A specific target region instead of the whole pole", "target definition", "PGDA 78 and 104 rasters", "to do"],
             ["6", "Novelty: distance from known analogs", "result filter", "list of about 35 places with coordinates", "to do; by hand for the top five"],
             ["7", "Shape of the slope distribution (Wasserstein distance)", "scored", "from criterion 2", "untested"],
             ["8", "Share of terrain below 5° and 8° (landing) and 15°/20°/25° (driving)", "scored, mission language", "PGDA 78, 104 / Copernicus, lidar", "untested; thresholds from NASA documents"],
             ["9", "Confirmation with 1-2 m lidar or an ICESat-2 profile", "second stage", "5 m models / USGS 3DEP, GUGiK, ArcticDEM, SlideRule", "access confirmed, not used"],
             ["10", "Share of shadow at Sun elevation 1.5° and 5°", "scored, extra", "PGDA 69 / same horizon code", "untested; 4-6 h of work"],
             ["11", "Point-to-point slope 57/225/560 m", "auxiliary", "PGDA 70 / Copernicus from 225 m", "checked; 57 m below the noise floor"],
             ["12", "Lithology: anorthosite, basalt, other", "description, category", "anorthositic highlands / GLiM map", "untested"],
             ["13", "Aridity and permafrost", "description, flag", "zero; ice in shadow / IMERG, Permafrost CCI", "untested"],
             ["14", "Access: road, airport, land protection", "description, separate axis", "not applicable / OpenStreetMap, WDPA", "untested"],
             ["15", "Local relief and hypsometry", "auxiliary", "20 m model / Copernicus", "baseline of the competition"],
             ["16", "Gradient coherence (anisotropy)", "drop from the ranking", "20 m model / Copernicus", "checked: adds nothing"],
             ["17", "Surface temperature", "do not score", "Diviner / MODIS LST", "ranges do not overlap (110 K vs 175 K)"],
             ["18", "Rock abundance, thermal inertia, radar, albedo", "do not score", "Diviner to ±60-70°, Mini-RF / no counterpart", "pole not covered or no pair"],
             ["19", "Hurst exponent", "drop", "0.98 at the pole / unstable from 30 m", "checked: does not discriminate"]],
            [9, 56, 27, 44, 38]),
      Spacer(1, 2 * mm),
      para("Never scored: 1/6 g gravity, vacuum, radiation, regolith properties. "
           "Mars is possible only from baselines of about 0.6-1 km (MOLA shot spacing about 300 m).", SMALL),
      para("4.3. Agreement with the file \"challenge and choice of criteria\"", H2),
      para("The file <font face='Arial-Bold'>WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md</font> chooses terrain as the leading dimension, "
           "landing and mobility as the frame, and bare ground and temperature as supporting dimensions. The direction agrees; "
           "the source review changes three points."),
      table([["Point in the criteria file", "What the review showed", "Consequence"],
             ["Supporting dimension: temperature (Diviner + MODIS LST)", "the coldest surface on Earth is about 175 K, lunar cold traps below 110 K", "do not score; describe as a place where the analogy breaks down"],
             ["Optionally rock abundance from Diviner", "the maps end at ±60° or ±70°", "drop"],
             ["Leading dimension: slopes 57/225/560 m", "a statistic along the laser tracks; Copernicus reliable from about 200 m", "PGDA 90 reference, baselines 200-1600 m"]], [54, 64, 56]),
      para("What the criteria file does not have", H2),
      bullets([
          "Closed depressions, i.e. the feature that separates cratered terrain from terrain carved by water.",
          "A test of our own code on a ready NASA product.",
          "A two-stage scheme: global scan, then confirmation with lidar or ICESat-2.",
          "Target regions defined by the extent of NASA rasters for Artemis sites.",
          "Engineering thresholds for landing and driving.",
          "A measurement of the search effectiveness (chapter 6).",
          "The information that other teams already compute relief, slope percentiles and hypsometry.",
      ]),
      para("4.4. How the 12 \"potential considerations\" relate to the chosen criteria", H2),
      table([["Consideration from the challenge text", "How we answer it"],
             ["Think beyond visual similarity", "terrain shape from an elevation model, not the look of an image"],
             ["Different dimensions; does not have to match everything", "result separately for roughness, slope distribution and depressions"],
             ["Look beyond well-known sites; Surprise us", "filter of known analogs + manual check of the top five"],
             ["Consider scale", "2 km cells and 15 × 15 km regions; reported stability under a change of window"],
             ["Connect your analog to exploration", "landing and driving thresholds; test ranges for lander lidars"],
             ["Remember Earth's limits", "a fixed block on the site card"],
             ["Use multiple datasets", "LOLA + Copernicus + WorldCover + lidar or ICESat-2 for the short list"]], [70, 104]),
      PageBreak()]

# 5 validation tests
S += [para("5. Tests that separate an index from a pretty map", H1),
      table([["Test", "What it checks", "Pass criterion", "Time"],
             ["T1. Reproducing the NASA product", "our code on the 20 m lunar model vs the ready 200 m slope map", "agreement to a few tenths of a degree", "1-2 h"],
             ["T2. Profile vs grid", "point-to-point slopes from the model vs the PGDA 70 map", "measured conversion factor", "1 h"],
             ["T3. Positive and negative controls", "known analogs vs forested mountains and random cells", "analogs higher than fluvial terrain", "2 h"],
             ["T4. Ranking stability", "change of window, weights, removal of one feature", "reported overlap of the top ten", "1-2 h"],
             ["T5. Lidar degradation", "1 m lidar averaged to 30 m vs Copernicus over Meteor Crater", "difference smaller than the spread between places", "2 h"],
             ["T6. Symmetric uncertainty", "error layers of both models converted to slope noise", "features only where the signal exceeds the noise", "1 h"]],
            [42, 62, 50, 20]),
      Spacer(1, 3 * mm),
      para("T1 is the most important: it turns the claim \"we compare quantitatively\" into something the jury can check. "
           "None of the competing teams reviewed describes such a step.")]

# 6 discovery effectiveness
S += [para("6. Effectiveness in finding undiscovered places", H1)]
if disc:
    mm_ = disc["moon_median"]
    S += [para("6.1. Test on data: do topological features increase selectivity", H2),
          para("The same code computed nine features in cells of about 2 km for a 160 × 160 km window around the lunar south pole "
               "(LOLA 20 m model averaged to 30 m) and for 38 Earth tiles. Two sets were compared: amplitude only "
               "(slope at 240 and 570 m, roughness at 200-1600 m) and amplitude with the share and depth of closed depressions and anisotropy. "
               "A cell is \"lunar\" when its Mahalanobis distance lies within the 90th percentile of the lunar cells."),
          para("Medians of the lunar cells: slope 240 m %s°, 570 m %s°; depression share %s; anisotropy %s." %
               (fnum(mm_["s240"]), fnum(mm_["s570"]), fnum(mm_["dep_frac"], 3), fnum(mm_["aniso"])), SMALL),
          img(fig_disc(), 150),
          para("Fig. 3. Share of land cells judged lunar, without a land-cover mask. The shorter the blue bar "
               "for the controls (Tatras, Alps), the better the topological features filter out fluvial terrain.", SMALL)]
    DISC_TEXT = os.path.join(HERE, "discovery_findings.json")
    if os.path.exists(DISC_TEXT):
        f = json.load(open(DISC_TEXT, encoding="utf-8"))
        S += [KeepTogether([table(f["table"], f["widths"]), Spacer(1, 2 * mm)]), bullets(f["bullets"])]
S += [para("6.2. What decides the effectiveness", H2),
      para("Effectiveness has two components here: the system should rank truly similar places high (accuracy) "
           "and at the same time not flood the list with ordinary mountains or places already known (selectivity and novelty)."),
      table([["Lever", "Why it raises effectiveness", "Cost"],
             ["The same estimator on both bodies, validated by test T1", "removes a systematic offset between the Moon and Earth, which today shifts the whole ranking", "1-2 h"],
             ["Closed depressions as a feature", "filter out terrain carved by water that has lunar steepness (measured in 6.1)", "ready in the pilot"],
             ["Masks: vegetation, water, ice, buildings", "remove false hits from tree crowns and smooth glaciers", "1-2 h"],
             ["Specific target regions instead of the whole pole", "a narrow target gives a sharper ranking than a 2.4-11.6° distribution", "1 h"],
             ["Area scan instead of hand-picked tiles", "undiscovered places are by definition where nobody looked", "a night of computing"],
             ["Grouping cells into contiguous areas", "a single 2 km cell can be chance; a 5-15 km area is a place fit for a test range", "1-2 h"],
             ["Novelty filter", "distance from a list of about 35 known analogs + manual check of the top five", "2 h"],
             ["Confirmation of the short list with lidar or ICESat-2", "checks candidates at baselines Copernicus does not see", "2-3 h"]], [56, 92, 26]),
      para("6.3. How to measure effectiveness before the pitch", H2),
      bullets([
          "<b>Hidden known analogs:</b> we remove e.g. Devon Island and Atacama from the list and check at which rank the ranking finds them. "
          "We report the result as \"k of n known places in the first 5% of cells\".",
          "<b>Negative controls:</b> the share of forested mountains, fields and dunes that pass the threshold. It should be close to zero.",
          "<b>Stability:</b> how many places of the top ten remain after a change of window and weights. A competing team itself reports a median of 4 of 10.",
          "<b>An honest description of novelty:</b> \"we did not find this place in the analog catalogues\", not \"nobody knows it\".",
      ]),
      para("6.4. What the system will not find", H2),
      bullets([
          "Forms smaller than about 100-200 m: boulders, small craters, caves and lava tubes.",
          "Places similar in material or temperature, but not in shape.",
          "Places under forest, because the surface model measures the tree crowns there.",
      ]),
      PageBreak()]

# 7 plan
S += [para("7. Plan for the remaining time", H1),
      table([["Track", "Scope", "Who decides"],
             ["Science", "reference population from PGDA 90, test T1, closed depressions, masks", "the person who answers to the jury"],
             ["Data and scan", "scan of bare-ground regions, grouping into areas, feature table", "column contract agreed first"],
             ["App", "map, ranking, site card with result per dimension and a \"where the analogy breaks down\" block", "after the contract is agreed"],
             ["Pitch and submission", "7 slides, 3 min pitch, English text, README with citations, description of SI use", "from the start, in parallel"]], [30, 104, 40]),
      para("Order if time runs out", H2),
      bullets(["Test T1 and masks.", "Closed depressions and ranking per dimension.", "Novelty filter for the top five.",
               "Site card and map.", "Engineering thresholds and a lidar close-up of Meteor Crater as extras for the pitch."]),
      para("Things that need a person", H2),
      bullets(["Change of challenge in the portal (team owner only).", "Confirmation of the Artemis programme status in a NASA release.",
               "Manual novelty check of the candidates.", "Copernicus DEM attribution text for the README."]),
      para("8. Risks", H1),
      table([["Risk", "How we limit it"],
             ["The jury asks whether a 30 m grid and laser profiles measure the same thing", "PGDA 90 reference and test T1 with a concrete number"],
             ["The ranking shows places already known", "novelty filter and careful wording"],
             ["Similar projects of other teams", "distinguishing features: validation on a NASA product, topology, two stages, lidar"],
             ["Numbers from unverified sources end up on a slide", "status of every source in the file KRYTERIA-DEEP-RESEARCH.md"],
             ["No time for the app", "fallback plan: static map and ranking table"]], [70, 104]),
      PageBreak()]

# 9 sources
S += [para("9. Sources", H1),
      para("Data and tools used in the computations", H2),
      bullets([
          "NASA PGDA 70, Lunar slopes and Hurst exponent: https://pgda.gsfc.nasa.gov/products/70 · Rosenburg et al. 2011, doi:10.1029/2010JE003716",
          "NASA PGDA 90, A New View of the Lunar South Pole from LOLA: https://pgda.gsfc.nasa.gov/products/90 · Barker et al. 2023, doi:10.3847/PSJ/acf3e1",
          "Copernicus DEM GLO-30 (ESA, DLR, Airbus), AWS Open Data: https://registry.opendata.aws/copernicus-dem/",
          "ESA WorldCover 2021 v200: https://registry.opendata.aws/esa-worldcover-vito/",
          "Libraries: numpy, scipy, rasterio, scikit-image, pandas, matplotlib, reportlab",
      ]),
      para("Literature and documentation (full list with verification status in KRYTERIA-DEEP-RESEARCH.md)", H2),
      bullets([
          "Kreslavsky and Head 2000, doi:10.1029/2000JE001259 · Kreslavsky et al. 2013, doi:10.1016/j.icarus.2013.04.027",
          "NASA PGDA 69 (polar illumination), 78 and 104 (5 m models of sites and regions): https://pgda.gsfc.nasa.gov/products/69, /78, /104",
          "Copernicus DEM Product Handbook v5.0: https://dataspace.copernicus.eu/",
          "Kumari et al. 2022, doi:10.3847/PSJ/ac88c2 (landing and mobility thresholds)",
          "Foucher et al. 2021, doi:10.1016/j.pss.2021.105162 (analog types and their limitations)",
          "Preston and Dartnell 2014, Int. J. Astrobiology 13, 81 (no defined criteria for assessing analogs)",
          "Lambert and Reimold 2023, doi:10.3389/fspas.2023.1186173 (scoring of impact craters)",
          "ESA CAFE Executive Summary: https://esamultimedia.esa.int/docs/gsp/C4000104716ExS.pdf",
          "Sanganeria 2026: https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/",
          "Challenges: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/ · "
          "https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/",
      ]),
      para("Files in the repository", H2),
      bullets(["docs/PODSUMOWANIE-KIERUNKOW.md: what we checked on the data before starting.", "docs/moon-analogs/KRYTERIA-DEEP-RESEARCH.md: full catalogue of criteria and sources.",
               "docs/moon-analogs/WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md: challenge text and choice of dimensions.",
               "analysis/: scripts and raw results (validate.py, pilot_scan.py, discovery_test.py, build_report.py)."])]

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                        title="Moon analogs on Earth: report of team Zodiak", author="Zodiak")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("written", OUT)
