import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image
import svgwrite
import os

# Set config to restore SHX file if missing/corrupted
os.environ['SHAPE_RESTORE_SHX'] = 'YES'

def render_continent_from_shapefile(shapefile_path, continent='americas', output_png='continent.png', 
                                   output_svg='continent.svg', min_area=0.5, use_projection=True, 
                                   fill_color='#FF9999', show_borders=False):
    """
    Read countries shapefile and render continent to PNG and SVG
    
    Parameters:
    shapefile_path: path to ne_10m_admin_0_countries.shp
    continent: 'americas', 'europe', 'asia', 'africa', 'oceania', 'africa_oceania'
    min_area: minimum area in square degrees to keep (filters tiny islands)
    use_projection: if True, uses a map projection to make continents more slender
    fill_color: hex color for the fill
    show_borders: if True, shows borders around countries
    """
    
    # Read the shapefile
    print(f"Reading shapefile: {shapefile_path}")
    gdf = gpd.read_file(shapefile_path)
    
    # Set CRS if not defined (Natural Earth data is in WGS84)
    if gdf.crs is None:
        print("Setting CRS to EPSG:4326 (WGS84)...")
        gdf = gdf.set_crs('EPSG:4326')
    
    print(f"Current CRS: {gdf.crs}")
    print(f"Available columns: {gdf.columns.tolist()}")
    
    # Detect the continent column name (can be CONTINENT or CONT_NAME or other variations)
    continent_col = None
    for col in ['CONTINENT', 'CONT_NAME', 'continent', 'cont_name']:
        if col in gdf.columns:
            continent_col = col
            print(f"Found continent column: {continent_col}")
            break
    
    if continent_col is None:
        print("ERROR: Could not find continent column in shapefile")
        print(f"Available columns: {gdf.columns.tolist()}")
        print("\nPlease check which column contains continent information")
        # Print sample data to help debug
        if len(gdf) > 0:
            print("\nSample row:")
            print(gdf.iloc[0].to_dict())
        return
    
    # Show unique continent values
    print(f"Unique continents in data: {gdf[continent_col].unique()}")
    
    # Map continent names to Natural Earth continent names
    continent_mapping = {
        'americas': ['North America', 'South America'],
        'europe': ['Europe'],
        'asia': ['Asia'],
        'africa': ['Africa'],
        'oceania': ['Oceania'],
        'africa_oceania': ['Africa', 'Oceania']
    }
    
    if continent not in continent_mapping:
        print(f"Error: Unknown continent '{continent}'")
        print(f"Available: {list(continent_mapping.keys())}")
        return
    
    # Filter by continent
    continent_names = continent_mapping[continent]
    print(f"Filtering for continents: {continent_names}")
    
    continent_data = gdf[gdf[continent_col].isin(continent_names)]
    
    # Exclude specific countries if needed
    if continent == 'americas':
        print("Excluding Greenland...")
        continent_data = continent_data[continent_data['NAME'] != 'Greenland']
    
    print(f"Total countries/territories: {len(continent_data)}")
    
    if len(continent_data) == 0:
        print("ERROR: No data found for this continent")
        return
    
    # Filter out tiny territories by area if requested
    if min_area > 0:
        print(f"Filtering out territories smaller than {min_area} square degrees...")
        continent_data['area'] = continent_data.geometry.area
        
        if len(continent_data) > 0:
            print(f"Area range: {continent_data['area'].min():.6f} to {continent_data['area'].max():.2f}")
            continent_data = continent_data[continent_data['area'] >= min_area]
            print(f"Countries/territories after filtering: {len(continent_data)}")
        
        if len(continent_data) == 0:
            print(f"ERROR: No geometries remain after filtering with min_area={min_area}")
            return
    
    # Apply projection for more slender appearance
    if use_projection:
        print("Applying Mercator projection...")
        continent_data = continent_data.to_crs('EPSG:3857')
    
    # Get bounds for scaling
    bounds = continent_data.total_bounds
    print(f"Bounds: {bounds}")
    
    # === Create PNG ===
    print(f"Creating PNG: {output_png}")
    fig, ax = plt.subplots(1, 1, figsize=(12, 16), dpi=150)
    
    # Plot the geometries
    if show_borders:
        continent_data.plot(ax=ax, color=fill_color, edgecolor='white', linewidth=0.5)
    else:
        continent_data.plot(ax=ax, color=fill_color, edgecolor='none', linewidth=0)
    
    # Remove axes
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.axis('off')
    
    # Save PNG
    plt.tight_layout(pad=0)
    plt.savefig(output_png, bbox_inches='tight', pad_inches=0, facecolor='white')
    plt.close()
    
    print(f"PNG saved: {output_png}")
    
    # === Create SVG ===
    print(f"Creating SVG: {output_svg}")
    
    # Calculate dimensions
    width = 1200
    aspect_ratio = (bounds[3] - bounds[1]) / (bounds[2] - bounds[0])
    height = int(width * aspect_ratio)
    
    dwg = svgwrite.Drawing(output_svg, size=(width, height))
    
    # Add white background
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='white'))
    
    # Function to convert coordinates to pixels
    def coords_to_pixels(x, y):
        px = (x - bounds[0]) / (bounds[2] - bounds[0]) * width
        py = (bounds[3] - y) / (bounds[3] - bounds[1]) * height
        return px, py
    
    # Draw each geometry
    for geom in continent_data.geometry:
        if geom.geom_type == 'Polygon':
            points = [coords_to_pixels(x, y) for x, y in geom.exterior.coords]
            dwg.add(dwg.polygon(
                points=points,
                fill=fill_color,
                stroke='white' if show_borders else 'none',
                stroke_width=1 if show_borders else 0
            ))
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                points = [coords_to_pixels(x, y) for x, y in poly.exterior.coords]
                dwg.add(dwg.polygon(
                    points=points,
                    fill=fill_color,
                    stroke='white' if show_borders else 'none',
                    stroke_width=1 if show_borders else 0
                ))
    
    dwg.save()
    print(f"SVG saved: {output_svg}")
    
    print(f"\nDone! Files created:")
    print(f"  - {output_png}")
    print(f"  - {output_svg}")

