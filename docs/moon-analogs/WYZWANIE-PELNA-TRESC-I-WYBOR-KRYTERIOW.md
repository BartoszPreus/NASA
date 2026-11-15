# The "Moon and Mars analogs" challenge: full text + which criteria to choose
Page: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
Read: Sat 14 Nov 2026, about 16:45 (tabs **Details** and **Resources**). The analysis was done by Wiktor with Claude Code (SI). (Part 1 translated from Polish on 15 Nov 2026; historical.)
Part 1 is the analysis and recommendation, part 2 is the original NASA text in English, unchanged.

**Challenge tags:** level Advanced / Intermediate / Beginner-Youth · topics: Earth Science, Planets & Moons, Software, Space Exploration.

---
## Part 1. Analysis: what to choose from the list

### Conclusion in three sentences
1. The challenge lists **8 dimensions of analogy** and **12 "potential considerations"**, but says explicitly that they are optional ("You may (but are not required to)") and that an analog "does not need to match the Moon or Mars in every way".
2. We choose **one leading dimension (terrain) and two supporting ones (bare ground, temperature/illumination)**, and tie everything together with an application: landing and mobility tests.
3. We deliberately skip the other dimensions and say so explicitly on the site card ("we do not measure this"), because NASA rewards showing where the analogy breaks down.

### The 8 dimensions of analogy: a decision for each
The "Decision" column is a recommendation, not a NASA requirement.

| # | Dimension (from the challenge text) | Decision | Reason |
|---|---|---|---|
| 2 | Terrain: elevation, slope, roughness, craters | **LEADING** | Already works: slope fingerprint 57/225/560 m, scan of 38 tiles (`docs/PODSUMOWANIE-KIERUNKOW.md`). LOLA data are named in the challenge resources. |
| 8 | Conditions for landing, mobility, navigation, robotics, construction | **FRAME (use case)** | Needs no new data. Slope and roughness are directly parameters of landing safety and trafficability. Answers "Connect your analog to exploration". |
| 1 | Geology, mineralogy, surface materials | **SUPPORTING, minimal version** | We have a bare-ground filter (ESA WorldCover). We do not do mineralogy. Optionally rock abundance from Diviner, if time allows. |
| 3 | Temperature, illumination, extremes | **SUPPORTING** | Diviner is a separate item in the challenge resources, and the description says its polar products "could be compared with extreme cold (...) terrestrial environments". Plan: MODIS LST against Diviner + latitude as a proxy for the low Sun. **Not yet checked on data.** |
| 4 | Water, ice, permafrost, resources | skip | One sentence on the site card. Glaciers should at most be filtered out, because they inflate the terrain score. |
| 5 | Dust, wind, erosion, atmospheric processes | skip | Mainly about Mars. Our target is the lunar south pole. |
| 6 | Biology, extremophiles, biosignatures | skip | No global data and no expertise in the team. |
| 7 | Caves, lava tubes, subsurface | skip | Not visible in a 30 m DEM. |

**Why three and not eight:** our own scan showed that terrain alone is not enough (Tatras 36%, Alps 34% "lunar" cells; only the bare-ground filter removes them), so one dimension is too few. Every further dimension is a new data source and a new validation, and little time is left until the deadline (Sun 15 Nov, 13:30). Three dimensions give an honest "multidimensional similarity" and fit in the time.

