# Zodiak pitch script

Imagine you are preparing a rover to drive near the Moon's south pole. Before the mission, you want to rehearse somewhere you can reach. So where on Earth do you start looking, and how do you tell whether the terrain is similar enough for the test you have in mind?

We are Team Zodiak. We built a tool that finds Earth terrain resembling candidate lunar base regions, and that shows what each match leaves out.

First, what we measure. We take NASA's LOLA elevation data around seven candidate base regions and measure the shape of the terrain between about 200 metres and 1.6 kilometres: slopes, roughness and closed depressions. We run the same code on Earth, on Copernicus elevation, and keep ground that ESA WorldCover marks as bare. We scored 1,758,778 valid cells in 2,060 tiles and found 3,175 candidate patches. We do not measure boulders, rock, regolith, temperature or light.

Second, our default ranking, and its weak point. Our default mask counts "moss and lichen" as bare ground. So the top of the default ranking is Arctic plateaus, 16 of the top 30 on the Putorana Plateau in Siberia, and that ground is mostly moss-and-lichen tundra, not bare rock.

Third, the strict ranking. When we count only "bare or sparse vegetation", only 3 of the default top 30 remain. The strict top 30 is the Atacama and the Puna, the western Tibetan Plateau and Ladakh, the coastal desert of southern Peru, the Hazen Plateau in the Canadian Arctic, and Mauna Loa. We show both rankings and treat the strict one as the conservative reading.

Fourth, what validation shows. Our slope code reproduces NASA's lunar slope map to 0.042 degrees. At the scale of one-degree tiles, the score does not pick out known analog sites: the AUC is 0.531, consistent with chance. Around 22 known lunar analog sites, the median site holds 1.02 times the scan-wide share of lunar-like ground, against 0.39 for random circles; that is borderline, because 2.8 percent of random runs reach it. The ranks hardly move when we resample the lunar data, but they change a lot when we leave a feature group out.

Fifth, the literature. Of the strict top 30, 9 sites lie in known analog regions and 15 in regions that the pages we opened name as Mars analogs, never as Moon analogs; the other 6 were not found in the analog catalogues and searches we list. We do not call any of these places a discovery.

A team could use Zodiak to narrow the search, look at the images and evidence, and decide which places deserve a field visit, with every step traceable from NASA's lunar measurements to the Earth site.