# Example usage
if __name__ == '__main__':
    shapefile_path = 'ne_10m_admin_0_countries.shp'
    
    # Americas - Light Red (excluding Greenland)
    print("\n=== RENDERING AMERICAS ===")
    render_continent_from_shapefile(
        shapefile_path=shapefile_path,
        continent='americas',
        output_png='americas.png',
        output_svg='americas.svg',
        min_area=0.1,  # Keep most islands
        use_projection=True,
        fill_color='#FF9999',
        show_borders=False
    )
    
    # Europe - Blue
    print("\n=== RENDERING EUROPE ===")
    render_continent_from_shapefile(
        shapefile_path=shapefile_path,
        continent='europe',
        output_png='europe.png',
        output_svg='europe.svg',
        min_area=0.01,  # Keep small islands
        use_projection=True,
        fill_color='#99CCFF',
        show_borders=False
    )
    
    # Asia - Yellow
    print("\n=== RENDERING ASIA ===")
    render_continent_from_shapefile(
        shapefile_path=shapefile_path,
        continent='asia',
        output_png='asia.png',
        output_svg='asia.svg',
        min_area=0.1,
        use_projection=True,
        fill_color='#FFFF99',
        show_borders=False
    )
    
    # Africa + Oceania - Grey
    print("\n=== RENDERING AFRICA + OCEANIA ===")
    render_continent_from_shapefile(
        shapefile_path=shapefile_path,
        continent='africa_oceania',
        output_png='africa_oceania.png',
        output_svg='africa_oceania.svg',
        min_area=0.1,
        use_projection=True,
        fill_color='#CCCCCC',
        show_borders=False
    )
    
    print("\n=== ALL DONE ===")
    print("Generated 4 continents with precise boundaries!")