### The 12 "potential considerations": what we have, what to add
| Consideration | Status | What to do |
|---|---|---|
| Think beyond visual similarity | ✅ our main thesis | Say it explicitly: we measure the shape of the terrain, not the look of an image. |
| Consider different dimensions of analogy | 🔶 partly | 3 dimensions as in the table above. |
| An analog does not have to match everything | ✅ fits the method | Show the result **separately for each dimension**, not as one number. |
| Think about processes as well as places | ❌ skip | One sentence: why polar and volcanic terrain have a 560/57 ratio close to the lunar one (hypothesis, not a result). |
| Look beyond well-known analog sites | 🔶 candidates exist, novelty unchecked | **Novelty filter**: list of known analogs + manual check of the top 5 in the literature. The page names as known: Antarctica, Atacama, Iceland, Hawaii, and in the summary also Haughton Crater and Death Valley. |
| Explore the whole Earth, including below its surface | 🔶 pilot of 38 tiles | A larger scan of bare-ground regions. We skip the subsurface. |
| Use multiple datasets when useful | ✅ | LOLA (PGDA) + Copernicus DEM + WorldCover; Diviner + MODIS LST will be added. |
| Consider scale | ✅ | Cells of about 2 km. Show that the result depends on the window (Meteor Crater at 2 km and 4 km). |
| Connect your analog to exploration | 🔶 only in the plan | Use case: where to practise landing and rover driving on terrain with roughness like near the lunar pole. |
| Be creative with your approach | ✅ | Similarity metric + ranking + map. The challenge names a "similarity-ranking system" explicitly. |
| Remember Earth's limits as an analog | 🔶 to be added | A fixed section on the site card: gravity, vacuum, radiation, regolith, vegetation, 30 m resolution. |
| Surprise us | 🔶 depends on the novelty filter | A non-obvious candidate (e.g. Tassili n'Ajjer, Kunlun) + Morasko as a counterexample. |

### Order of work (most important first)
1. **Novelty filter for the top 5.** Without it "Look beyond well-known sites" and "Surprise us" fall away, i.e. what sets the project apart.
2. **Site card**: result per dimension + "where the analogy breaks down". This covers four considerations at once at low cost.
3. **Temperature (Diviner + MODIS LST).** First 30 minutes to check whether the data can be downloaded and compared. If not, we stay with two dimensions and say so openly.
4. **Larger scan + map.**
5. **Pitch** in parallel from the start (Presentation criterion).

### How this relates to the 5 jury criteria
| Jury criterion | What raises it in this choice |
|---|---|
| Relevance | NASA data at the core: LOLA and Diviner are on the challenge resource list. |
| Creativity | A metric from terrain shape instead of image texture, a systematic scan instead of a hand-made list. |
| Validity | Known analogs come out high, controls low; explicit limits of the method. This is our weakest criterion, so we do not hide the limits. |
| Impact | Use case of lander and rover tests. |
| Presentation | One story: "where on Earth to practise landing near the lunar pole" + Morasko. |

### What this analysis does not settle
- The choice of dimensions assumes the LiDAR/DEM track described in `ANALOGI-LIDAR-RESEARCH-I-PLAN.md`. With a different project idea the table would look different.
- The feasibility of the temperature dimension is unchecked (Diviner has not been downloaded yet).
- The page says that resources may have been added before the start of the hackathon. State of the resources on 14 Nov: 11 links, the same as in `ANALOGI-KSIEZYC-MARS-LINKI.md`.

---
## Part 2. Original challenge text (EN, unchanged)

### Summary
Selecting future landing sites and lunar base locations depends on many factors, including topography, geology, environment, and available resources, to name a few. Places on Earth that have analogous characteristics to the Moon or Mars – the Atacama Desert, Haughton Crater, Death Valley – allow mission teams to test equipment and methods before they fly; however, such terrestrial analog sites are not entirely well characterized. Your challenge is to use open Earth, Moon, and Mars data from NASA and other space agencies to identify and characterize new terrestrial analogs for future bases or landing sites, drawing on deserts, polar regions, volcanic and arid terrains, caves, and other environments that share conditions with the lunar or Martian surface, then present your findings as a map, visualization, or other tool.

### Background
Earth is our most accessible laboratory for preparing to explore the Moon and Mars. Scientists and engineers already use terrestrial “analog” environments — deserts, polar regions, volcanic landscapes, impact craters, and caves — to study planetary processes and test instruments, technologies, and exploration concepts. However, no location on Earth perfectly reproduces another planetary environment, and different locations may provide useful analogs for different characteristics.

As humanity prepares for sustained exploration of the Moon and future human exploration of Mars, we could use open Earth, Moon, and Mars data to search globally and systematically for terrestrial environments that may provide useful — and perhaps previously unrecognized — analogs. Participants might consider dimensions such as geology and surface materials, terrain type and topography, atmospheric and aeolian processes such as dust storms, temperature and other environmental extremes, water or ice, biological and habitability characteristics, subsurface environments, and conditions relevant to robotic or human operations.

The goal is not simply to rediscover well-known analog sites, or to find one place that simply looks like the Moon or Mars. Participants are encouraged to combine datasets creatively to identify and characterize locations anywhere on Earth, explain what makes them analogous and what does not, and show how these environments could help conduct lunar or Mars science and exploration. Solutions might range from identifying a compelling individual site, environment, or geophysical process to developing maps, similarity metrics, machine learning approaches, or other innovative methods for discovering and comparing planetary analogs. You might consider Earth, Moon, Mars data obtained from various NASA and other space agencies missions, as well as data and images obtained locally.

### Objectives
Your challenge is to search our own planet Earth for places, environments and processes that could serve as analogs and can help us explore the Moon and Mars. Using open NASA Earth data together with available Moon and Mars data from other space agencies and open sources, identify and characterize one or more locations on Earth that could serve as useful analogs for candidate permanent Moon-base locations or future Mars landing and exploration sites. Explore what makes your Earth location analogous to the Moon or Mars. You might compare data and images of geology and surface materials, terrain and topography, temperature and environmental extremes, water or ice, dust and atmospheric processes, biology and habitability, caves or subsurface environments, or conditions relevant to robotic and human exploration. Your analog does not need to match the Moon or Mars in every way. Explain which characteristics or processes provide a strong analogy, where the analogy breaks down, and how studying or using your Earth analog could help prepare for the exploration of the Moon or Mars.

Be creative in how you search for, analyze, and communicate your analog. You could develop a written report, an interactive map, visualization, app, story, similarity-ranking system, ML tool, or another innovative approach. You might investigate a single compelling location, compare several locations around the world, or develop a method for systematically searching Earth for previously unrecognized analogs. Use open data from NASA and other space agencies as your window into Earth, the Moon, and Mars—and show us what our home planet can teach us about exploring the next ones. You might consider documenting your findings in a written format to share with other enthusiasts interested in the topic and to educate the public.

### Potential Considerations
*You may (but are not required to) consider the following:*

- **Think beyond visual similarity.** Two places may look alike but differ substantially in geology, environment, or physical processes. Use data to explain why your proposed Earth location is a meaningful analog.
- **Consider different dimensions of analogy**, including:
  - Geology, mineralogy, and surface materials
  - Terrain, elevation, slope, roughness, craters, and other topographic features
  - Temperature, illumination, and environmental extremes
  - Water, ice, permafrost, and other potential resources
  - Dust, wind, erosion, and other atmospheric or surface processes
  - Biology, extremophiles, habitability, and biosignatures
  - Caves, lava tubes, underground environments, and other subsurface features
  - Conditions relevant to landing, mobility, navigation, robotic operations, human exploration, or construction
- **An analog does not have to match everything.** An Earth location might be an excellent geological analog but a poor temperature analog, for example. Identify what is similar, how similar it is, and what is different.
- **Think about processes as well as places.** Earth processes such as sedimentation, dust storms, volcanic activity, erosion, ice dynamics, or water-driven alteration may provide insights into processes occurring today — or that occurred in the past — on the Moon or Mars.
- **Look beyond well-known analog sites.** Locations such as Antarctica, the Atacama Desert, Iceland, Hawaii are already widely studied. For example, NASA's global Earth-observation datasets may allow you to discover compelling analogs in places that have received much less attention.
- **Explore the whole Earth, including below its surface.** Polar regions, deserts, mountains, volcanoes, impact craters, salt flats, glaciers, caves, lava tubes, mines, and other environments could all offer interesting possibilities.
- **Use multiple datasets when useful.** Combining observations of terrain, temperature, geology, vegetation, water, ice, aerosols, or other characteristics may reveal relationships that are difficult to recognize using a single dataset.
- **Consider scale.** A continent or desert does not need to be treated as a single analog. A particular crater, valley, volcanic field, cave system, or even a small area within a much larger region could provide a much stronger match.
- **Connect your analog to exploration.** Explain how the location or process you identify could help scientists and engineers understand Moon, Mars, or both; test instruments or technologies, prepare robotic or human operations; search for resources or signs of habitability; or reduce exploration risks.
- **Be creative with your approach.** Maps and visualizations are welcome, but solutions could also use geographic information systems (GIS), statistical analysis, similarity metrics, machine learning, interactive applications, games, or other innovative methods.
- **Remember Earth's limits as an analog.** Earth cannot reproduce important lunar and Martian conditions such as reduced gravity, the lunar vacuum, the thin Martian atmosphere, or their radiation environments. Recognizing these differences is part of good scientific analysis.
- **Surprise us.** A strong solution may identify an unexpected Earth location, reveal an unexpected connection between Earth and Moon or Mars, or introduce a new way of using Earth data to help enable future exploration.

*For data and resources related to this challenge, refer to the Resources tab at the top of the page. More resources may be added before the hackathon begins.*

### Resources
*NASA does not endorse any non-U.S. Government entity and is not responsible for information contained on non-U.S. Government websites. For non-U.S. Government websites, participants must comply with any data use parameters of that specific website.*

#### NASA Data & Resources
**Earth**
- [NASA Earthdata Search](https://search.earthdata.nasa.gov/): NASA's primary portal for discovering and accessing Earth science observations.
- [NASA Worldview](https://worldview.earthdata.nasa.gov/index.html): An easy-to-use interactive environment for visually exploring NASA satellite imagery and environmental observations.

**Moon and Mars**
- [NASA Planetary Data System (PDS)](https://pds.nasa.gov/): NASA's long-term archive for planetary science data from NASA orbital, lander, and rover missions. It provides access to lunar and Martian mission observations spanning imagery, geoscience, atmospheres, plasma environments, cartography, and other measurements.
- [NASA Lunar Reconnaissance Orbiter (LRO)](https://pds-geosciences.wustl.edu/missions/lro/): LRO provides extensive observations of the lunar surface through instruments including LROC, LOLA, Diviner, LEND, Mini-RF and others.
- [NASA LRO Diviner Lunar Data](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm): Diviner maps lunar surface temperatures and provides especially useful products for studying the lunar poles. Its polar and resource products could be compared with extreme cold, ice-bearing, or other terrestrial environments.

#### Space Agency Partner Resources
**CSA (Canadian Space Agency)**
- [RADARSAT Constellation Mission (RCM) - Data](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm): RCM is Canada's new generation of Earth observation satellites. The RCM includes a trio of Earth observation satellites, capable of scanning Earth day or night and in any weather conditions. The RCM is designed to provide effective solutions in three main areas: Maritime surveillance (ice, surface wind, oil pollution and ship monitoring); Disaster management (mitigation, warning, response and recovery); and Ecosystem monitoring (agriculture, wetlands, forestry and coastal change monitoring).
- [RADARSAT 1 - Data](https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1): Launched in November 1995, RADARSAT-1 provided Canada and the world with an operational radar satellite system capable of timely delivery of large amounts of data. Equipped with a powerful synthetic aperture radar (SAR) instrument, it acquired images of the Earth day or night, in all weather and through cloud cover, smoke and haze. All data products in the Canadian RADARSAT-1 archive have been released under an open license.
- [Synthetic Aperture Radar (SAR) Python Tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial): This tutorial demonstrates how to work with SAR imagery using Python and QGIS. It includes easy and practical steps for accessing and visualizing data.

**ESA (European Space Agency)**
- [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/): Provides free and open access to Sentinel Earth-observation data covering land, oceans, and atmosphere, with tools for visualization and processing.
- [ESA Open Science Catalog](https://opensciencedata.esa.int/): A catalog of publicly available geoscience datasets, products, experiments, and workflows.

**JAXA (Japan Aerospace Exploration Agency)**
- [JAXA G-Portal](https://gportal.jaxa.jp/gpr/index/index): Provides Earth-observation products from JAXA missions, searchable by variables such as precipitation, snow, vegetation, etc.

*Editorial note: the tracking parameter `utm_source` was removed from the links; the rest of the addresses are as on the page.*
