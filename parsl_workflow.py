# test docker image and orchestrate containers
# with kubernetes by running a minimum version of 
# the workflow with a kubernetes parsl config

# documentation for parsl config: https://parsl.readthedocs.io/en/stable/userguide/configuring.html#kubernetes-clusters


from datetime import datetime
import json
import logging
import logging.handlers
import os

import pdgstaging
import pdgraster

import parsl
from parsl import python_app
from parsl.config import Config
from parsl.executors import HighThroughputExecutor
from parsl.providers import KubernetesProvider
from parsl.addresses import address_by_route
from kubernetes import client, config

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

# define variables for config
max_blocks=2, 
min_blocks=1, 
init_blocks=2, 
max_workers=1, 
cores_per_worker=1, 
image='ghcr.io/mbjones/k8sparsl:0.3', # change to my image name  
namespace='pdgrun'

htex_kube = Config(
    executors=[
        HighThroughputExecutor(
            label='kube-htex',
            cores_per_worker=cores_per_worker,
            max_workers=max_workers,
            worker_logdir_root='/',
            # Address for the pod worker to connect back
            address=address_by_route(),
            #address='192.168.0.103',
            #address_probe_timeout=3600,
            worker_debug=True,
            provider=KubernetesProvider(

                # Namespace in K8S to use for the run
                namespace=namespace,

                # Docker image url to use for pods
                image=image,

                # Command to be run upon pod start, such as:
                # 'module load Anaconda; source activate parsl_env'.
                # or 'pip install parsl'
                #worker_init='echo "Worker started..."; lf=`find . -name \'manager.log\'` tail -n+1 -f ${lf}',
                worker_init='echo "Worker started..."',

                # The secret key to download the image
                #secret="YOUR_KUBE_SECRET",

                # Should follow the Kubernetes naming rules
                pod_name='parsl-worker',

                nodes_per_block=1,
                init_blocks=init_blocks,
                min_blocks=min_blocks,
                # Maximum number of pods to scale up
                max_blocks=max_blocks,
                # persistent_volumes (list[(str, str)]) – List of tuples 
                # describing persistent volumes to be mounted in the pod. 
                # The tuples consist of (PVC Name, Mount Directory).
                # persistent_volumes=[('mypvc','/var/data')]
            ),
        ),
    ]
)
parsl.load(htex_kube)


lc = "test_polygons.gpkg"
# data input sample, with ~370 GB and 6 files: 
# /var/data/submission/pdg/nitze_lake_change/data_2022-11-04/lake_change_GD_cleaned/cleaned_files/data_products_32635-32640
# data input sample with ~750 MB and 10 files:
# /var/data/submission/pdg/nitze_lake_change/data_2022-11-04/lake_change_GD_cleaned/cleaned_files/data_products_32651-32660/


