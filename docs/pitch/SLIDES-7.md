# Zodiak slide outline

Use these seven slides for the demo draft. Numeric claims and figure inputs are documented in [NUMBERS.md](NUMBERS.md). The team owner adds the final public demo link and confirms the official submission wording.

| Slide | One sentence to land | Figure files | Numbers to show |
|---|---|---|---|
| 1. Zodiak | We search Earth for terrain where mission teams could rehearse work planned for the lunar south pole. | [Lunar relief at Haworth](../../data/moon/hillshade/haworth.png), NASA LOLA | None |
| 2. What counts as a terrain match | We measure slope, roughness and depressions on both bodies and filter Earth terrain by land cover. | [Haworth lunar relief](../../data/moon/hillshade/haworth.png), NASA LOLA | Seven lunar reference regions |
| 3. From a scan to a shortlist | The ranking shows the best local match in each patch, and the full site catalogue retains likely dune fields with a flag. | [Ranking map](ranking-map.png), plot from the committed ranking | 1,758,778 valid cells; 2,060 tiles; 3,175 patches; 15 × 15 km ranking window |
| 4. What holds up | The plane-fit lunar slope check agrees closely with NASA, and the Earth controls produce no candidates after masking. | [Negative controls](../figures/eff_j20_controls.png) | 0.042° median absolute NASA map difference on the native grid; zero candidates in four masked controls |
| 5. Where the analogy breaks | Earth terrain can look like lunar terrain while its rocks, weather and operating conditions still differ. | [Mauna Loa satellite image](../../data/sites/images/N19W156-01.jpg), NASA Worldview/GIBS; [Haworth lunar relief](../../data/moon/hillshade/haworth.png), NASA LOLA | None |
| 6. Why we validate and review | A shortlist is useful because the team can see how model choice, known-site checks and literature change its interpretation. | [Known-site enrichment](../figures/eff_enrichment.png) | 0.91× known-site median versus 0.35× random-circle median; both relative to the scan-wide bare-cell rate |
| 7. What a mission team would do next | Use the regional shortlist to choose where to inspect geology, access and rover conditions before field work. | [Ranking map](ranking-map.png) | None |

**Title slide:** Team Zodiak · Bartosz Preus, Hubert Włodzimierz Woźniak, Wiktor Witczak, Oliwier Gołembiewski · NASA Space Apps 2026 · *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*.

**Presenter notes:** Use Mauna Loa as an established example already in the reference registry. Show the credit beside each NASA image. Keep site-specific new candidate examples out of the final demo until the checks in [the J22 report](../NOVELTY.md) are complete. Replace the static ranking map with an app screenshot if the team has a verified demo.
