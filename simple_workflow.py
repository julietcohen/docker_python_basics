# test docker image and container by running a
# minimum version of the workflow

# use env: dkr-vw (has python 3.10.13)

from datetime import datetime
import json
import logging
import logging.handlers
import os

import pdgstaging
import pdgraster

import shutil

print("Removing old directories and files...")

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

lc = "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/data/test_polygons.gpkg"

config = {
  "deduplicate_clip_to_footprint": False,
  "deduplicate_method": None,
  "dir_output": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/", 
  "dir_input": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/data/", 
  "ext_input": ".gpkg",
  "dir_staged": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/staged/", 
  "dir_geotiff": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/geotiff/",  
  "dir_web_tiles": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/web_tiles/", 
  "filename_staging_summary": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/staging_summary.csv",
  "filename_rasterization_events": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/raster_events.csv",
  "filename_rasters_summary": "/Users/jcohen/Documents/docker/viz-workflow-practice/workflow/raster_summary.csv",
  "version": datetime.now().strftime("%B%d,%Y"),
  "simplify_tolerance": 0.1,
  "tms_id": "WGS1984Quad",
  "z_range": [
    0,
    9
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
      "nodata_val": None,
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