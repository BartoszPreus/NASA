# Zodiak pitch script

Imagine you are preparing a rover to drive near the Moon's south pole. Before the mission, you want to rehearse somewhere you can reach. So where on Earth do you start looking, and how do you tell whether the terrain is similar enough for the test you have in mind?

We are Team Zodiak. We built a tool to find Earth terrain that resembles candidate lunar base regions and to show what each match leaves out.

We start with NASA's LOLA elevation data around seven candidate base regions. We measure slopes, roughness and closed depressions. Then we run the same measurements on Earth, on Copernicus elevation data, and use ESA WorldCover to keep mostly bare ground with little water or ice. We join neighbouring cells into patches and rank the strongest local window in each patch. Dune-like patches stay visible with a flag because a hollow between dunes can look surprisingly lunar in an elevation grid.

We scored 1,758,778 valid cells across 2,060 tiles with stored data. That gives us 3,175 candidate terrain patches. The map turns those numbers into a regional shortlist. Here is an established example, Mauna Loa, alongside a lunar relief map. We can compare the terrain while looking at NASA imagery and context on conditions that differ, such as temperature.

We checked a plane-fit slope estimator against NASA's published map. The median absolute difference on the native grid was 0.042 degrees. None of the four control tiles produced a candidate after masking. We also tested a different elevation model and found that the choice changed which cells qualified. Around known analogs, the median enrichment was 0.91 times the bare-cell baseline, compared with 0.36 around matched random circles. The known sites did better than those random circles and still fell below the scan-wide baseline. That matters when interpreting the shortlist.

The same surface shape can come from volcanoes, glaciers, rivers or impacts. It can look right on a map and still have different rock, soil, temperature and lighting. Our literature review helps label places already used in analog research.

A team could use Zodiak to narrow the search, inspect imagery and evidence, and decide which locations deserve a field visit. The goal is to make that choice traceable, from NASA's lunar terrain measurements all the way to the Earth sites you might investigate.
