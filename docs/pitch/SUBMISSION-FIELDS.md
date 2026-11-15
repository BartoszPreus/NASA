# NASA Space Apps portal fields

Each section below maps to a field in the [submission checklist](../hackathon/Zgloszenie-projektu-checklista.md). The team owner can paste the English text after confirming the links and final wording.

## Project Name

Zodiak | Earth Terrain Analogs for the Lunar South Pole

## High-Level Project Summary

Where on Earth could mission teams rehearse rover mobility or landing terrain procedures for the lunar south pole? Zodiak uses NASA lunar elevation data to describe candidate base regions, then searches Earth for comparable terrain. We ranked contiguous patches from 1,758,778 valid cells in 2,060 tiles with stored data. The results pair each terrain match with imagery, documented analogs, and evidence about where the comparison breaks. The shortlist helps teams decide where to investigate next.

## Link to Project Demo

**Team owner:** Insert a public, no-login URL for the slide demo built from [the seven-slide outline](SLIDES-7.md), or for the agreed video. Open it in a private window before submission. The checked-in [ranking map](ranking-map.png) illustrates the result while the interactive app is being prepared in [issue #3](https://github.com/BartoszPreus/NASA/issues/3).

## Link to Final Project

https://github.com/BartoszPreus/NASA

**Team owner:** Confirm this link opens without sign-in before submitting. Use the team's public project URL here if it becomes the primary deliverable.

## Detailed Project Description

Zodiak applies the same slope, roughness and closed-depression measurements to NASA LOLA lunar elevation and Copernicus Earth elevation. The default reference pools seven candidate lunar base regions. ESA WorldCover filters Earth cells by bare ground, ice and water. The pipeline combines connected cells into patches, ranks their best 15 × 15 km windows, and uses a terrain rule to put dune-like relief last. NASADEM and MODIS provide an alternative Earth input for comparison. NASA Worldview, POWER, Diviner and partner data help explain why a similar landform can still differ sharply in operating conditions.

The scanned data yielded 3,175 candidate terrain patches. Our checks include NASA's published lunar slope map, independent ICESat-2 laser tracks, negative controls, and a comparison of known sites with random circles. At the scale of one-degree tiles, the score does not separate known analog sites from the rest of the scanned land. The method screens terrain for further study. It cannot determine regolith, environmental equivalence, or whether a site is suitable or accessible for a field trial. For the Moon-to-Earth comparison we deliver a reproducible Python pipeline, downloadable results, a ranking map, and a source and validation report.

## Use of Super Intelligence (SI)

The team chose the challenge, the research goals and the interpretation. We used Claude Code, Antigravity and OpenAI Codex to assist with coding, data checks, research and drafting. We reviewed generated claims against source records and committed numerical outputs. The included plots are rendered from data and the satellite imagery is credited to its providers.

## NASA Data

NASA LRO LOLA elevation from Goddard PGDA drives the lunar reference. NASA LOLA slope maps and the Planetary Data System grid are used for validation. ICESat-2 ATL06 laser profiles are an independent check of Earth grid slopes. NASADEM and MODIS land cover form an alternative Earth input. Worldview/GIBS imagery, POWER climate, MODIS surface temperatures, and LRO Diviner, LROC, Mini-RF, LEND and LAMP describe the compared environments. The [complete NASA source table](https://github.com/BartoszPreus/NASA#nasa-data) links each product and its citation.

## Space Agency Partner Data and Other References

We use ESA/Copernicus elevation and ESA WorldCover for Earth terrain and land cover. The ESA Open Science Catalog points to the ESA CCI permafrost cube sampled for context. JAXA G-Portal products accessed through the JAXA Earth API provide GCOM-C/SGLI surface temperature and GCOM-W/AMSR2 soil moisture. USGS 3DEP and Polish GUGiK lidar illustrate scale and resolution. Natural Earth supplies map outlines, and terrain names and known analogs have recorded sources. The [partner and reference tables](https://github.com/BartoszPreus/NASA#partner-agency-data) give provider links, credits and product-specific terms.

We reviewed RADARSAT Constellation Mission, RADARSAT-1 and the Canadian Space Agency radar tutorial and left them out because the terrain comparison uses elevation grids and does not process Earth radar imagery.
