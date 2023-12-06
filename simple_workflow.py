# test docker image and container by running a
# minimum version of the workflow

from datetime import datetime
import json
import logging
import logging.handlers
import os

import pdgstaging
import pdgraster

import shutil


print("Removing old directories and files...")
old_filepaths = ["/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/staging_summary.csv",
                "/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/raster_summary.csv",
                "/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/raster_events.csv",
                "/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/config__updated.json",
                "/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/log.log"]
for old_file in old_filepaths:
  if os.path.exists(old_file):
      os.remove(old_file)

# remove dirs from past run
old_dirs = ["/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/staged",
            "/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/geotiff",
            "/Users/jcohen/Documents/docker/repositories/docker_python_basics/app/web_tiles"]
for old_dir in old_dirs:
  if os.path.exists(old_dir) and os.path.isdir(old_dir):
      shutil.rmtree(old_dir)


# configure logger
logger = logging.getLogger("logger")
# Remove any existing handlers from the logger
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
# prevent logging statements from being printed to terminal
logger.propagate = False
# set up new handler
handler = logging.FileHandler("/tmp/log.log")
formatter = logging.Formatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

lc = "test_polygons.gpkg"

config = {
  "deduplicate_clip_to_footprint": False,
  "deduplicate_method": None,
  "dir_output": "/app", 
  "dir_input": ".", 
  "ext_input": ".gpkg",
  "dir_staged": "/app/staged/", 
  "dir_geotiff": "/app/geotiff/",  
  "dir_web_tiles": "/app/web_tiles/", 
  "filename_staging_summary": "/app/staging_summary.csv",
  "filename_rasterization_events": "/app/raster_events.csv",
  "filename_rasters_summary": "/app/raster_summary.csv",
  "version": datetime.now().strftime("%B%d,%Y"),
  "simplify_tolerance": 0.1,
  "tms_id": "WGS1984Quad",
  "z_range": [
    0,
    7
  ],
  "geometricError": 57,
  "z_coord": 0,
  "statistics": [
    {
      "name": "change_rate", 
      "weight_by": "area",
      "property": "ChangeRateNet_myr-1", 
      "aggregation_method": "min", 
      "resampling_method": "mode",  
      "val_range": [
        -2,
        2
      ],
      "palette": ["#ff0000", # red
                  "#FF8C00", # DarkOrange
                  "#FFA07A", # LightSalmon
                  "#FFFF00", # yellow
                  "#66CDAA", # MediumAquaMarine
                  "#AFEEEE", # PaleTurquoise,
                  "#0000ff"], # blue
      "nodata_val": 0,
      "nodata_color": "#ffffff00" # fully transparent white
    },
  ],
}

print("Staging...")

stager = pdgstaging.TileStager(config = config, check_footprints = False)
# generate the staged files
stager.stage(lc)

print("Staging complete. Rasterizing...")

# for initial testing, only rasterize the highest z-level:
# staged_paths = stager.tiles.get_filenames_from_dir(base_dir = "staged")
# rasterizer = pdgraster.RasterTiler(config)
# rasterizer.rasterize_vectors(staged_paths, make_parents = False)

# or rasterize all z-levels and web tiles:
rasterizer = pdgraster.RasterTiler(config)
rasterizer.rasterize_all()

print("Script complete.")