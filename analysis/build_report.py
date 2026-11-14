"""Builds docs/RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf from the analysis results (Polish, internal team report).
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
    canvas.drawString(18 * mm, 10 * mm, "Zodiak · NASA Space Apps 2026 · raport wewnętrzny · przygotowany z pomocą SI (Claude Code), nierecenzowany")
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
    rows = [("Connecting Ridge (Księżyc)", [8.14, 7.74, 7.36], NAVY, "-"), ("Meteor Crater", [2.40, 2.27, 2.37], ORANGE, "-"),
            ("Morasko (las)", [1.88, 1.47, 1.32], "#4a9a5b", "--"), ("Pole uprawne (kontrola)", [0.29, 0.18, 0.14], GREY, "--")]
    fig, ax = plt.subplots(figsize=(6.3, 2.9), dpi=200)
    for n, v, c, ls in rows:
        ax.plot(b, v, marker="o", color=c, ls=ls, lw=1.8, ms=4)
        ax.annotate(n, (b[-1], v[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=c)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(b); ax.set_xticklabels(["57 m", "225 m", "560 m"])
    ax.set_yticks([0.1, 0.3, 1, 3, 10]); ax.set_yticklabels(["0,1°", "0,3°", "1°", "3°", "10°"]); ax.set_xlim(50, 2600)
    ax.set_xlabel("baza pomiaru nachylenia", fontsize=8); ax.set_ylabel("mediana nachylenia", fontsize=8)
    ax.tick_params(labelsize=8); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", lw=0.3, alpha=0.5)
    p = os.path.join(FIG, "profile.png"); fig.tight_layout(); fig.savefig(p); plt.close(fig); return p


def fig_pilot():
    rows = [r for r in pilot if r["moonlike_bare"] is not None]
    rows.sort(key=lambda r: r["moonlike_bare"])
    fig, ax = plt.subplots(figsize=(6.3, 5.4), dpi=200)
    y = range(len(rows))
    ax.barh(y, [100 * r["moonlike"] for r in rows], color="#cfd6e0", height=0.75, label="księżycowe (same nachylenia)")
    ax.barh(y, [100 * r["moonlike_bare"] for r in rows], color=[ORANGE if r["known"] else BLUE for r in rows], height=0.45,
            label="księżycowe i goły grunt")
    ax.set_yticks(list(y)); ax.set_yticklabels([("* " if r["known"] else "") + r["label"] for r in rows], fontsize=7)
    ax.set_xlabel("udział komórek 2 km w kaflu, %", fontsize=8); ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.legend(fontsize=7, loc="lower right", frameon=False)
    p = os.path.join(FIG, "pilot.png"); fig.tight_layout(); fig.savefig(p); plt.close(fig); return p


def fig_disc():
    rows = [r for r in disc["tiles"] if r["amp_all"] is not None and r["land"] > 200]
    rows.sort(key=lambda r: r["amp_all"])
    fig, ax = plt.subplots(figsize=(6.3, 5.4), dpi=200)
    y = list(range(len(rows)))
    ax.barh([i + 0.2 for i in y], [100 * r["amp_all"] for r in rows], color="#cfd6e0", height=0.4, label="tylko amplituda (nachylenie + szorstkość)")
    ax.barh([i - 0.2 for i in y], [100 * r["full_all"] for r in rows], color=BLUE, height=0.4, label="amplituda + zamknięte zagłębienia + koherencja")
    ax.set_yticks(y); ax.set_yticklabels([("* " if r["known"] else "") + r["label"] for r in rows], fontsize=7)
    ax.set_xlabel("udział komórek lądowych wewnątrz 90% obwiedni Księżyca, % (bez maski pokrycia terenu)", fontsize=8)
    ax.tick_params(axis="x", labelsize=8); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.legend(fontsize=7, loc="lower right", frameon=False)
    p = os.path.join(FIG, "disc.png"); fig.tight_layout(); fig.savefig(p); plt.close(fig); return p


def img(path, width_mm):
    from PIL import Image as PI
    w, h = PI.open(path).size
    return Image(path, width=width_mm * mm, height=width_mm * mm * h / w)


# ---------------------------------------------------------------- story
S = []
S += [Spacer(1, 40 * mm), para("Analogi Księżyca na Ziemi", TITLE),
      para("Raport z walidacji pomysłu, wyboru kryteriów i skuteczności wyszukiwania", SUB),
      para("Drużyna Zodiak · NASA Space Apps Challenge 2026 · Poznań", SUB), Spacer(1, 6 * mm),
      para("Stan na sobotę 14.11.2026, ok. 17:15. Termin oddania: niedziela 15.11.2026, 13:30.", P),
      para("Wyzwanie: <i>Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars</i>. "
           "Wersja z 15.11.2026: usunięto opis drugiej, porzuconej ścieżki projektu; pozostałe liczby są ze stanu z 14.11.", P),
      Spacer(1, 8 * mm),
      para("<b>Jak czytać ten raport.</b> Liczby w rozdziałach 2, 3 i 6 pochodzą ze skryptów uruchomionych na danych "
           "(folder <font face='Arial-Bold'>analysis/</font> w repozytorium). Rozdział 4 streszcza przegląd literatury i dokumentacji; "
           "jego pełna wersja ze statusem weryfikacji każdego źródła jest w pliku "
           "<font face='Arial-Bold'>docs/moon-analogs/KRYTERIA-DEEP-RESEARCH.md</font>. Raport przygotował Wiktor z pomocą SI (Claude Code); "
           "nie był recenzowany przez drugą osobę.", BOX),
      PageBreak()]

# 1
S += [para("1. Streszczenie i rekomendacja", H1),
      para("<b>Pomysł działa, z zastrzeżeniami.</b> Dane NASA i partnerów pobierają się bez konta, ten sam kod liczy cechy terenu "
           "dla Księżyca i Ziemi, a w skanie pilotażowym znane analogi wychodzą wysoko i płaskie kontrole nisko. "
           "Sama stromość terenu nie wystarcza do wskazywania nowych miejsc: przepuszcza zwykłe góry.", BOX),
      para("Najważniejsze ustalenia", H2),
      bullets([
          "<b>Dostęp do danych:</b> mapy chropowatości Księżyca (PGDA 70, 108 MB), model wysokości bieguna 20 m (PGDA 90), "
          "Copernicus DEM 30 m i pokrycie terenu ESA WorldCover działają anonimowo.",
          "<b>Rozróżnianie terenów:</b> Meteor Crater leży bliżej Księżyca niż pole uprawne (odległość 2,07 wobec 6,37), "
          "ale nadal jest 3,4 razy mniej stromy niż Connecting Ridge.",
          "<b>Skan 38 kafli:</b> Devon Island 51%, Atakama 32% komórek „księżycowych i gołych”; Wielkopolska 0%, wydmy Sahary 2%. "
          "Tatry i Alpy mają 36% i 34% przed nałożeniem maski gołego gruntu.",
          "<b>Kryteria:</b> wzorcem dla bieguna powinien być siatkowy produkt PGDA 90 (bazy 200–1600 m), a nie mapy 57/225/560 m. "
          "Temperatura i kamienistość nie nadają się do punktacji.",
          "<b>Skuteczność:</b> dodanie zamkniętych zagłębień usuwa fałszywe trafienia. Tassili n'Ajjer, najlepszy „nowy” kandydat pilotażu, "
          "spada z 15% do 1%; tereny wulkaniczne i polarne zostają.",
          "<b>Nowość:</b> w literaturze recenzowanej nie znaleźliśmy globalnego szukania analogów Księżyca po modelu wysokości. "
          "Inne zespoły Space Apps 2026 liczą jednak podobne cechy, więc same nachylenia nie są wyróżnikiem.",
      ]),
      para("Rekomendacja", H2),
      para("Idziemy w analogi Księżyca. Warunki: zespół przełącza wyzwanie w portalu (robi to właściciel zespołu) "
           "i jedna osoba bierze odpowiedzialność za część naukową."),
      para("Co jest nadal otwarte", H2),
      bullets([
          "Nowość kandydatów, którzy zostali po teście (Ellesmere, Kunlun, Altiplano, Gobi Ałtaj), nie była sprawdzana w literaturze.",
          "Test zgodności naszego kodu z gotową mapą NASA (rozdział 5, test T1) nie został jeszcze wykonany; jest tylko zgrubna kontrola krzyżowa z PGDA 70.",
          "Status programu Artemis po zmianach z początku 2026 r. znamy tylko ze źródeł wtórnych.",
      ]),
      PageBreak()]

# 2
S += [para("2. Stan projektu w chwili raportu", H1),
      table([["", "Analogi Księżyca"],
             ["Wyzwanie", "otwarte: znaleźć i scharakteryzować nowe analogi, „surprise us”"],
             ["Dane", "PGDA 108 MB + kafle DEM ok. 35 MB, bez konta"],
             ["Co już działa", "cechy terenu, skan 38 kafli, ranking, maska pokrycia terenu"],
             ["Do zrobienia", "większy skan, cechy topologiczne, mapa z kartami miejsc, filtr nowości"],
             ["Największe ryzyko", "pytania jury o wiarygodność metody; zmiana wyzwania w portalu"],
             ["Mocne kryteria jury", "Creativity, Relevance"]], [36, 138]),
      PageBreak()]

# 3
S += [para("3. Księżyc: walidacja pomysłu na danych", H1),
      para("3.1. Dostęp do danych", H2),
      table([["Źródło", "Format", "Rozmiar", "Konto"],
             ["NASA PGDA 70: nachylenia 57/225/560 m + Hurst (LOLA)", "PDS3 IMG, int16, siatka globalna", "108 MB", "nie"],
             ["NASA PGDA 90: model wysokości bieguna 20 m (LOLA)", "GeoTIFF COG, rzut biegunowy", "2,6 GB; czytany oknami", "nie"],
             ["Copernicus DEM GLO-30 (AWS Open Data)", "GeoTIFF, kafle 1°", "2,5–46 MB na kafel", "nie"],
             ["ESA WorldCover 2021", "GeoTIFF COG, czytany zdalnie", "bez pobierania", "nie"]], [78, 46, 34, 16]),
      para("3.2. Czy metoda rozróżnia tereny", H2),
      para("Mediana nachylenia w oknie 2 × 2 km, czyli w skali jednego piksela mapy księżycowej. Odległość to norma euklidesowa "
           "w przestrzeni logarytmów trzech nachyleń."),
      table([["Miejsce", "57 m", "225 m", "560 m", "560/57", "Odległość"],
             ["Connecting Ridge, Księżyc 89,45°S", "8,14°", "7,74°", "7,36°", "0,90", "0"],
             ["Meteor Crater", "2,40°", "2,27°", "2,37°", "0,99", "2,07"],
             ["Morasko (55% las)", "1,88°", "1,47°", "1,32°", "0,70", "2,80"],
             ["Pole uprawne 52,30°N 16,52°E", "0,29°", "0,18°", "0,14°", "0,49", "6,37"]], [64, 20, 20, 20, 22, 28]),
      Spacer(1, 2 * mm), img(fig_profile(), 150),
      para("Rys. 1. Księżycowy profil prawie nie zależy od skali, podobnie jak Meteor Crater; na polu nachylenie spada z bazą o połowę.", SMALL),
      bullets([
          "<b>Wykładnik Hursta odpada:</b> dla Meteor Crater wychodzi 0,40 albo 0,83 zależnie od okna, a na biegunie Księżyca ma medianę 0,98.",
          "<b>Wynik zależy od okna:</b> przy 4 × 4 km Meteor Crater spada do 0,76° przy bazie 57 m.",
          "<b>Copernicus mierzy korony drzew</b>, więc Morasko jest zawyżone. Próg szumu na płaskim terenie to 0,3–0,4° przy 57 m.",
      ]),
      PageBreak(),
      para("3.3. Skan pilotażowy: 38 kafli Ziemi", H2),
      para("Komórka ok. 2 km jest „księżycowa”, gdy jej trzy nachylenia mieszczą się w 90% elipsoidzie rozkładu pikseli Księżyca "
           "na południe od 80°S (mediana 5,09° / 4,89° / 4,67°). Kolor oznacza komórki, które są jednocześnie w ponad 80% gołym gruntem. "
           "Gwiazdka (*) i kolor pomarańczowy to znane analogi."),
      img(fig_pilot(), 150),
      para("Rys. 2. Udział komórek księżycowych w kaflu. Szary pasek: same nachylenia. Kolorowy: po masce gołego gruntu.", SMALL),
      bullets([
          "Znane analogi są na górze, płaskie kontrole na dole: metoda przechodzi test zdrowego rozsądku.",
          "Szare paski dla Tatr, Alp i Teneryfy pokazują, że same nachylenia przepuszczają zalesione góry.",
          "Kafle wybrano ręcznie (38 z ok. 26 tysięcy), więc to pilotaż, nie ranking globalny.",
      ]),
      PageBreak()]

# 4
S += [para("4. Kryteria porównania miejsc", H1),
      para("Zasada wyboru: cecha wchodzi do rankingu tylko wtedy, gdy da się ją policzyć tym samym kodem na obu ciałach, "
           "przy bazie powyżej progu szumu obu źródeł. Reszta trafia na kartę miejsca jako opis albo jako „tu analogia się łamie”."),
      para("4.1. Dwa wzorce Księżyca, których nie wolno mieszać", H2),
      table([["", "PGDA 70 (Rosenburg 2011)", "PGDA 90 (Barker 2023)"],
             ["Co mierzy", "nachylenie punkt-punkt wzdłuż śladów lasera", "nachylenie i szorstkość z dopasowania płaszczyzny na siatce 20 m"],
             ["Bazy", "57, 225, 560 m", "100, 200, 400, 800, 1600 m"],
             ["Zasięg i siatka", "globalny, 16 pikseli na stopień (zgrubny na biegunie)", "biegun południowy, 20–50 m"],
             ["Odpowiednik na Ziemi", "tylko profile ICESat-2", "dowolny dobry model wysokości"],
             ["Rola u nas", "cecha pomocnicza", "wzorzec główny"]], [34, 70, 70]),
      Spacer(1, 2 * mm),
      para("Piksel 20 m w modelu księżycowym to nie rozdzielczość: tylko 15–75% pikseli zawiera faktyczny pomiar lasera. "
           "Copernicus jest wiarygodny od bazy ok. 200 m i tylko na gołym gruncie.", SMALL),
      para("4.2. Katalog parametrów", H2),
      para("Kolejność od najważniejszego. Kolumna „Status” mówi, czy kryterium sprawdziliśmy na danych.", P),
      table([["Nr", "Kryterium", "Rola", "Dane (Księżyc / Ziemia)", "Status"],
             ["1", "Goły grunt: brak roślinności, zabudowy, wody", "filtr twardy", "nie dotyczy / ESA WorldCover", "sprawdzone; bez niego ranking jest bezużyteczny"],
             ["2", "Nachylenie i szorstkość przy bazach 200–1600 m", "punktowane, rdzeń", "PGDA 90 / Copernicus 30 m", "sprawdzone (rozdz. 6)"],
             ["3", "Zamknięte zagłębienia: udział powierzchni i głębokość", "punktowane, rdzeń", "model 20 m / ten sam algorytm", "sprawdzone: Księżyc 1,8%, Ziemia zwykle poniżej 0,4%"],
             ["4", "Brak lodu i śniegu", "filtr twardy", "nie dotyczy / WorldCover, MODIS", "do zrobienia; lodowce zawyżają wynik"],
             ["5", "Konkretny region docelowy zamiast całego bieguna", "definicja celu", "rastry PGDA 78 i 104", "do zrobienia"],
             ["6", "Nowość: odległość od znanych analogów", "filtr wyniku", "lista ok. 35 miejsc ze współrzędnymi", "do zrobienia; ręcznie dla pierwszej piątki"],
             ["7", "Kształt rozkładu nachyleń (odległość Wassersteina)", "punktowane", "z kryterium 2", "nietestowane"],
             ["8", "Udział terenu poniżej 5° i 8° (lądowanie) oraz 15°/20°/25° (jazda)", "punktowane, język misji", "PGDA 78, 104 / Copernicus, lidar", "nietestowane; progi z dokumentów NASA"],
             ["9", "Potwierdzenie lidarem 1–2 m lub profilem ICESat-2", "drugi stopień", "modele 5 m / USGS 3DEP, GUGiK, ArcticDEM, SlideRule", "dostęp potwierdzony, nieużyte"],
             ["10", "Udział cienia przy Słońcu 1,5° i 5°", "punktowane, dodatek", "PGDA 69 / ten sam kod horyzontu", "nietestowane; 4–6 h pracy"],
             ["11", "Nachylenie punkt-punkt 57/225/560 m", "pomocnicze", "PGDA 70 / Copernicus od 225 m", "sprawdzone; 57 m poniżej progu szumu"],
             ["12", "Litologia: anortozyt, bazalt, inne", "opis, kategoria", "wyżyny anortozytowe / mapa GLiM", "nietestowane"],
             ["13", "Suchość i zmarzlina", "opis, flaga", "zero; lód w cieniu / IMERG, Permafrost CCI", "nietestowane"],
             ["14", "Dostępność: droga, lotnisko, ochrona terenu", "opis, osobna oś", "nie dotyczy / OpenStreetMap, WDPA", "nietestowane"],
             ["15", "Relief lokalny i hipsometria", "pomocnicze", "model 20 m / Copernicus", "poziom wyjściowy konkurencji"],
             ["16", "Koherencja gradientu (anizotropia)", "odrzucić z rankingu", "model 20 m / Copernicus", "sprawdzone: nic nie wnosi"],
             ["17", "Temperatura powierzchni", "nie punktować", "Diviner / MODIS LST", "zakresy się nie pokrywają (110 K wobec 175 K)"],
             ["18", "Kamienistość, bezwładność cieplna, radar, albedo", "nie punktować", "Diviner do ±60–70°, Mini-RF / brak odpowiednika", "biegun nieobjęty lub brak pary"],
             ["19", "Wykładnik Hursta", "odrzucić", "0,98 na biegunie / niestabilny z 30 m", "sprawdzone: nie rozróżnia"]],
            [9, 56, 27, 44, 38]),
      Spacer(1, 2 * mm),
      para("Nigdy niepunktowane: grawitacja 1/6 g, próżnia, promieniowanie, właściwości regolitu. "
           "Mars jest możliwy dopiero od baz ok. 0,6–1 km (odstęp pomiarów MOLA ok. 300 m).", SMALL),
      para("4.3. Zgodność z plikiem „wyzwanie i wybór kryteriów”", H2),
      para("Plik <font face='Arial-Bold'>WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md</font> wybiera teren jako wymiar wiodący, "
           "lądowanie i mobilność jako ramę oraz goły grunt i temperaturę jako wymiary wspierające. Kierunek się zgadza; "
           "przegląd źródeł zmienia trzy punkty."),
      table([["Punkt w pliku kryteriów", "Co pokazał przegląd", "Skutek"],
             ["Wymiar wspierający: temperatura (Diviner + MODIS LST)", "najzimniejsza powierzchnia Ziemi ok. 175 K, zimne pułapki Księżyca poniżej 110 K", "nie punktować; opisać jako miejsce, gdzie analogia się łamie"],
             ["Opcjonalnie rock abundance z Divinera", "mapy kończą się na ±60° lub ±70°", "skreślić"],
             ["Wymiar wiodący: nachylenia 57/225/560 m", "statystyka wzdłuż śladów lasera; Copernicus wiarygodny od ok. 200 m", "wzorzec PGDA 90, bazy 200–1600 m"]], [54, 64, 56]),
      para("Czego w pliku kryteriów nie ma", H2),
      bullets([
          "Zamkniętych zagłębień, czyli cechy odróżniającej teren kraterowy od wyrzeźbionego przez wodę.",
          "Testu własnego kodu na gotowym produkcie NASA.",
          "Dwustopniowego schematu: skan globalny, potem potwierdzenie lidarem lub ICESat-2.",
          "Regionów docelowych zdefiniowanych zasięgiem rastrów NASA dla miejsc Artemis.",
          "Progów inżynierskich dla lądowania i jazdy.",
          "Pomiaru skuteczności wyszukiwania (rozdział 6).",
          "Informacji, że inne zespoły liczą już relief, percentyle nachyleń i hipsometrię.",
      ]),
      para("4.4. Jak 12 „potential considerations” ma się do wybranych kryteriów", H2),
      table([["Consideration z treści wyzwania", "Czym na nie odpowiadamy"],
             ["Think beyond visual similarity", "kształt terenu z modelu wysokości, nie wygląd zdjęcia"],
             ["Different dimensions; does not have to match everything", "wynik osobno dla szorstkości, rozkładu nachyleń i zagłębień"],
             ["Look beyond well-known sites; Surprise us", "filtr znanych analogów + ręczne sprawdzenie pierwszej piątki"],
             ["Consider scale", "komórki 2 km i regiony 15 × 15 km; raportowana stabilność przy zmianie okna"],
             ["Connect your analog to exploration", "progi lądowania i jazdy; poligony dla lidarów lądowników"],
             ["Remember Earth's limits", "stały blok na karcie miejsca"],
             ["Use multiple datasets", "LOLA + Copernicus + WorldCover + lidar lub ICESat-2 dla krótkiej listy"]], [70, 104]),
      PageBreak()]

# 5 validation tests
S += [para("5. Testy, które odróżnią indeks od ładnej mapy", H1),
      table([["Test", "Co sprawdza", "Kryterium zaliczenia", "Czas"],
             ["T1. Odtworzenie produktu NASA", "nasz kod na księżycowym modelu 20 m wobec gotowej mapy nachyleń 200 m", "zgodność do kilku dziesiątych stopnia", "1–2 h"],
             ["T2. Profil wobec siatki", "nachylenia punkt-punkt z modelu wobec mapy PGDA 70", "zmierzony współczynnik przeliczenia", "1 h"],
             ["T3. Kontrole dodatnie i ujemne", "znane analogi wobec zalesionych gór i losowych komórek", "analogi wyżej niż teren rzeczny", "2 h"],
             ["T4. Stabilność rankingu", "zmiana okna, wag, usunięcie jednej cechy", "raportowane pokrycie pierwszej dziesiątki", "1–2 h"],
             ["T5. Degradacja lidaru", "lidar 1 m uśredniony do 30 m wobec Copernicus nad Meteor Crater", "różnica mniejsza niż rozrzut między miejscami", "2 h"],
             ["T6. Symetryczna niepewność", "warstwy błędu obu modeli przeliczone na szum nachylenia", "cechy tylko tam, gdzie sygnał przekracza szum", "1 h"]],
            [42, 62, 50, 20]),
      Spacer(1, 3 * mm),
      para("T1 jest najważniejszy: zamienia deklarację „porównujemy ilościowo” w coś, co jury może sprawdzić. "
           "Żaden z przejrzanych zespołów konkurencyjnych takiego kroku nie opisuje.")]

# 6 discovery effectiveness
S += [para("6. Skuteczność w znajdowaniu nieodkrytych miejsc", H1)]
if disc:
    mm_ = disc["moon_median"]
    S += [para("6.1. Test na danych: czy cechy topologiczne zwiększają wybiórczość", H2),
          para("Ten sam kod policzył dziewięć cech w komórkach ok. 2 km dla okna 160 × 160 km wokół bieguna południowego Księżyca "
               "(model LOLA 20 m uśredniony do 30 m) oraz dla 38 kafli Ziemi. Porównano dwa zestawy: sama amplituda "
               "(nachylenie przy 240 i 570 m, szorstkość przy 200–1600 m) oraz amplituda z udziałem i głębokością zamkniętych zagłębień i anizotropią. "
               "Komórka jest „księżycowa”, gdy jej odległość Mahalanobisa mieści się w 90. percentylu komórek Księżyca."),
          para("Mediany komórek Księżyca: nachylenie 240 m %s°, 570 m %s°; udział zagłębień %s; anizotropia %s." %
               (fnum(mm_["s240"]), fnum(mm_["s570"]), fnum(mm_["dep_frac"], 3), fnum(mm_["aniso"])), SMALL),
          img(fig_disc(), 150),
          para("Rys. 3. Udział komórek lądowych uznanych za księżycowe, bez maski pokrycia terenu. Im krótszy niebieski pasek "
               "przy kontrolach (Tatry, Alpy), tym lepiej cechy topologiczne odsiewają teren rzeczny.", SMALL)]
    DISC_TEXT = os.path.join(HERE, "discovery_findings.json")
    if os.path.exists(DISC_TEXT):
        f = json.load(open(DISC_TEXT, encoding="utf-8"))
        S += [KeepTogether([table(f["table"], f["widths"]), Spacer(1, 2 * mm)]), bullets(f["bullets"])]
S += [para("6.2. Co decyduje o skuteczności", H2),
      para("Skuteczność ma tu dwa składniki: system ma wysoko stawiać miejsca naprawdę podobne (trafność) "
           "i jednocześnie nie zasypywać listy zwykłymi górami ani miejscami już znanymi (wybiórczość i nowość)."),
      table([["Dźwignia", "Dlaczego podnosi skuteczność", "Koszt"],
             ["Ten sam estymator na obu ciałach, zwalidowany testem T1", "usuwa systematyczne przesunięcie między Księżycem a Ziemią, które dziś przesuwa cały ranking", "1–2 h"],
             ["Zamknięte zagłębienia jako cecha", "odsiewają teren wyrzeźbiony przez wodę, który ma księżycową stromość (zmierzone w 6.1)", "gotowe w pilotażu"],
             ["Maski: roślinność, woda, lód, zabudowa", "usuwają fałszywe trafienia z koron drzew i gładkich lodowców", "1–2 h"],
             ["Konkretne regiony docelowe zamiast całego bieguna", "wąski cel daje ostrzejszy ranking niż rozkład 2,4–11,6°", "1 h"],
             ["Skan obszarowy zamiast ręcznie wybranych kafli", "nieodkryte miejsca są z definicji tam, gdzie nikt nie patrzył", "noc obliczeń"],
             ["Grupowanie komórek w spójne obszary", "pojedyncza komórka 2 km bywa przypadkiem; poligon 5–15 km to miejsce nadające się na poligon", "1–2 h"],
             ["Filtr nowości", "odległość od listy ok. 35 znanych analogów + ręczne sprawdzenie pierwszej piątki", "2 h"],
             ["Potwierdzenie krótkiej listy lidarem lub ICESat-2", "sprawdza kandydatów przy bazach, których Copernicus nie widzi", "2–3 h"]], [56, 92, 26]),
      para("6.3. Jak zmierzyć skuteczność przed pitchem", H2),
      bullets([
          "<b>Ukryte znane analogi:</b> usuwamy z listy np. Devon Island i Atakamę i sprawdzamy, na którym miejscu ranking je odnajduje. "
          "Wynik podajemy jako „k z n znanych miejsc w pierwszych 5% komórek”.",
          "<b>Kontrole ujemne:</b> udział zalesionych gór, pól i wydm, które przechodzą próg. Powinien być bliski zeru.",
          "<b>Stabilność:</b> ile miejsc z pierwszej dziesiątki zostaje po zmianie okna i wag. Konkurencyjny zespół sam podaje u siebie medianę 4 z 10.",
          "<b>Uczciwy opis nowości:</b> „nie znaleźliśmy tego miejsca w katalogach analogów”, a nie „nikt go nie zna”.",
      ]),
      para("6.4. Czego system nie znajdzie", H2),
      bullets([
          "Form mniejszych niż ok. 100–200 m: głazów, małych kraterów, jaskiń i tub lawowych.",
          "Miejsc podobnych materiałem lub temperaturą, ale nie kształtem.",
          "Miejsc pod lasem, bo model powierzchni mierzy tam korony drzew.",
      ]),
      PageBreak()]

# 7 plan
S += [para("7. Plan na pozostały czas", H1),
      table([["Tor", "Zakres", "Kto decyduje"],
             ["Nauka", "populacja odniesienia z PGDA 90, test T1, zamknięte zagłębienia, maski", "osoba, która odpowiada przed jury"],
             ["Dane i skan", "skan regionów gołego gruntu, grupowanie w obszary, tabela cech", "kontrakt kolumn ustalony jako pierwszy"],
             ["Aplikacja", "mapa, ranking, karta miejsca z wynikiem per wymiar i blokiem „gdzie analogia się łamie”", "po ustaleniu kontraktu"],
             ["Pitch i zgłoszenie", "7 slajdów, pitch 3 min, tekst po angielsku, README z cytowaniami, opis użycia SI", "od początku, równolegle"]], [30, 104, 40]),
      para("Kolejność, jeśli czasu zabraknie", H2),
      bullets(["Test T1 i maski.", "Zamknięte zagłębienia i ranking per wymiar.", "Filtr nowości dla pierwszej piątki.",
               "Karta miejsca i mapa.", "Progi inżynierskie i zbliżenie lidarowe na Meteor Crater jako dodatki na pitch."]),
      para("Rzeczy wymagające człowieka", H2),
      bullets(["Zmiana wyzwania w portalu (tylko właściciel zespołu).", "Potwierdzenie statusu programu Artemis w komunikacie NASA.",
               "Ręczne sprawdzenie nowości kandydatów.", "Tekst atrybucji Copernicus DEM do README."]),
      para("8. Ryzyka", H1),
      table([["Ryzyko", "Jak je ograniczamy"],
             ["Jury pyta, czy siatka 30 m i profile lasera mierzą to samo", "wzorzec PGDA 90 i test T1 z konkretną liczbą"],
             ["Ranking pokazuje miejsca już znane", "filtr nowości i ostrożne sformułowania"],
             ["Podobne projekty innych zespołów", "wyróżniki: walidacja na produkcie NASA, topologia, dwa stopnie, lidar"],
             ["Liczby ze źródeł niezweryfikowanych trafiają na slajd", "status każdego źródła w pliku KRYTERIA-DEEP-RESEARCH.md"],
             ["Brak czasu na aplikację", "plan awaryjny: statyczna mapa i tabela rankingu"]], [70, 104]),
      PageBreak()]

# 9 sources
S += [para("9. Źródła", H1),
      para("Dane i narzędzia użyte w obliczeniach", H2),
      bullets([
          "NASA PGDA 70, Lunar slopes and Hurst exponent: https://pgda.gsfc.nasa.gov/products/70 · Rosenburg i in. 2011, doi:10.1029/2010JE003716",
          "NASA PGDA 90, A New View of the Lunar South Pole from LOLA: https://pgda.gsfc.nasa.gov/products/90 · Barker i in. 2023, doi:10.3847/PSJ/acf3e1",
          "Copernicus DEM GLO-30 (ESA, DLR, Airbus), AWS Open Data: https://registry.opendata.aws/copernicus-dem/",
          "ESA WorldCover 2021 v200: https://registry.opendata.aws/esa-worldcover-vito/",
          "Biblioteki: numpy, scipy, rasterio, scikit-image, pandas, matplotlib, reportlab",
      ]),
      para("Literatura i dokumentacja (pełna lista ze statusem weryfikacji w KRYTERIA-DEEP-RESEARCH.md)", H2),
      bullets([
          "Kreslavsky i Head 2000, doi:10.1029/2000JE001259 · Kreslavsky i in. 2013, doi:10.1016/j.icarus.2013.04.027",
          "NASA PGDA 69 (oświetlenie biegunów), 78 i 104 (modele 5 m miejsc i regionów): https://pgda.gsfc.nasa.gov/products/69, /78, /104",
          "Copernicus DEM Product Handbook v5.0: https://dataspace.copernicus.eu/",
          "Kumari i in. 2022, doi:10.3847/PSJ/ac88c2 (progi lądowania i mobilności)",
          "Foucher i in. 2021, doi:10.1016/j.pss.2021.105162 (typy analogów i ich ograniczenia)",
          "Preston i Dartnell 2014, Int. J. Astrobiology 13, 81 (brak zdefiniowanych kryteriów oceny analogów)",
          "Lambert i Reimold 2023, doi:10.3389/fspas.2023.1186173 (punktacja kraterów uderzeniowych)",
          "ESA CAFE Executive Summary: https://esamultimedia.esa.int/docs/gsp/C4000104716ExS.pdf",
          "Sanganeria 2026: https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/",
          "Wyzwania: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/ · "
          "https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/",
      ]),
      para("Pliki w repozytorium", H2),
      bullets(["docs/PODSUMOWANIE-KIERUNKOW.md: co sprawdziliśmy na danych przed startem.", "docs/moon-analogs/KRYTERIA-DEEP-RESEARCH.md: pełny katalog kryteriów i źródeł.",
               "docs/moon-analogs/WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md: treść wyzwania i wybór wymiarów.",
               "analysis/: skrypty i surowe wyniki (validate.py, pilot_scan.py, discovery_test.py, build_report.py)."])]

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                        title="Analogi Księżyca na Ziemi: raport zespołu Zodiak", author="Zodiak")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("written", OUT)
