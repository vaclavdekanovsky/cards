import os
from typing import Optional

try:
    import geopandas as gpd
except Exception as e:
    import sys

    msg = (
        "Failed to import geopandas (and dependencies).\n"
        f"Python executable: {sys.executable}\n"
        "If using Conda, try:\n"
        "  conda install -c conda-forge geopandas shapely fiona pyproj gdal mkl-service\n"
        "Or with pip (in a clean env):\n"
        "  pip install geopandas shapely fiona pyproj matplotlib\n"
        f"Original error: {e}"
    )
    raise SystemExit(msg) from e

import matplotlib.pyplot as plt


# Public world countries GeoJSON (Natural Earth derived)
WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"


def auto_detect_continent_field(df: gpd.GeoDataFrame) -> Optional[str]:
    candidates = [
        "continent",
        "CONTINENT",
        "Continent",
        "region_un",
        "REGION_UN",
        "region_wb",
        "UNREGION1",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    expected = {"Africa", "Europe", "Asia", "Oceania", "North America", "South America", "Americas"}
    for c in df.columns:
        try:
            uniques = set(map(lambda x: str(x) if x is not None else "", df[c].unique()))
        except Exception:
            continue
        if len(expected & uniques) >= 2:
            return c
    return None


def select_continent(df: gpd.GeoDataFrame, continent_field: str, values):
    values_lower = {v.lower() for v in values}
    return df[df[continent_field].astype(str).str.lower().isin(values_lower)]


def union_geom(df: gpd.GeoDataFrame):
    if df.empty:
        return None
    return df.geometry.unary_union


def save_filled_png(geom, out_path: str, dpi: int = 300):
    if geom is None or geom.is_empty:
        print(f"Skipping {out_path} (empty geometry)")
        return
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="datalim")

    gpd.GeoSeries([geom], crs="EPSG:4326").plot(
        ax=ax, facecolor="black", edgecolor="black", linewidth=0.4
    )

    minx, miny, maxx, maxy = gpd.GeoSeries([geom]).total_bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    plt.savefig(out_path, dpi=dpi, bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close(fig)
    print(f"Saved {out_path}")


def main():
    print("Loading world GeoJSON from the internet…")
    df = gpd.read_file(WORLD_GEOJSON_URL)
    if df.crs is None:
        df = df.set_crs(epsg=4326, allow_override=True)

    field = auto_detect_continent_field(df)
    if not field:
        raise SystemExit("Could not detect a continent field in the dataset.")

    groups = {
        "americas": ["Americas", "North America", "South America"],
        "europe": ["Europe"],
        "asia": ["Asia"],
        "africa": ["Africa"],
        "australia": ["Oceania", "Australia", "Australia and New Zealand"],
    }

    # Build individual geometries
    geoms = {}
    for name, vals in groups.items():
        sel = select_continent(df, field, vals)
        geoms[name] = union_geom(sel)

    # Combine Africa + Australia
    from shapely.ops import unary_union

    africa_australia = None
    if geoms.get("africa") is not None and geoms.get("australia") is not None:
        africa_australia = unary_union([geoms["africa"], geoms["australia"]])
    else:
        africa_australia = geoms.get("africa") or geoms.get("australia")

    # Save PNGs (filled black, transparent background)
    save_filled_png(geoms.get("americas"), os.path.join("output", "americas.png"))
    save_filled_png(geoms.get("europe"), os.path.join("output", "europe.png"))
    save_filled_png(geoms.get("asia"), os.path.join("output", "asia.png"))
    save_filled_png(africa_australia, os.path.join("output", "africa_australia.png"))


if __name__ == "__main__":
    main()
