# Zodiak Earth–Moon Terrain Atlas

The atlas shows candidate terrain patches from the Earth survey alongside the lunar south pole reference regions. The rank reflects terrain geometry at the published scales. The comparison cards add environmental context and link to the evidence.

From the repository root with Python 3.12 or later:

```console
python app/build_data.py
python -m http.server 8000 --bind 127.0.0.1 --protocol HTTP/1.1 --directory app
```

Open [the local atlas](http://127.0.0.1:8000/). The data export reads the tracked pipeline outputs. The app is plain HTML, CSS and JavaScript with Leaflet. A bundled copy of Leaflet supports a local demonstration without a CDN connection. The geographic backdrop is bundled too. Serve this folder over HTTP so the browser can fetch the JSON files.

Search by site ID, country or place and select a ranked patch or map marker. Change the lunar target in the card to see comparison ranges and the selected region's recorded instrument values. The map and list can filter out known analogs and can include the group flagged by the dune-like terrain rule. The link in the card saves a site and target to share within any served copy. Method and sources has the pipeline steps and keys for the validation results.

- [Export schema](data/SCHEMA.md)
- [Data and application citations](../docs/sources/j7.md)

Written with SI assistance (Codex).
