import geopandas as gpd

gdf = gpd.read_file("test_polygons.gpkg")

# save first row as a new gdf
subset_gdf = gpd.GeoDataFrame(gdf.iloc[[0]], geometry='geometry')
length = len(subset_gdf)
print(f"Length of new GDF is {length}.")
subset_gdf.to_file('/app/subset.gpkg', driver='GPKG')
