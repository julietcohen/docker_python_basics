import geopandas as gpd

#gdf = gpd.read_file("/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/data/test_polygons.gpkg")
#gdf = gpd.read_file("data/test_polygons.gpkg")
gdf = gpd.read_file("test_polygons.gpkg")

length = len(gdf)

print(f"Length of GDF is {length}.")
