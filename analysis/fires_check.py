"""Feasibility check: MODIS -> VIIRS S-NPP hot-spot harmonization for Poland.

Data sources (NASA FIRMS yearly country archives, public, no login / MAP_KEY needed):
  https://firms.modaps.eosdis.nasa.gov/country/
  https://firms.modaps.eosdis.nasa.gov/data/country/modis/{YYYY}/modis_{YYYY}_Poland.csv        (2000-2025)
  https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/{YYYY}/viirs-snpp_{YYYY}_Poland.csv (2012-2025)
Citation: NASA FIRMS, MODIS Collection 6.1 (MCD14) and VIIRS S-NPP 375 m (VNP14IMG) active fire products,
  https://www.earthdata.nasa.gov/data/tools/firms

Usage: python -I fires_check.py <data_dir>
"""
import glob
import os
import sys
import time

import numpy as np
import pandas as pd

t0 = time.time()
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "data")
BIEBRZA = dict(lat=(53.2, 53.75), lon=(22.3, 23.1))  # approximate Biebrza NP bounding box


def load(prefix):
    files = sorted(glob.glob(os.path.join(DATA, f"{prefix}_*_Poland.csv")))
    df = pd.concat([pd.read_csv(f, dtype={"acq_time": str, "confidence": str}) for f in files], ignore_index=True)
    return df, files


modis_raw, mf = load("modis")
viirs_raw, vf = load("viirs-snpp")
print(f"Files: MODIS {len(mf)}, VIIRS {len(vf)}; total MB "
      f"{sum(os.path.getsize(f) for f in mf + vf) / 1e6:.1f}")
print(f"Raw rows: MODIS {len(modis_raw):,}  VIIRS S-NPP {len(viirs_raw):,}")


def clean(df, sensor):
    df = df.copy()
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    n0 = len(df)
    if sensor == "modis":
        df = df[pd.to_numeric(df["confidence"], errors="coerce") >= 30]   # MODIS confidence 0-100
    else:
        df = df[df["confidence"].str.lower() != "l"]                       # VIIRS l / n / h
    n1 = len(df)
    if "type" in df.columns:
        df = df[df["type"] == 0]                                           # 0 = presumed vegetation fire
    print(f"{sensor}: {n0:,} -> {n1:,} after confidence -> {len(df):,} after type==0")
    return df


modis = clean(modis_raw, "modis")
viirs = clean(viirs_raw, "viirs")
print("Type distribution raw MODIS:", modis_raw["type"].value_counts().to_dict(),
      " VIIRS:", viirs_raw["type"].value_counts().to_dict())


def monthly(df):
    s = df.groupby([df.acq_date.dt.year.rename("year"), df.acq_date.dt.month.rename("month")]).size()
    return s


m = monthly(modis)
v = monthly(viirs)
years = range(max(m.index.get_level_values(0).min(), v.index.get_level_values(0).min()),
              min(m.index.get_level_values(0).max(), v.index.get_level_values(0).max()) + 1)
idx = pd.MultiIndex.from_product([list(years), range(1, 13)], names=["year", "month"])
tab = pd.DataFrame({"modis": m.reindex(idx, fill_value=0), "viirs": v.reindex(idx, fill_value=0)})
print(f"\nOverlap years: {years.start}-{years.stop - 1}")
print("Annual counts (filtered):")
ann = tab.groupby("year").sum()
ann["ratio"] = (ann.viirs / ann.modis).round(2)
print(ann.to_string())

# (b) per-calendar-month ratio VIIRS/MODIS, median over years and its spread
tab["ratio"] = np.where(tab.modis > 0, tab.viirs / tab.modis.replace(0, np.nan), np.nan)
g = tab.groupby("month")["ratio"]
stab = pd.DataFrame({"median": g.median(), "q25": g.quantile(.25), "q75": g.quantile(.75),
                     "min": g.min(), "max": g.max(), "n_years": g.count(),
                     "modis_mean": tab.groupby("month").modis.mean(),
                     "viirs_mean": tab.groupby("month").viirs.mean()}).round(2)
stab["IQR/median"] = ((stab.q75 - stab.q25) / stab["median"]).round(2)
print("\nPer-calendar-month VIIRS/MODIS ratio over all overlap years:")
print(stab.to_string())

# (c) calibrate on overlap years except last 2 full years, test on those 2
test_years = [years.stop - 2, years.stop - 1]
train = tab[~tab.index.get_level_values("year").isin(test_years)]
test = tab[tab.index.get_level_values("year").isin(test_years)].copy()
k_month = train.groupby("month")["ratio"].median()
k_global = train.viirs.sum() / train.modis.sum()
test["pred_month_k"] = test.modis * test.index.get_level_values("month").map(k_month).values
test["pred_global_k"] = test.modis * k_global


def score(pred, obs):
    return np.mean(np.abs(pred - obs)), np.corrcoef(pred, obs)[0, 1]


print(f"\nHeld-out years {test_years}; train {years.start}-{test_years[0] - 1}; global k = {k_global:.2f}")
for name in ["modis", "pred_global_k", "pred_month_k"]:
    mae, r = score(test[name].values, test.viirs.values)
    print(f"  {name:14s} MAE = {mae:8.1f} hot spots/month   Pearson r = {r:.3f}")
mae_g = score(test.pred_global_k.values, test.viirs.values)[0]
print(f"  mean observed VIIRS/month in test = {test.viirs.mean():.1f}; "
      f"MAE global-k as % of mean = {100 * mae_g / test.viirs.mean():.0f}%")
print(test[["modis", "viirs", "pred_global_k", "pred_month_k"]].round(0).astype(int).to_string())

# (d) Biebrza NP fire calendar: April 2020 vs median April of other years
print("\nBiebrza NP bbox lat 53.2-53.75, lon 22.3-23.1 (filtered detections), April counts:")
for name, df in [("MODIS", modis), ("VIIRS", viirs)]:
    b = df[df.latitude.between(*BIEBRZA["lat"]) & df.longitude.between(*BIEBRZA["lon"])]
    apr = b[b.acq_date.dt.month == 4].groupby(b.acq_date.dt.year).size()
    yrs = range(df.acq_date.dt.year.min(), df.acq_date.dt.year.max() + 1)
    apr = apr.reindex(yrs, fill_value=0)
    others = apr.drop(2020)
    print(f"  {name}: April 2020 = {apr.get(2020, 0)}; median April other years = {others.median():.0f} "
          f"(max other = {others.max()} in {others.idxmax()}); per-year: {apr.to_dict()}")

print(f"\nProcessing time: {time.time() - t0:.1f} s")