def run_pdg_workflow(
    workflow_config,
    batch_size = 300
):
    """
    Run the main PDG workflow for the following steps:
    1. staging
    2. raster highest
    3. raster lower
    4. web tiling

    Parameters
    ----------
    workflow_config : dict
        Configuration for the PDG staging workflow, tailored to rasterization and 
        web tiling steps only.
    batch_size: int
        How many staged files, geotiffs, or web tiles should be included in a single creation
        task? (each task is run in parallel) Default: 300
    """

    start_time = datetime.now()

    logging.info("Staging initiated.")

    stager = pdgstaging.TileStager(workflow_config)
    #tile_manager = rasterizer.tiles
    tile_manager = stager.tiles
    config_manager = stager.config

    input_paths = stager.tiles.get_filenames_from_dir('input')
    input_batches = make_batch(input_paths, batch_size)

    # Stage all the input files (each batch in parallel)
    app_futures = []
    for i, batch in enumerate(input_batches):
        app_future = stage(batch, workflow_config)
        app_futures.append(app_future)
        logging.info(f'Started job for batch {i} of {len(input_batches)}')

    # Don't continue to next step until all files have been staged
    [a.result() for a in app_futures]

    logging.info("Staging complete.")

    # ----------------------------------------------------------------

    # Create highest geotiffs 
    rasterizer = pdgraster.RasterTiler(workflow_config)

    # Process staged files in batches
    logging.info(f'Collecting staged file paths to process...')
    staged_paths = tile_manager.get_filenames_from_dir('staged')
    logging.info(f'Found {len(staged_paths)} staged files to process.')
    staged_batches = make_batch(staged_paths, batch_size)
    logging.info(f'Processing staged files in {len(staged_batches)} batches.')

    app_futures = []
    for i, batch in enumerate(staged_batches):
        app_future = create_highest_geotiffs(batch, workflow_config)
        app_futures.append(app_future)
        logging.info(f'Started job for batch {i} of {len(staged_batches)}')

    # Don't move on to next step until all geotiffs have been created
    [a.result() for a in app_futures]

    logging.info("Rasterization highest complete. Rasterizing lower z-levels.")

    # ----------------------------------------------------------------

    # Rasterize composite geotiffs
    min_z = config_manager.get_min_z()
    max_z = config_manager.get_max_z()
    parent_zs = range(max_z - 1, min_z - 1, -1)

    # Can't start lower z-level until higher z-level is complete.
    for z in parent_zs:

        # Determine which tiles we need to make for the next z-level based on the
        # path names of the geotiffs just created
        logging.info(f'Collecting highest geotiff paths to process...')
        child_paths = tile_manager.get_filenames_from_dir('geotiff', z = z + 1)
        logging.info(f'Found {len(child_paths)} highest geotiffs to process.')
        # create empty set for the following loop
        parent_tiles = set()
        for child_path in child_paths:
            parent_tile = tile_manager.get_parent_tile(child_path)
            parent_tiles.add(parent_tile)
        # convert the set into a list
        parent_tiles = list(parent_tiles)

        # Break all parent tiles at level z into batches
        parent_tile_batches = make_batch(parent_tiles, batch_size)
        logging.info(f'Processing highest geotiffs in {len(parent_tile_batches)} batches.')

        # Make the next level of parent tiles
        app_futures = []
        for parent_tile_batch in parent_tile_batches:
            app_future = create_composite_geotiffs(
                parent_tile_batch, workflow_config)
            app_futures.append(app_future)

        # Don't start the next z-level, and don't move to web tiling, until the
        # current z-level is complete
        [a.result() for a in app_futures]

    logging.info("Composite rasterization complete. Creating web tiles.")

    # ----------------------------------------------------------------

    # Process web tiles in batches
    logging.info(f'Collecting file paths of geotiffs to process...')
    geotiff_paths = tile_manager.get_filenames_from_dir('geotiff')
    logging.info(f'Found {len(geotiff_paths)} geotiffs to process.')
    geotiff_batches = make_batch(geotiff_paths, batch_size)
    logging.info(f'Processing geotiffs in {len(geotiff_batches)} batches.')

    app_futures = []
    for i, batch in enumerate(geotiff_batches):
        app_future = create_web_tiles(batch, workflow_config)
        app_futures.append(app_future)
        logging.info(f'Started job for batch {i} of {len(geotiff_batches)}')

    # Don't record end time until all web tiles have been created
    [a.result() for a in app_futures]

    end_time = datetime.now()
    logging.info(f'⏰ Total time to create all z-level geotiffs and web tiles: '
                 f'{end_time - start_time}')

# ----------------------------------------------------------------

# Define the parsl functions used in the workflow:

@python_app
def stage(paths, config):
    """
    Stage a file
    """
    from datetime import datetime
    import json
    import logging
    import logging.handlers
    import os
    import pdgstaging

    # configure logger:
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

    stager = pdgstaging.TileStager(config = config, check_footprints = False)
    for path in paths:
        stager.stage(path)
    return True

# Create highest z-level geotiffs from staged files
@python_app
def create_highest_geotiffs(staged_paths, config):
    """
    Create a batch of geotiffs from staged files
    """
    from datetime import datetime
    import json
    import logging
    import logging.handlers
    import os
    import pdgraster

    # configure logger:
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

    # rasterize the vectors, highest z-level only
    rasterizer = pdgraster.RasterTiler(config)
    return rasterizer.rasterize_vectors(
        staged_paths, make_parents = False)
    # no need to update ranges because manually set val_range in config

# ----------------------------------------------------------------

# Create composite geotiffs from highest z-level geotiffs 
@python_app
def create_composite_geotiffs(tiles, config):
    """
    Create a batch of composite geotiffs from highest geotiffs
    """
    from datetime import datetime
    import json
    import logging
    import logging.handlers
    import os
    import pdgraster

    # configure logger:
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

    rasterizer = pdgraster.RasterTiler(config)
    return rasterizer.parent_geotiffs_from_children(
        tiles, recursive = False)

# ----------------------------------------------------------------

# Create a batch of webtiles from geotiffs
@python_app
def create_web_tiles(geotiff_paths, config):
    """
    Create a batch of webtiles from geotiffs
    """

    from datetime import datetime
    import json
    import logging
    import logging.handlers
    import os
    import pdgraster

    # configure logger:
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

    rasterizer = pdgraster.RasterTiler(config)
    return rasterizer.webtiles_from_geotiffs(
        geotiff_paths, update_ranges = False)
        # no need to update ranges because the range is [1,4] for
        # all z-levels, and is defined in the config


def make_batch(items, batch_size):
    """
    Create batches of a given size from a list of items.
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

# ----------------------------------------------------------------

# run the workflow
config_file = '/Users/jcohen/Documents/docker/repositories/docker_python_basics/config.json'
logging.info(f'🗂 Workflow configuration loaded from {config_file}')
print("Loaded config. Running workflow.")
logging.info(f'Starting PDG workflow: staging, rasterization, and web tiling')
run_pdg_workflow(config_file)
# Shutdown and clear the parsl executor
htex_local.executors[0].shutdown()
parsl.clear()

print("Script complete.")