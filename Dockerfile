# -----------------------------------------------------

# for simple_workflow.py:

# base image
FROM python:3.9

WORKDIR /Users/jcohen/Documents/docker/repositories/docker_python_basics

# python script to run
ADD simple_workflow.py .

# data to process
COPY data/test_polygons.gpkg .

# packages to install
# the build will fail if these don't work
RUN pip install git+https://github.com/PermafrostDiscoveryGateway/viz-staging.git
RUN pip install git+https://github.com/PermafrostDiscoveryGateway/viz-raster.git
RUN pip install pydantic==1.10.9
# can remove the pydantic requirement when merge the existing PR that has this change for viz-raster
# so that will already satisfy this requirement 

CMD [ "python", "./simple_workflow.py" ]

# -----------------------------------------------------

# # for simple_test.py:

# # base image
# FROM python:3.9

# WORKDIR /Users/jcohen/Documents/docker/viz-workflow-practice/workflow

# # python script to run
# ADD simple_test.py .

# # add the input data
# COPY data/test_polygons.gpkg .
# #COPY /data/test_polygons.gpkg /Users/jcohen/Documents/docker/viz-workflow-practice/workflow

# # packages to install
# RUN pip install geopandas

# CMD [ "python", "./simple_test.py" ]
# # after this command completes, the container shuts down
# # if there is a time-consuming process in the script, like a loop 
# # so in order to use interactive session you need a time-consuming process
# # install vi in the container (in the command line) for interactivity
# # for example, ubuntu base image (which is huge) would already have vi

