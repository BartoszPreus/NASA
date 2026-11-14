# Be An Earth System Trend Detective!
**Poziom:** Advanced · **Tematy:** Earth Science, Software
**Strona:** https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/
**Nasza ocena:** nieoceniane wcześniej. Dopisane, bo technicznie mocno pasuje do Pythona i statystyki.

## Zadanie (oficjalne streszczenie)
Change is always occurring in the Earth's interconnected environmental system, and when it runs in a consistent direction – rising or falling, increasing or decreasing, thickening or thinning – measured variables reflect it. But a measured Earth science data variable can trend one way in one region and the opposite way in another, even when the same process drives both. The multitude of Earth science data variables makes it difficult to select variables that could indicate change, and to then perform an analysis on the selected variables. Your challenge is to create a tool that can select variables measured by Earth science missions or produced by Earth science models, visualize how they change over time, and determine what is changing, where it is changing, how much it is changing, and if these changes are what scientists call "significant."

## Cele (4 elementy, pełny zakres = wizualizacja + analiza)
1. Wybór zmiennych Earth science do badania trendów (MODIS, OMI, AIRS, GPM, modele MERRA-2 i GLDAS).
2. Pobranie danych dla konkretnego regionu.
3. Szereg czasowy i jego wizualizacja, wystarczająco długie do statystyki.
4. Analiza statystyczna: tempo zmian plus test istotności (**t-test, Mann-Kendall, przedziały ufności**).

## Potencjalne kierunki (opcjonalne)
- Odbiorcy: licealiści, studenci i publiczność z podstawami nauki. Proste definicje zmiennych. Użytkownik jako „detektyw danych”.
- Krótki kwestionariusz (co / gdzie badać), który podsuwa zmienne, plus 1–2 przykłady demo.
- „SI” może podpowiadać zmienne na podstawie artykułów, badań albo typu regionu (pustynia, las deszczowy, estuarium, atmosfera nad dużym miastem).
- Dane dzienne i miesięczne są najprostsze. Trend nieistotny też jest ciekawy.
- Sezonowość komplikuje sprawę. Trendy liniowe w zupełności wystarczą na start.
- Narzędzia hydrologiczne CUAHSI.

## Zasoby — NASA
- Giovanni (menu zmiennych, szeregi czasowe, pobieranie): https://giovanni.gsfc.nasa.gov/
- Hydrology Time Series (GES DISC): https://disc.gsfc.nasa.gov/information/tools
- AppEEARS (ekstrakcja i szeregi czasowe): https://appeears.earthdatacloud.nasa.gov/
- NOAA Climate Data Online: https://www.ncei.noaa.gov/cdo-web/
- Artykuł o szeregach czasowych SeaWiFS i testach istotności: https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf

## Zasoby — partnerzy
- KNMI Climate Explorer: https://climexp.knmi.nl/
- Testy trendów (Medium): https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b
- Przewodnik po istotności statystycznej: https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance
- CSA RCM data: https://donnees-data.asc-csa.gc.ca/en/dataset/rcm
- Geo.ca: https://geo.ca/
- SWOT: https://www.asc-csa.gc.ca/eng/satellites/swot/
- CSA, monitoring ekosystemów: https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp
- SAR Python tutorial: https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial
