# Quantitative 3D terrain-shape parameters from DEMs for Earth vs Moon/Mars comparison

Researcher note on evidence quality (read first). Access during this session was poor: the Wiley/AGU full text of Rosenburg et al. 2011 returned HTTP 403, the Caltech thesis PDFs (Rosenburg 2014 Ch. 2 and Ch. 4) reset the connection twice, `tharsis.gsfc.nasa.gov` (Aharonson preprint) did not resolve, and one PDF mirror was blocked by the tool permission layer. Consequently:

- **[VERIFIED-PAGE]** = I opened the page and read it (PGDA product 70, PGDA product 90, arXiv abstracts 2603.18626, 2501.08584, 1805.11249, 2103.00291, USGS record for Shepard 2001, Caltech record for Kreslavsky 2013).
- **[SNIPPET]** = seen only in a search-engine result summary/abstract snippet; treat as UNVERIFIED until the paper is opened.
- **[RECALL - UNVERIFIED]** = stated from the researcher's background knowledge of the literature, not opened this session. These are placed in *Inferences* or *Gaps*, never in *Cited Findings*, and must be checked against the cited DOI before going into the final report.

No formula below was copied from an opened primary full text. Formulas are the standard forms as I recall them from the named papers and are all marked accordingly.

---

## 1. Slope statistics at multiple baselines (median absolute slope, median differential slope, RMS slope, interquartile curvature)

### Takeaway
The lunar standard is *along-track, point-to-point, median* statistics at fixed baselines (Rosenburg 2011: median absolute slope + Hurst; Kreslavsky 2013: interquartile range of profile curvature at 115 m-1.8 km). Median/IQR measures are preferred over RMS because slope distributions are heavy-tailed; the team's PGDA-70 maps are exactly the Rosenburg median-absolute-slope product, and a like-for-like Earth quantity must be computed as a 1-D two-point slope at the same baseline, not as a 3x3-kernel gridded slope.

### Cited Findings
- PGDA product 70 = LOLA roughness maps of two kinds: (a) median absolute (unsigned) along-track slope in degrees, point-to-point at 57 m, 225 m and 560 m baselines, median taken in overlapping 0.25-degree windows, interpolated to 16 pixels/degree, simple cylindrical, built with GMT `surface`; (b) Hurst exponent maps. Source data: LOLA lasers 1 and 2 through mission phase LRO_NO_13. Citation requested by the page: Rosenburg et al. 2011, JGR 116, E02001. [VERIFIED-PAGE] — [PGDA product 70](https://pgda.gsfc.nasa.gov/products/70)
- PGDA-70 Hurst maps: H = slope of the best-fit line to log(v(dx)) vs log(dx), v = RMS deviation; computed in 1-degree windows spaced 0.25 degree along track; baseline range 57 m to 2.7 km; "each fit runs from 57 m to a breakover point if one exists"; gridded at 8 pixels/degree. [VERIFIED-PAGE] — [PGDA product 70](https://pgda.gsfc.nasa.gov/products/70)
- Rosenburg et al. 2011 reports the Hurst exponent "high within the lunar highlands, with a median value of 0.95, and lower in the maria (with a median value of 0.76)", over baselines of about 17 m to 2.7 km. [SNIPPET] — [Rosenburg et al. 2011, doi:10.1029/2010JE003716](https://doi.org/10.1029/2010JE003716). Note the conflict in lower baseline: search snippet says ~17 m, PGDA-70 page says 57 m for the distributed maps (17 m is roughly the smallest LOLA spot-to-spot spacing within one shot pattern; 57 m is the along-track shot spacing).
- Differential slope (as used in the lunar work, following Kreslavsky & Head): the slope at scale L minus the slope at twice that scale, 2L, i.e. a detrended slope that removes regional tilt. [SNIPPET] — [Rosenburg thesis Ch. 2, Caltech](https://thesis.library.caltech.edu/8408/13/Rosenburg_Margaret_2014_Ch2.pdf)
- Kreslavsky & Head 2000 (Mars, MOLA): "the median absolute value of the differential slope at a given baseline is proposed as a data-derived measure of the surface roughness at this scale"; baselines 0.6 to ~20 km; MOLA ranging precision estimated at ~20 cm from the smoothest terrains. [SNIPPET] — [Kreslavsky & Head 2000, doi:10.1029/2000JE001259](https://doi.org/10.1029/2000JE001259)
- Kreslavsky & Head 1999 (companion, MOLA) used baselines 0.4-25 km and states that median slope complements "interquartile scale" roughness characterisation, being more sensitive to smaller-baseline slopes. [SNIPPET] — [Kreslavsky & Head 1999, JGR 104 (search summary; no DOI retrieved)](https://earthref.org/ERR/61111)
- Kreslavsky et al. 2013 (Icarus 226, 52-66): roughness measure = interquartile range of along-profile curvature at several baselines from 115 m to 1.8 km; "hectometer-scale roughness poorly correlates with kilometer-scale roughness" because they reflect different processes and ages (short scale: regolith processes and recent impacts; km scale: older impact, volcanic, tectonic events); maps reveal mare/cryptomare geologic contacts. [VERIFIED-PAGE, abstract only] — [Caltech record](https://authors.library.caltech.edu/records/h4s1k-yg166), [doi:10.1016/j.icarus.2013.04.027](https://doi.org/10.1016/j.icarus.2013.04.027)
- PGDA product 90 (LOLA south pole, Barker et al. 2023, PSJ 4, 183, doi:10.3847/PSJ/acf3e1; data doi:10.60903/gsfcpgda-lola-spole) contains *2-D, gridded* roughness layers that are much closer to what can be computed from GLO-30 than the along-track product 70: LDEM at 5-240 m/px depending on latitude cap (80-90S at 80/40/20 m/px; 83S at 10 m/px; 75S at 30 m/px; 60S at 240/120/60 m/px), LDSM slope map with error layer, LDEM_EFFRES effective-resolution map, and LDRM roughness products: ROUGH (spread of height residuals around a plane fit in a circular window), SLP (slope of that plane fit), RMSD (RMS height deviation between a central point and a surrounding annulus), all at baselines 100, 200, 400, 800, 1600 m; H (Hurst exponent, 1000 and 50 m/px); CLASS (k-means class from the roughness spectrum); AVGROUGH; SPSLP (roughness spectral slope). [VERIFIED-PAGE] — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)

### Inferences
- [RECALL - UNVERIFIED] Standard formulas, to be checked against the DOIs above before publication:
  - Point-to-point slope at baseline L: `s_L(x) = [h(x+L/2) - h(x-L/2)] / L`; median absolute slope = `median(|s_L|)` over the window, reported as `atan` in degrees.
  - Differential slope (Kreslavsky & Head 2000): `s_d(x) = s_L(x) - s_2L(x)`, both centred on x; roughness = `median(|s_d|)`. Subtracting the 2L slope removes regional tilt, so a smooth tilted plain reads as smooth.
  - Profile curvature (Kreslavsky 2013): second difference `c_L(x) = [h(x-L) - 2h(x) + h(x+L)] / L^2` (or equivalently the height of the middle point above the chord, divided by L); roughness = interquartile range of c_L. My recollection of the five baselines is 0.115, 0.23, 0.46, 0.92, 1.8 km; only the end members are confirmed.
  - RMS slope: `s_rms(L) = sqrt(<s_L^2>)`; RMS deviation / Allan deviation: `v(L) = sqrt(<[h(x) - h(x+L)]^2>)`, so `s_rms = v/L`.
- Why median/IQR and not RMS: lunar and Martian slope distributions are non-Gaussian with long tails (crater walls), so RMS is dominated by a few steep facets and by ranging outliers; this is the stated motivation in the Kreslavsky papers [RECALL - UNVERIFIED] and is consistent with the Aharonson 2001 finding of long-tailed slope distributions (section 6).
- Like-for-like trap for the team: PGDA-70 is a *1-D two-point* slope along roughly N-S LRO tracks. A GLO-30 slope from Horn/Zevenbergen 3x3 kernels is a 2-D gradient magnitude at an effective baseline of ~60 m and is systematically larger than the 1-D absolute slope along one direction (for an isotropic surface the 1-D component is smaller than the full gradient by a factor of order 0.6-0.7; this factor is a geometric expectation, not a sourced number). To match, compute on GLO-30 `|h(i+k) - h(i-k)|/(2k*30 m)` along columns for 2k*30 m = 60, 240, 540 m, then take the median in the cell.
- Better option: compare GLO-30 against the *gridded* south-pole products of PGDA-90 (30 m/px LDEM to 75S exists; RMSD/ROUGH/SLP at 100-1600 m baselines), using the identical algorithm on both DEMs rather than mixing a published lunar map with a home-made Earth one.
- The poor correlation between hectometre- and kilometre-scale roughness on the Moon (Kreslavsky 2013) is itself a usable discriminator: a multi-baseline *roughness spectrum* (vector of roughness at 100/200/400/800/1600 m) carries more information than slope at one baseline, which fits the team's observation that slope-only similarity is not specific.

### Gaps
- Numerical median slopes for highlands / maria / south polar region at 57, 225, 560 m were NOT retrieved (paper paywalled/403). The team can read these directly off the PGDA-70 maps they already have loaded; I recall highland median slopes of several degrees and mare values of ~1-2 degrees at the shortest baselines, but this is [RECALL - UNVERIFIED].
- Exact baseline list and curvature normalisation in Kreslavsky 2013 not verified.
- No verified Earth values of median differential slope at the same baselines were found.

---

## 2. Structure function / deviogram / Allan deviation and the Hurst exponent

### Takeaway
The deviogram (log RMS deviation vs log baseline) is the planetary-science standard, standardised by Shepard et al. 2001; lunar highlands are near self-affine with H ~0.95 below ~1 km and a break at ~1 km, maria H ~0.76. H is a poor similarity feature at 30 m posting because the fit has few octaves, sits across the lunar breakover, and is biased by DEM smoothing and noise.

### Cited Findings
- Shepard et al. 2001 (JGR Planets 106, E12, 32777-32795, doi:10.1029/2000JE001429) reviews roughness parameters, argues that "scale-dependent roughness parameters are almost always required", proposes a standard parameter set so that data from different groups/techniques can be compared, and demonstrates it on topographic data from 60 surfaces collected by five groups; discusses implications for planetary roughness, lander safety and radar. [VERIFIED-PAGE, abstract only] — [USGS publication record](https://www.usgs.gov/publications/roughness-natural-terrain-a-planetary-and-remote-sensing-perspective)
- RMS deviation is the RMS height difference between points separated by a given distance and is commonly well described by a power law, `v(L) = v0 * L^H`, H in [0,1], v0 = RMS deviation at unit scale; RMS deviation is directly related to RMS slope (Shepard 2001 gives the relation); the RMS deviation estimate is unstable at small sample numbers. [SNIPPET, from an Itokawa roughness paper citing Shepard] — [arXiv:1905.04882](https://arxiv.org/pdf/1905.04882)
- Moon, LOLA along-track (Rosenburg 2011): median H = 0.95 in highlands, 0.76 in maria. [SNIPPET] — [doi:10.1029/2010JE003716](https://doi.org/10.1029/2010JE003716)
- Rosenburg thesis: highland topography "behaves as a nearly self-similar fractal system on scales of order 100 meters, and there is a distinct change in this behavior above and below approximately 1 km". [SNIPPET] — [Rosenburg 2014 thesis, Caltech](https://thesis.library.caltech.edu/8408/)
- PGDA-70 handles the break explicitly: the fit runs from 57 m only up to the breakover point when one exists, "which avoids nonlinear parts of the deviogram"; the largest-baseline (window-scale) trend is removed to avoid window-size bias. [VERIFIED-PAGE] — [PGDA product 70](https://pgda.gsfc.nasa.gov/products/70)
- Moon, metre scale (Cai & Fa 2020, JGR Planets, LROC NAC DTMs over 462 regions): H from 0.7 to 0.95, median 0.9 in both maria and highlands; mare H "much larger than those of the volcanic features on Earth and Mars", attributed to accumulation of craters smaller than 1 km; highland values match simulated cratered terrain. [SNIPPET] — [doi:10.1029/2020JE006429](https://doi.org/10.1029/2020JE006429)
- The two lunar mare values conflict (0.76 at 17/57 m-2.7 km along-track LOLA vs ~0.9 from metre-scale NAC DTMs): different data, baselines and fitting ranges; they are not interchangeable. [SNIPPET] — [Rosenburg 2011](https://doi.org/10.1029/2010JE003716); [Cai & Fa 2020](https://doi.org/10.1029/2020JE006429)
- Mars (Orosei et al. 2003, MOLA): H greater than 0.5 over most of the surface, i.e. scaling behaviour "almost self-similar". [SNIPPET] — [Orosei et al. 2003, record at Smithsonian repository](https://repository.si.edu/handle/10088/6338) (link surfaced by search; exact record not opened)
- PGDA-90 provides gridded south-pole Hurst-exponent layers (LDRM H at 1000 and 50 m/px) derived from RMSD at 100-1600 m baselines (50 m from the LOLA single-shot roughness product). [VERIFIED-PAGE] — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)

### Inferences
- [RECALL - UNVERIFIED] Standard relations (Shepard 2001; Turcotte's fractal texts): RMS slope scales as `s_rms(L) = s0 * L^(H-1)`; H = 1 is self-similar (slope independent of scale), H = 0.5 is Brownian; fractal dimension of a profile `D = 2 - H`, of a surface `D = 3 - H`. Shepard's table of terrestrial field surfaces (lava flows such as pahoehoe/a'a, playas, alluvial fans) gives H mostly around 0.3-0.7 at centimetre-to-decametre scales, i.e. distinctly lower than the lunar highland 0.95. This contrast is consistent with the Cai & Fa snippet above but the specific terrestrial numbers must be taken from Shepard's Table before use.
- Why H from GLO-30 is unstable (reasoned, consistent with the sources above):
  1. Too few octaves: with 30 m posting and a cell of a few km, usable lags are ~60 m to ~1 km, i.e. about 4 octaves, and the lunar deviogram itself breaks at ~1 km, so the fit range that is physically meaningful on the Moon is almost entirely at or below GLO-30's true resolution.
  2. Resolution vs posting: a radar DEM's effective resolution is coarser than its 30 m posting; smoothing suppresses short-lag variance and biases H upward (toward 1). LOLA DEMs have the same problem between tracks, which is why PGDA-90 ships an LDEM_EFFRES layer.
  3. Noise: uncorrelated height noise adds a lag-independent term to v(L)^2, flattening the deviogram at short lags and biasing H downward. Smoothing and noise act in opposite directions, so the net bias is site dependent.
  4. Detrending/window: without removing the window-scale trend the longest lags are biased (PGDA-70 removes it); with too aggressive detrending the long lags are suppressed.
  5. Non-topographic signal: GLO-30 is a surface model (vegetation, buildings), adding short-scale roughness with no lunar counterpart.
  6. Small-sample instability of the RMS deviation estimator (noted in the Itokawa paper).
- Practical consequence: use H only as a weak, coarse feature (or drop it) and prefer the deviogram *values* v(L) at 3-5 fixed lags, or the PGDA-90 style RMSD at 100/200/400/800/1600 m, compared directly. Values at fixed baselines are robust; the fitted exponent is not.

### Gaps
- Shepard 2001 full text not opened: whether it uses the term "Allan deviation" (the search summary could not confirm) and the per-surface H table are unverified. I recall that Shepard explicitly equates RMS deviation with the Allan deviation / square root of the structure function, [RECALL - UNVERIFIED].
- Exact lunar breakover scale distribution and south-polar H values not retrieved; available directly from the PGDA-70 Hurst maps and PGDA-90 LDRM H layers.
- No verified H values for Earth computed at lunar-comparable baselines (60 m-2.7 km) from a global DEM were found.

---

## 3. Power spectral density of topography (beta, relation to H and D, anisotropy)

### Takeaway
On cratered terrain the PSD slope is controlled by the crater size-frequency distribution and crater shape (Rosenburg, Aharonson & Sari 2015), not by a generic "fractal" process, and lunar spectra show a scale separation between sub-km and km scales. For Mars, Aharonson et al. 2001 tied spectral differences between lowlands and highlands to sedimentation vs cratering. PSD slope has the same fit-range fragility as H; 2-D spectral anisotropy is the more useful, less-used product.

### Cited Findings
- Rosenburg, Aharonson & Sari 2015 (JGR Planets 120, 177-194, doi:10.1002/2014JE004746): cratering produces characteristic PSD variations "controlled by the size-frequency distribution of craters and the spectral content (shape) of individual features"; Monte Carlo cratered-terrain model benchmarked by an analytic 1-D PSD. [SNIPPET, abstract] — [Caltech record](https://resolver.caltech.edu/CaltechAUTHORS:20150420-150449404)
- Same paper: for self-similar craters the PSD slope beta varies inversely with the production-function exponent alpha, "leveling off to 0 at high alpha (surface topography dominated by the smallest craters) and maintaining a roughly constant value (beta ~ 2) at low alpha (surface topography dominated by the largest craters)". [SNIPPET, abstract] — [doi:10.1002/2014JE004746](https://doi.org/10.1002/2014JE004746)
- Same paper: at small scales (~115 m to 1 km) model predictions agree with PSD slopes measured on LOLA transects over the observed range of lunar size-frequency distributions; differences between global PSD slopes at sub-km and km scales "reflect a scale separation in roughness". [SNIPPET, abstract] — [doi:10.1002/2014JE004746](https://doi.org/10.1002/2014JE004746)
- Aharonson, Zuber & Rothman 2001 (JGR 106, MOLA): a sedimentation-like model accounts for the shallower long-wavelength lowland spectrum, "while the addition of another process such as cratering is necessary to explain the spectral slope in short wavelengths"; northern plains slopes typically below 0.5 degree. [SNIPPET, abstract] — [Caltech record](https://resolver.caltech.edu/CaltechAUTHORS:AHAjgre01)
- Landais, Schmidt & Lovejoy 2018/2019 (arXiv:1805.11249; Icarus, doi:10.1016/j.icarus.2018.07.005), "Multifractal topography of several planetary bodies in the Solar System": global topography of Earth, Mars, Mercury and Moon analysed with multifractal methods (heights, slopes, higher moments); data agree with multifractal theory at scales larger than ~10 km; all four bodies show the same fractal behaviour at scales smaller than ~10 km; proposed (as hypotheses) links to mantle dynamic topography at large scale and elastic thickness at small scale. A search summary says Earth data were ETOPO1 and the others PDS products. [VERIFIED-PAGE, abstract only; numeric exponents not on the page] — [arXiv:1805.11249](https://arxiv.org/abs/1805.11249)

### Inferences
- [RECALL - UNVERIFIED] Standard relations for a self-affine surface: 1-D profile PSD `S(k) ~ k^-beta` with `beta = 2H + 1` (so H = (beta-1)/2, D_profile = (5-beta)/2); radially averaged 2-D PSD `beta_2D = 2H + 2`. Mixing 1-D and 2-D conventions is the most common error when comparing published betas. beta ~ 2 (Brownian, H = 0.5) is the classic terrestrial value at km scales.
- The Rosenburg 2015 result means lunar beta is a *proxy for local crater population and degradation state*, not a universal constant; an Earth cell with matching beta is not thereby crater-like. PSD slope cannot distinguish a crater field from a random self-affine surface because it discards phase.
- Landais et al. is the one verified cross-body study that puts Earth and Moon in the same framework, but it is global, at >=km resolution (ETOPO1 is 1 arc-minute), and its "same behaviour below 10 km" conclusion argues *against* expecting scaling exponents to discriminate bodies. This supports the team's finding that H is uninformative.
- Anisotropy: no planetary paper quantifying 2-D spectral anisotropy for Earth-Moon comparison was found. As an engineering suggestion (not sourced): ratio of directional variograms/structure functions at fixed lag, or the eccentricity of the 2-D PSD/autocorrelation ellipse, or the eigenvalue ratio of the surface-normal orientation tensor. Fluvially dissected and tectonic terrain is anisotropic at the cell scale; crater-saturated terrain is near-isotropic. LOLA along-track products cannot provide this (single direction); gridded PGDA-90 DEMs can.
- Pitfalls: windowing/tapering and detrending change beta; interpolation between LOLA tracks removes cross-track power at short wavelengths (polar convergence of tracks makes the south pole the best-sampled area); GLO-30 has a noise floor and resolution roll-off below roughly 2-3 pixels.

### Gaps
- Numerical lunar beta values (highlands/maria, sub-km vs km) not retrieved (thesis Ch. 4 PDF failed to load).
- Aharonson 2001 spectral exponents and its quantitative Earth/Venus comparison data sets not retrieved (preprint host unreachable).
- No published like-for-like PSD comparison between a ~30 m Earth DEM and a lunar DEM was found.

---

## 4. Landform classification metrics (geomorphons, curvature, TPI, TRI, VRM)

### Takeaway
Geomorphons, TPI, TRI and VRM come from terrestrial geomorphometry/ecology and have essentially no standing as lunar roughness standards; lunar/Martian DEM classification work exists but mostly uses clustering of slope/relief/curvature attributes. They are easy to compute identically on both DEMs, so their value to the team is as *self-computed* like-for-like features, not as literature-anchored ones.

### Cited Findings
- Geomorphons: Jasiewicz & Stepinski 2013, Geomorphology (doi:10.1016/j.geomorph.2012.11.005), pattern-recognition landform classification; the GRASS `r.geomorphon` implementation returns one of 498 unique ternary patterns per cell (commonly reduced to 10 landform classes). [SNIPPET] — [doi:10.1016/j.geomorph.2012.11.005](https://doi.org/10.1016/j.geomorph.2012.11.005); [r.geomorphon manual](https://manpages.ubuntu.com/manpages/bionic/en/man1/r.geomorphon.1grass.html)
- A targeted search found no study applying geomorphons specifically to a lunar DEM. [search result, negative] — search performed 2026-11-14; closest hits below.
- Wang et al. 2017, Journal of Geographical Sciences, "Automatic mapping of lunar landforms using DEM-derived geomorphometric parameters": ISO-cluster unsupervised classification of DEM-derived parameters, tested on three lunar sites. [SNIPPET] — [doi:10.1007/s11442-017-1443-z](https://link.springer.com/article/10.1007/s11442-017-1443-z)
- Deng et al. 2022, Journal of Geographical Sciences: lunar relief-amplitude classification from LOLA DEM and SLDEM2015, with the optimal moving-window size chosen by the mean change-point method. [SNIPPET] — [doi:10.1007/s11442-022-2052-z](https://doi.org/10.1007/s11442-022-2052-z)
- EGU 2018 abstract "Distribution of landforms at the Lunar North Pole": landform analysis of a 60.6 km circular region around the pole from DEMs at 25-100 m grid spacing. [SNIPPET] — [ADS 2018EGUGA..2010420M](https://ui.adsabs.harvard.edu/abs/2018EGUGA..2010420M)
- Mars: Bue & Stepinski 2006 "terrain fingerprinting" classification of global MOLA DEM, later applied by Koenders et al. 2009 to MOLA, HRSC and OMEGA-MOLA data; Stepinski et al. 2006 segment-then-classify with a 12-dimensional terrain-attribute vector per object, best accuracy ~84.6% with SVM at Tisia Valles. [SNIPPET] — [Koenders et al. 2009, geomorphometry.org](https://geomorphometry.org/uploads/pdf/pdf2009/koenders2009geomorphometry.pdf); [Stepinski et al. 2006](https://link.springer.com/doi/10.1007/11893318_26)
- Review: Liu & Cheng 2023, "Progress and prospects for research on Martian topographic features and typical landform identification", Frontiers in Astronomy and Space Sciences. [SNIPPET] — [doi:10.3389/fspas.2023.1275516](https://www.frontiersin.org/articles/10.3389/fspas.2023.1275516/full)
- Limitation noted for Mars: DEM-derived topography captures slope, roughness and undulation, but coarse DEMs cannot separate fine-scale landform types, motivating imagery (CTX) fusion. [SNIPPET] — [MarsMapNet paper](https://iris.unitn.it/retrieve/ab19bab4-ec60-4757-9d7d-7fad6effd2b8/TGRS3616965.pdf)

### Inferences
- [RECALL - UNVERIFIED] Definitions: TRI (Riley et al. 1999) = root of summed squared elevation differences between a cell and its 8 neighbours; TPI (Weiss 2001) = cell elevation minus mean elevation in an annulus/neighbourhood of radius R; VRM (Sappington et al. 2007) = 1 - |sum of unit normal vectors|/n in a window, designed to be decorrelated from slope; profile/plan curvature from the second derivatives of a fitted quadratic (Zevenbergen & Thorne 1987). Original papers were not opened; cite them only after checking.
- TRI at one pixel scale is essentially a rescaled local slope and adds little to slope-only similarity. VRM and TPI-at-several-radii add independent information (VRM is slope-decorrelated by design; multi-radius TPI is a band-pass relief measure closely related to PGDA-90 RMSD "central point vs surrounding annulus").
- PGDA-90 RMSD (central point vs annulus at 100-1600 m) is conceptually a multi-scale |TPI|; computing mean/median |TPI| at radii 100/200/400/800/1600 m on GLO-30 gives the nearest like-for-like match to an official lunar product.
- Geomorphon class *fractions* per cell (percent pit, hollow, valley, ridge, peak, spur, slope, flat...) are a promising shape descriptor for the team's specific problem: impact terrain should be rich in closed "pit/depression" forms and poor in connected "valley" forms, while fluvial terrain is the reverse. This is untested in the literature found; the lookup distance must be set identically in metres on both DEMs.
- All of these are resolution dependent; they must be computed after resampling both DEMs to a common posting and effective resolution.

### Gaps
- No verified application of TPI, TRI, VRM or geomorphons to LOLA/SLDEM lunar DEMs or MOLA/HRSC Martian DEMs was found; absence in a quick search is not proof of absence.
- No published Earth vs Moon comparison using any of these indices was found.

---

## 5. Closed depressions and craters: SFD and morphometry (Moon vs terrestrial simple craters)

### Takeaway
Fresh lunar simple craters of km size have depth/diameter ~0.2 (Pike), dropping to 0.11-0.17 below ~400 m (Stopar et al. 2017); Meteor Crater's present apparent d/D is ~0.14, i.e. shallower than a fresh lunar crater of the same 1.2 km diameter (which would be ~240 m deep) because of erosion and infill, though its "true" depth to the breccia-lens base (~300 m, d/D ~0.25) is lunar-like. A single 1.2 km crater spans ~40 GLO-30 pixels, so it can be measured, but the surrounding terrain is not crater-saturated.

### Cited Findings
- Stopar et al. 2017 (Icarus 298, 34-48), "Relative depths of simple craters and the nature of the lunar regolith": >930 simple craters, 40 m to 10 km, from LROC NAC and Kaguya TC DTMs; d/D = 0.11-0.17 for an extremely fresh set under 400 m diameter; larger craters typically near 0.21, "as expected of gravity-dominated crater excavation". [SNIPPET, abstract] — [University of Arizona record](https://experts.arizona.edu/en/publications/relative-depths-of-simple-craters-and-the-nature-of-the-lunar-reg-2/)
- LROC public summary of the same paper: d/D about 0.2 above 400 m, ~0.17 for 200-400 m, ~0.15 for 100-200 m, ~0.12 for 30-100 m; no deep-and-steep craters found below 200 m diameter. [SNIPPET] — [LROC featured image 975](https://lroc.im-ldi.com/images/975)
- A citing paper quotes the Stopar bins by radius instead (0.13 for 20-50 m radius, 0.15 for 50-100 m, 0.17 for 100-200 m); bins differ by convention, check before use. [SNIPPET] — [arXiv:1802.03664](https://arxiv.org/pdf/1802.03664)
- Pike: simple-crater rim height h ~ 0.036 D (rim heights 3-4% of diameter); simple lunar craters (below ~15 km) have depth/diameter about 0.2; Pike's ratio distribution inflects sharply at ~15 km apparent diameter. [SNIPPET] — [Pike 1977, in Impact and Explosion Cratering, pp. 489-509, ADS](https://ui.adsabs.harvard.edu/abs/1977iecp.symp..489P/abstract); [NTRS record](https://ntrs.nasa.gov/citations/19780057837)
- Simple-to-complex transition on the Moon: ~14-15 km on maria, ~16-18 km on highlands (Feoktistova & Ipatov 2021, Earth Moon Planets 125, LOLA profiles of Copernican craters 10-100 km: mare craters with D<15 km simple, 15-18 km ambiguous; highland craters with D<18 km mostly simple; mare craters with D<14 km have depths greater than 0.15 D). [VERIFIED-PAGE, abstract] — [arXiv:2103.00291](https://arxiv.org/abs/2103.00291)
- Meteor (Barringer) Crater, Arizona: about 1,200 m (3,900 ft) in diameter, about 170 m (560 ft) deep, rim rising about 45 m (148 ft) above the surrounding plain. [SNIPPET, tertiary source: Wikipedia mirror] — [Meteor Crater (Wikipedia mirror)](https://ipfs.ssi.eecc.de/ipns/en.wikipedia-on-ipfs.org/wiki/Meteor_Crater). NASA describes it as about one mile wide and up to 570 feet (~174 m) deep. [SNIPPET] — [science.nasa.gov](https://science.nasa.gov/?p=1241303)
- Meteor Crater "true" depth to the base of the breccia lens is approximately 300 m (attributed to Melosh & Ivanov 1999). [SNIPPET, secondary] — [craterexplorer.ca crater classification](https://craterexplorer.ca/crater-classification/)
- Simple craters generally: depth-to-diameter about 1:5 to 1:7, smooth bowl shape. [SNIPPET, secondary] — [craterexplorer.ca](https://craterexplorer.ca/crater-classification/)
- Popular-press Earth-Moon comparison: lunar crater Linne (2.2 km diameter, ~550 m deep, d/D ~0.25) is about twice the diameter of Barringer but almost three times as deep. [SNIPPET, non-primary] — [Space.com](https://www.space.com/7146-comparing-craters-earth-moon.html); [Astronomy.com](https://www.astronomy.com/science/how-deep-are-the-craters-on-the-moon/)
- Authoritative reference for Meteor Crater morphometry (not opened): Kring, D. A. (2017), Guidebook to the Geology of Barringer Meteorite Crater, Arizona, LPI Contribution No. 2040 (earlier edition 2007, LPI Contribution No. 1355), free download from LPI. [SNIPPET, bibliographic only] — [barringercrater.com guidebook page](https://barringercrater.com/blog/geological-guide-book-to-meteor-crater)

### Inferences
- Arithmetic from the figures above: Meteor Crater apparent d/D = 170/1200 = 0.14 (0.145 with 174/1200). A fresh lunar simple crater at D = 1.2 km with d/D ~0.2 would be ~240 m deep with a rim ~43 m high (0.036 D). So Meteor Crater's rim height (45 m) matches the lunar scaling very well while its floor is ~70 m too shallow. Its d/D coincides with *fresh lunar craters of 100-400 m diameter* or with *moderately degraded* km-scale lunar craters, which is arguably the more common state in the south polar highlands.
- [RECALL - UNVERIFIED] The shallowness is attributed to ~50 kyr of erosion plus tens of metres of Pleistocene lake sediments and alluvium on the floor, and rim lowering of order 10-20 m; the crater outline is "squarish" because of two orthogonal joint sets in the Colorado Plateau target; upper-wall slopes are steep (roughly 40+ degrees in cliff-forming Kaibab, gentler below). Fresh lunar simple craters have wall slopes near the angle of repose (~30-35 degrees). All of this is in Kring's guidebook and must be cited from it.
- [RECALL - UNVERIFIED] Pike's 1977 fits for fresh lunar simple craters (D < ~15 km): depth `d = 0.196 D^1.010`, rim height `h = 0.036 D^1.014` (km). The search confirmed the 0.036 D rim-height coefficient and the ~0.2 ratio but NOT the 0.196/1.010 depth fit; verify in Pike (1977).
- [RECALL - UNVERIFIED] Other terrestrial simple craters: Lonar (India) ~1.8-1.9 km diameter, ~135-150 m deep to the lake, in Deccan basalt (the best target-rock analog for mare basalt); Tswaing (South Africa) ~1.1 km diameter, ~100-120 m deep, heavily infilled. Both have apparent d/D of roughly 0.07-0.1, i.e. much shallower than lunar fresh values. No source was opened for these numbers; take them from the Earth Impact Database (https://www.passc.net/EarthImpactDatabase/) before use.
- Gravity does matter for the *transition* diameter (simple-to-complex ~15-18 km on the Moon vs a few km on Earth, [RECALL] ~2-4 km depending on target), so only terrestrial craters below ~2-4 km are shape-comparable to lunar simple craters; larger terrestrial craters are complex and flat-floored where lunar ones of the same size are still bowls.
- For a cell-based similarity index the more relevant crater metrics are *population* metrics: closed-depression density (count of sinks above a size threshold per km2, from priority-flood depression filling), fraction of cell area inside closed depressions, depression circularity, and depth/diameter of detected depressions. On Earth the same detector fires on karst sinkholes, volcanic craters/maars, kettles, deflation basins and playas; these (with volcanic crater fields and karst cones) are the only terrestrial terrains that mimic the *topology* of cratered terrain.
- Crater size-frequency distributions: at 30 m posting only craters above ~200-300 m (7-10 pixels) are resolvable; the lunar highlands are saturated in craters at these sizes whereas Earth has ~200 confirmed impact structures in total, so a CSFD match is impossible in principle and the comparison has to be made on generic closed-depression statistics.

### Gaps
- Kring guidebook and Earth Impact Database entries were not opened: Meteor Crater rim-crest diameter, rim uplift and wall slope, and Lonar/Tswaing dimensions remain unverified.
- Pike 1977 primary text not opened.
- No published study was found that quantitatively overlays a Meteor Crater DEM profile on a lunar simple-crater profile of the same size; the comparison above is arithmetic on separately sourced numbers.
- Lunar south-pole-specific d/D statistics: an MDPI Remote Sensing paper, "Depth to Diameter Analysis on Small Simple Craters at the Lunar South Pole - Possible Implications for Ice Harboring" (https://www2.mdpi.com/2072-4292/14/3/450), surfaced in search but was not opened.

---

## 6. Hypsometry, relief and slope histograms for inter-planetary comparison

### Takeaway
Inter-planetary slope/hypsometry comparison does exist (Aharonson et al. 2001; Kreslavsky & Head 1999; Landais et al. 2018) but only at global scale and km baselines; the robust result is that the *shape (tail) of the slope distribution* differs between bodies, which argues for comparing whole slope histograms rather than a single statistic.

### Cited Findings
- Aharonson, Zuber & Rothman 2001: Mars' slope distribution is "longer tailed than those of Earth and Venus, indicating a lower efficiency of planation processes relative to relief-building tectonics and volcanics". [SNIPPET, abstract] — [Caltech record](https://resolver.caltech.edu/CaltechAUTHORS:AHAjgre01)
- Same paper: Mars' bimodal hypsometry becomes unimodal when referenced to the centre of figure, whereas Earth's bimodality is retained. [SNIPPET, abstract] — [Caltech record](https://authors.library.caltech.edu/13034)
- Kreslavsky & Head 1999 (MOLA, baselines 0.4-25 km) used median slope alongside interquartile-scale roughness. [SNIPPET] — [EarthRef record](https://earthref.org/ERR/61111)
- Landais et al.: Earth, Mars, Mercury and Moon share the same scaling behaviour below ~10 km in global data. [VERIFIED-PAGE, abstract] — [arXiv:1805.11249](https://arxiv.org/abs/1805.11249)
- Lunar relief amplitude classification with an objectively chosen window (mean change-point method) exists for LOLA/SLDEM2015 (Deng et al. 2022). [SNIPPET] — [doi:10.1007/s11442-022-2052-z](https://doi.org/10.1007/s11442-022-2052-z)

### Inferences
- Local hypsometric integral/curve within a cell is cheap and scale-free (normalised), and distinguishes plateau-with-incised-valleys (high integral, convex curve) from plain-with-raised-rims or peaks (low integral); however a crater-pocked plain and a dissected plateau are near mirror images, so the sign of elevation skewness matters. It is not a published lunar standard.
- Local relief (max-min or 5-95 percentile range in a fixed window) is gravity-sensitive in principle: lower lunar gravity and absent fluvial erosion permit steeper long-lived relief, but polar highland relief of several km over tens of km is matched on Earth only in high mountain belts, which are fluvially/glacially dissected.
- Comparing full slope histograms (section 7 distances) honours the Aharonson finding that tails carry the process signal.

### Gaps
- The Sharpton & Head Earth/Venus slope comparison named in the brief was not searched or retrieved; I recall it as Sharpton & Head 1985/1986 (JGR) on Venus vs Earth regional slopes, [RECALL - UNVERIFIED], no DOI checked.
- Whether Kreslavsky & Head 1999 contains an explicit Mars vs Earth-continents comparison was not confirmed.
- No hypsometry-based Earth-Moon comparison at local (cell) scale was found.

---

## 7. Direct DEM patch similarity and learned embeddings; distances between distributions

### Takeaway
Published "analog recognition" by learning exists but not for the Moon and not clearly DEM-based: GEAR (2026) matches trench morphology to plateau valleys with a hand-built filter pipeline plus a Siamese graph network; Meng et al. (2025) use a CNN on imagery for Mars analogs in the Qaidam Basin. No validated DEM-embedding method for Earth-Moon terrain similarity was found, so a transparent feature-vector + distribution-distance approach is the defensible choice for a hackathon.

### Cited Findings
- GEAR (Liu, Li, Zhou, Li, Yang, Wang, Zhao, Gao; arXiv:2603.18626, cs.CV, 19 March 2026): "Geography-knowledge Enhanced Analog Recognition Framework in Extreme Environments"; three-stage pipeline to find terrestrial analogs of the Mariana Trench on the Qinghai-Tibet Plateau (~2.5 million km2 search): (1) skeleton-guided screening/clipping of candidate valleys by size and linear morphology; (2) physics-aware filtering with a Topographic Waveform Comparator and a Morphological Texture Module; (3) a Morphology-integrated Siamese Graph Network (MSG-Net) using geomorphological metrics. Reported gain: F1 1.38 percentage points above the best baseline. Releases an expert-annotated topographic similarity dataset. No planetary application. The abstract does not state whether inputs are DEMs or imagery. [VERIFIED-PAGE, abstract only] — [arXiv:2603.18626](https://arxiv.org/abs/2603.18626)
- Meng et al. (arXiv:2501.08584), "Deep learning selection of analogues for Mars landing sites in the Qaidam Basin, Qinghai-Tibet Plateau": CNN trained with a discriminative (metric-learning) loss on Earth and Mars *surface imagery* so that same-location images are close and different-location images far; used to prioritise analog sites in the Qaidam evaporite region; the abstract reports no quantitative accuracy and does not use DEMs; Moon not addressed. [VERIFIED-PAGE, abstract only] — [arXiv:2501.08584](https://arxiv.org/abs/2501.08584)
- NASA's own south-pole product classifies terrain by k-means on the multi-baseline roughness spectrum (LDRM CLASS) and summarises it with average standardised roughness and roughness spectral slope, i.e. an unsupervised feature-space approach on roughness-at-several-baselines is already the agency practice for this exact region. [VERIFIED-PAGE] — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- A 2026 ML benchmark for lunar science ("SomBench: Benchmark Dataset for Advancing Machine Learning in Lunar Science", arXiv:2609.13277) surfaced in search; not opened, relevance unknown. [SNIPPET, title only] — [arXiv:2609.13277](https://arxiv.org/pdf/2609.13277)

### Inferences
- No source was found that evaluates Wasserstein/EMD, Kolmogorov-Smirnov or Mahalanobis distances specifically for terrain analog matching, so the following is methodological reasoning, not literature:
  - 1-D Wasserstein-1 between slope (or roughness, curvature, TPI) distributions has units of the variable (degrees), is sensitive to tail differences, and is stable for small samples; KS measures only the maximum CDF gap and is insensitive to tails, which is where the process signal lies (Aharonson 2001). Prefer Wasserstein, computed per baseline.
  - Mahalanobis distance in feature space needs a covariance estimated on the *lunar reference population* (so "distance" means "how many lunar sigmas away from typical south-pole terrain"); features must first be made roughly Gaussian (log of slopes/roughness) and collinear ones removed (slope at 57/225/560 m are highly correlated; use the first as level and ratios between baselines as shape).
  - Standardising each feature by lunar-reference mean and sigma mirrors PGDA-90 AVGROUGH ("average standardized roughness (sigma)").
- Self-supervised DEM embeddings need a training corpus and a validation set of known analogs; with neither, embeddings are not verifiable in a hackathon. If attempted, the domain gap (radar DSM with vegetation vs laser-altimetry DEM with track-interpolation artefacts) is likely to dominate the embedding unless both DEMs are degraded to a common effective resolution and noise level.
- A cheap sanity test of any similarity index: score known field analog sites (e.g. Meteor Crater, volcanic crater fields, anorthosite/impact sites used by agencies) against random land cells; the index should rank them above typical fluvial terrain.

### Gaps
- GEAR full text not read: input data type, the precise definition of the waveform comparator, and whether code/data are public are unknown.
- No peer-reviewed DEM-only similarity search or contrastive terrain-embedding study targeting the Moon was found in this session; I did not run a dedicated search for general terrain foundation models, so this is a weak negative.

---

## 8. Which metrics are invariant to gravity/process differences, and which discriminate impact-dominated from fluvially dissected terrain

### Takeaway
No source found addresses this question directly; the literature only implies it: scaling exponents look alike across bodies (Landais et al.), while crater populations set lunar spectra (Rosenburg et al. 2015) and slope-distribution tails record planation efficiency (Aharonson et al. 2001). The discriminating information is therefore topological and directional (closed depressions vs connected drainage, isotropy vs anisotropy), not amplitude-based.

### Cited Findings
- Scaling behaviour below ~10 km is the same for Earth, Mars, Mercury and Moon in global topography. [VERIFIED-PAGE, abstract] — [arXiv:1805.11249](https://arxiv.org/abs/1805.11249)
- On the Moon, PSD slope is set by the crater production-function exponent and crater shape. [SNIPPET] — [doi:10.1002/2014JE004746](https://doi.org/10.1002/2014JE004746)
- Lunar H at metre scale is higher than on terrestrial and Martian volcanic surfaces because of sub-km crater accumulation. [SNIPPET] — [doi:10.1029/2020JE006429](https://doi.org/10.1029/2020JE006429)
- Slope-distribution tail length differs between Mars and Earth/Venus and is interpreted as planation efficiency vs relief building. [SNIPPET] — [Aharonson et al. 2001](https://resolver.caltech.edu/CaltechAUTHORS:AHAjgre01)
- Lunar hectometre- and kilometre-scale roughness are poorly correlated and record different processes/ages. [VERIFIED-PAGE, abstract] — [doi:10.1016/j.icarus.2013.04.027](https://doi.org/10.1016/j.icarus.2013.04.027)

### Inferences
Proposed ranking for the team (reasoned from the above; none of it is a published validation):

| Metric | Like-for-like computable on GLO-30 and LOLA DEM? | Robust at 30 m? | Discriminates impact vs fluvial? | Lunar literature anchor |
|---|---|---|---|---|
| Median absolute slope at 57/225/560 m | Yes, if computed as 1-D two-point slope | Yes | Weak (amplitude only) | Rosenburg 2011; PGDA-70 |
| Median differential slope / IQR curvature at 115 m-1.8 km | Yes | Yes for >= ~240 m baselines; marginal at 115 m | Moderate (detrended; multi-scale ratio is informative) | Kreslavsky & Head 2000; Kreslavsky 2013 |
| RMSD / plane-fit roughness at 100-1600 m (roughness spectrum) | Yes, directly against PGDA-90 grids | Yes for >= 200 m | Moderate | Barker 2023; PGDA-90 |
| Hurst exponent / PSD slope | Formally yes | No (few octaves, breakover at ~1 km, smoothing/noise bias) | Weak (bodies look alike) | Shepard 2001; Rosenburg 2011, 2015 |
| Slope histogram distance (Wasserstein) | Yes | Yes | Moderate (tails) | Aharonson 2001 (concept) |
| Closed-depression density / area fraction / depression d/D | Yes (priority-flood on both DEMs) | Yes for depressions >= ~250 m | Strong | Pike 1977; Stopar 2017 (single-crater shape) |
| Drainage density / fraction of cell draining externally / stream-network connectivity | Yes | Yes | Strong (fluvial terrain is integrated; cratered terrain is internally drained) | none found |
| Anisotropy (directional variogram ratio, normal-vector orientation tensor) | Yes on gridded DEMs only | Yes | Strong (valleys/ridges anisotropic; crater fields isotropic) | none found |
| Geomorphon class fractions (pit vs valley share) | Yes | Moderate | Potentially strong, untested | none found for Moon |
| Elevation skewness / local hypsometric integral | Yes | Yes | Moderate | none found for Moon |

- Gravity/process dependence, qualitatively: (i) crater d/D for simple craters is approximately gravity-independent (~0.2 on any rocky body when fresh), but the simple-to-complex transition scales inversely with gravity, so only sub-few-km terrestrial craters compare; (ii) maximum stable slope is set by the angle of repose (material property, ~30-35 degrees, not gravity), so the upper end of the slope distribution is comparable, whereas the *bulk* of the terrestrial slope distribution is set by fluvial/hillslope transport that has no lunar equivalent; (iii) lunar topography is diffusively smoothed by micrometeorite gardening at short scales, giving rounded, convex-concave forms without channel incision, so curvature sign statistics and channel-ness (positive plan curvature along connected thalwegs) differ; (iv) amplitude metrics alone (slope, relief, TRI) will always match some steep fluvial terrain, which is the non-specificity the team observed.
- Recommended minimal specific feature set: roughness spectrum at 4-5 baselines (level + shape), closed-depression area fraction, drainage integration (share of cell area that drains out of the cell vs into internal sinks), and an anisotropy ratio. Scale-normalise against the lunar south-pole reference population from PGDA-90.
- Data-quality caveat that cuts across everything: GLO-30 is an X-band radar surface model (vegetation, buildings, water flattening, voids filled in steep terrain) with effective resolution coarser than 30 m; LOLA polar DEMs are true bare-surface laser altimetry but with interpolation between tracks and a spatially variable effective resolution (LDEM_EFFRES). Restrict Earth candidates to bare/sparsely vegetated land and resample both to a common grid (the 30 m/px LDEM to 75S or coarser 60 m) before computing any feature.

### Gaps
- No published study was found that tests which DEM metrics separate impact-dominated from fluvially dissected terrain across Earth and Moon; the table above is the researcher's reasoning and should be presented as such.
- No source was found (or sought in depth) for drainage-density or valley-network statistics applied to the Moon; for Mars, valley-network drainage density literature exists (e.g. Hynek et al., Luo & Stepinski) but was not retrieved, [RECALL - UNVERIFIED].
- GLO-30 vertical accuracy and effective resolution figures were not retrieved in this session (out of the assigned scope; the team already has GLO-30 working).
