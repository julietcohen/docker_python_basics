import geopandas as gpd

gdf = gpd.read_file("test_polygons.gpkg")

length = len(gdf)

print(f"Length of GDF is {length}.")
