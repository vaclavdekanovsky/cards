import geopandas as gpd
import pandas as pd
import os

# To prevent long rows from being truncated in the output
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

try:
    # Define the directory and filename
    input_dir = r"C:\Vasa\Cartoon\Travel Game\in\continent_maps"
    shapefile_name = "World_Continents.shp"
    shapefile_path = os.path.join(input_dir, shapefile_name)

    print(f"--- Reading Shapefile: {shapefile_path} ---")
    data = gpd.read_file(shapefile_path)

    print("--- Shapefile Details ---")

    # 1. Print CRS
    print("\n[Coordinate Reference System (CRS)]")
    print(data.crs)

    # 2. Print Bounding Box
    print("\n[Total Bounding Box (minx, miny, maxx, maxy)]")
    print(data.total_bounds)

    # 3. Print Columns
    print("\n[Columns]")
    print(data.columns)

    # 4. Print Geometry Types
    print("\n[Geometry Types Present]")
    print(data.geom_type.unique())

    # 5. Print Unique Values in likely columns
    print("\n--- Column Values ---")
    potential_cols = ['CONTINENT', 'NAME', 'continent', 'name', 'REGION']
    found_col = False
    for col in potential_cols:
        if col in data.columns:
            print(f"\n[Unique values in '{col}' column]")
            print(data[col].unique())
            found_col = True

    if not found_col:
        print("\nCould not find a likely continent name column.")

    # 6. Print Head
    print("\n--- Data Sample (First 5 Rows) ---")
    print(data.head())
    print("-" * 20)


except Exception as e:
    print(f"\nAn error occurred: {e}")
