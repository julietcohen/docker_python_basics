# -----------------------------------------------------

# for parsl_workflow.py:

# base image could be python 9 or 10
FROM python:3.10

# the following line may not work bc have not built image from docker file in this repo yet?
LABEL org.opencontainers.image.source https://github.com/julietcohen/docker_python_basics

# WORKDIR /Users/jcohen/Documents/docker/repositories/docker_python_basics
# use the following line if working from Datateam server:
WORKDIR /home/jcohen/docker_python_basics

COPY parsl_workflow.py .
COPY parsl_config.py .
COPY requirements.txt .
# for run with LC data:
COPY /var/data/submission/pdg/nitze_lake_change/data_2022-11-04/lake_change_GD_cleaned/cleaned_files/data_products_32635-32640 .

RUN pip install -r requirements.txt

# maybe we don't want to run a command bc we need to use the terminal to
# do it now that we are using parsl and k8s
# CMD [ "python", "./parsl_workflow.py" ]

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

