"""pipeline.nasa_context deletes images that its index.csv no longer lists (J41 note, issue #27)."""
import pandas as pd

from pipeline import nasa_context


def test_prune_images_keeps_indexed_and_removes_the_rest(tmp_path):
    for name in ("A-01.jpg", "B-01.jpg", "C-01.jpg", "notes.txt"):
        (tmp_path / name).write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "D-01.jpg").write_bytes(b"x")
    index = pd.DataFrame({"site_id": ["A-01", "B-01", "E-01"],
                          "file": ["data/sites/images/A-01.jpg", "data/sites/images/B-01.jpg", None]})

    removed = nasa_context.prune_images(tmp_path, index)

    assert removed == ["C-01.jpg"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["A-01.jpg", "B-01.jpg", "notes.txt", "sub"]
    assert (sub / "D-01.jpg").exists()  # only the folder itself is pruned


def test_run_images_prunes_after_writing_the_index(tmp_path, monkeypatch):
    (tmp_path / "OLD-01.jpg").write_bytes(b"x")

    def fake_row(site, img_dir):
        out = img_dir / f"{site.site_id}.jpg"
        out.write_bytes(b"x")
        return {"site_id": site.site_id, "lat": site.lat, "lon": site.lon, "bbox": "", "date": "2024-01-01",
                "layer": "L", "file": f"data/sites/images/{out.name}", "white_share": 0, "dark_share": 0,
                "bytes": 1, "note": ""}

    monkeypatch.setattr(nasa_context, "image_row", fake_row)
    sites = pd.DataFrame({"site_id": ["NEW-01"], "lat": [1.0], "lon": [2.0]})
    nasa_context.run_images(sites, tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["NEW-01.jpg", "index.csv"]
