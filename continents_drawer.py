import geopandas as gpd
import matplotlib.pyplot as plt
import os
from shapely.geometry import Polygon

import json

# based on files from https://hub.arcgis.com/datasets/esri::world-continents/explore

# --- Global Configuration ---
# The configuration will be loaded in the main execution block.

# Column in the shapefile that identifies the continents
CONTINENT_NAME_COLUMN = "CONTINENT"

# Colors for each continent group we want to draw
CONTINENT_COLORS = {
    "Europe": "blue",
    "Asia": "yellow",
    "Americas": "red",
    "Africa": "grey",
    "Oceania": "grey"
}

# --- Main Script ---

def draw_continent(output_name, color, all_continents_data, output_dir):
    """
    Draws a silhouette of a continent group using the provided data and saves it as a PNG.
    """
    print(f"Processing {output_name}...")

    # Determine which continent names from the file to use for the group
    if output_name == "Americas":
        names_in_file = ['North America', 'South America']
    elif output_name == "Oceania":
        names_in_file = ['Australia', 'Oceania']
    else:
        names_in_file = [output_name]
    
    # Filter the data to get the geometry for the specified continent(s)
    continent_selection = all_continents_data[all_continents_data[CONTINENT_NAME_COLUMN].isin(names_in_file)]

    if continent_selection.empty:
        print(f"Warning: No data found for '{output_name}' in the shapefile. Skipping.")
        return

    # Create a clipping mask in Lat/Lon (EPSG:4326) and then transform it
    # to the shapefile's native Coordinate Reference System (CRS) before clipping.
    clip_poly = Polygon([(-180, -85), (180, -85), (180, 85), (-180, 85)])
    clip_mask_latlon = gpd.GeoDataFrame([1], geometry=[clip_poly], crs="EPSG:4326")
    clip_mask = clip_mask_latlon.to_crs(all_continents_data.crs)
    
    # Perform the clip operation using the correctly projected mask.
    continent_clipped = gpd.clip(continent_selection, clip_mask)

    if continent_clipped.empty:
        print(f"Warning: Geometry for '{output_name}' is empty after clipping. Skipping.")
        return

    # Combine the geometries of the clipped parts
    continent_geom = continent_clipped.union_all()

    # Clean the geometry. buffer(0) is a standard trick for fixing invalid geometries.
    continent_geom = continent_geom.buffer(0)

    if not continent_geom or continent_geom.is_empty:
        print(f"Warning: Resulting geometry for '{output_name}' is empty. Skipping.")
        return

    # --- Plotting with Projection ---

    # Create a GeoSeries, correctly using the file's native CRS
    continent_gs = gpd.GeoSeries([continent_geom], crs=all_continents_data.crs)

    # Use custom projections for continents split by the dateline/prime meridian.
    if output_name == "Asia":
        # Center on 100°E
        custom_projection = "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        continent_projected = continent_gs.to_crs(custom_projection)
    elif output_name == "Americas":
        # Center on 100°W
        custom_projection = "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=-100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        continent_projected = continent_gs.to_crs(custom_projection)
    elif output_name == "Oceania":
        # Center on 150°E
        custom_projection = "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=150 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        continent_projected = continent_gs.to_crs(custom_projection)
    else:
        # Use the standard Robinson projection for other continents (Europe, Africa).
        continent_projected = continent_gs.to_crs("ESRI:54030")

    # Create a plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Plot the re-projected continent shape
    continent_projected.plot(ax=ax, facecolor=color, edgecolor=color)

    # Customize the plot for a clean silhouette
    ax.set_axis_off()
    ax.set_aspect('equal')

    # Set plot limits to bound the re-projected continent
    bounds = continent_projected.total_bounds
    ax.set_xlim([bounds[0], bounds[2]])
    ax.set_ylim([bounds[1], bounds[3]])

    # Save the figure
    filename = f"{output_name.lower()}.png"
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)
    print(f"Saved {output_path}")
    
    plt.close(fig)


if __name__ == "__main__":
    # Load configuration from JSON file
    try:
        with open("configuration.json", 'r') as f:
            config = json.load(f)
        base_input_dir = config['input_folder']
        base_output_dir = config['output_folder']
    except FileNotFoundError:
        print("Error: configuration.json not found. Please ensure the file exists.")
        exit()
    except KeyError:
        print("Error: configuration.json is missing 'input_folder' or 'output_folder'.")
        exit()

    # Define specific input and output directories based on the config
    INPUT_DIR = os.path.join(base_input_dir, "continent_maps")
    OUTPUT_DIR = os.path.join(base_output_dir, "continent_images")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # The shapefile for continents, located in the input directory
    SHAPEFILE = os.path.join(INPUT_DIR, "World_Continents.shp")

    # Check if the shapefile exists
    if not os.path.exists(SHAPEFILE):
        print(f"Error: Shapefile not found at '{SHAPEFILE}'")
        exit()

    # Load the continents dataset
    try:
        world_continents = gpd.read_file(SHAPEFILE)
    except Exception as e:
        print(f"Error reading shapefile: {e}")
        print("Please make sure you have 'geopandas' and its dependencies installed correctly.")
        exit()

    # --- Generate Continent Images ---
    for name, color in CONTINENT_COLORS.items():
        draw_continent(name, color, world_continents, OUTPUT_DIR)

    print("\nContinent drawing complete.")
    print(f"Images saved in '{OUTPUT_DIR}' directory.")