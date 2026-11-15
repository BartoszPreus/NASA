# NASA Space Apps portal fields

Each section below maps to a field in the [submission checklist](../hackathon/Zgloszenie-projektu-checklista.md). The team owner can paste the English text after confirming the links and final wording.

## Project Name

Zodiak | Earth Terrain Analogs for the Lunar South Pole

## High-Level Project Summary

Where on Earth could mission teams rehearse rover mobility or landing terrain procedures for the lunar south pole? Zodiak uses NASA lunar elevation data to describe candidate base regions, then searches Earth for comparable terrain. It compares the shape of the terrain between about 200 m and 1.6 km and ranks contiguous patches from 1,758,778 valid cells in 2,060 tiles. Our default ranking is led by Arctic moss-and-lichen tundra; counting only bare or sparsely vegetated ground, the shortlist becomes the Atacama and Puna, western Tibet and Ladakh, the coastal desert of southern Peru, the Hazen Plateau and Mauna Loa. Each match comes with imagery, documented analogs, validation that is honest about its limits, and evidence about where the comparison breaks.

## Link to Project Demo

DEMO LINK PLACEHOLDER

*DECISION FOR THE TEAM: hosting of the web app and the demo link (issue #11).*

**Team owner:** Insert a public, no-login URL for the slide demo built from [the seven-slide outline](SLIDES-7.md), or for the agreed video. Open it in a private window before submission. The checked-in [ranking map](ranking-map.png) illustrates the result while the interactive app is being prepared in [issue #3](https://github.com/BartoszPreus/NASA/issues/3).

## Link to Final Project

https://github.com/BartoszPreus/NASA

**Team owner:** Confirm this link opens without sign-in before submitting. Use the team's public project URL here if it becomes the primary deliverable.

## Detailed Project Description

Zodiak applies the same slope, roughness and closed-depression measurements to NASA LOLA lunar elevation and Copernicus Earth elevation. The default reference pools seven candidate lunar base regions. ESA WorldCover filters Earth cells by bare ground, ice and water. The pipeline combines connected cells into patches, ranks their best 15 × 15 km windows, and uses a terrain rule to put dune-like relief last. NASADEM and MODIS provide an alternative Earth input for comparison. NASA Worldview, POWER, Diviner and partner data help explain why a similar landform can still differ sharply in operating conditions.

The scanned data yielded 3,175 candidate terrain patches. The similarity is about terrain shape between about 200 m and 1.6 km only; boulders, rock, regolith, temperature and light are not in the score. The default land-cover mask counts ESA WorldCover "moss and lichen" as bare, so the top of the default ranking is mostly Arctic tundra (16 of its top 30 on the Putorana Plateau). With "bare / sparse vegetation" only, 3 of the default top 30 remain, and the strict top 30 is the Atacama and Puna (13), the western Tibetan Plateau and Ladakh (8), southern Peru and Arica (4), the Hazen Plateau (3), Mauna Loa (1) and one other site; we present both, the strict one as the conservative reading.

Our checks include NASA's published lunar slope map (median difference 0.042°), independent ICESat-2 laser tracks, negative controls, and a comparison of known sites with random circles. At the scale of one-degree tiles, the score does not separate known analog sites from the rest of the scanned land (AUC 0.531, consistent with chance). Around 22 known lunar analogs the median enrichment of lunar-like ground is 1.02× the scan-wide rate against 0.39× for random circles, a borderline result. Ranks are stable when the lunar sample is resampled and sensitive to which terrain features are used. A literature check of the strict top 30 found 9 sites in known analog regions, 15 in regions named as Mars analogs and 6 not found in the catalogues and searches we list; we do not call any of them a discovery. The method screens terrain for further study. It cannot determine regolith, environmental equivalence, or whether a site is suitable or accessible for a field trial. For the Moon-to-Earth comparison we deliver a reproducible Python pipeline, downloadable results, a ranking map, and a source and validation report.

## Use of Super Intelligence (SI)

The team chose the challenge, the research goals and the interpretation. We used Claude Code, Antigravity and OpenAI Codex to assist with coding, data checks, research and drafting. We reviewed generated claims against source records and committed numerical outputs. The included plots are rendered from data and the satellite imagery is credited to its providers.

## NASA Data

NASA LRO LOLA elevation from Goddard PGDA drives the lunar reference. NASA LOLA slope maps and the Planetary Data System grid are used for validation. ICESat-2 ATL06 laser profiles are an independent check of Earth grid slopes. NASADEM and MODIS land cover form an alternative Earth input. Worldview/GIBS imagery (MODIS, VIIRS and 30 m HLS for the review of the strict top 30), POWER climate, MODIS surface temperatures, and LRO Diviner, LROC, Mini-RF, LEND and LAMP describe the compared environments. The [complete NASA source table](https://github.com/BartoszPreus/NASA#nasa-data) links each product and its citation.

## Space Agency Partner Data and Other References

We use ESA/Copernicus elevation and ESA WorldCover for Earth terrain and land cover. The ESA Open Science Catalog points to the ESA CCI permafrost cube sampled for context. JAXA G-Portal products accessed through the JAXA Earth API provide GCOM-C/SGLI surface temperature and GCOM-W/AMSR2 soil moisture, and JAXA AW3D30 is a third elevation model on ten reference tiles. USGS 3DEP and Polish GUGiK lidar illustrate scale and resolution. Natural Earth supplies map outlines, and terrain names and known analogs have recorded sources. The [partner and reference tables](https://github.com/BartoszPreus/NASA#partner-agency-data) give provider links, credits and product-specific terms.

The Canadian Space Agency's RADARSAT-1 archive and radar tutorial support a separate comparison of Earth radar texture with lunar Mini-RF. The terrain score comes from elevation grids. We reviewed the RADARSAT Constellation Mission resource for a separate polarimetry comparison.
