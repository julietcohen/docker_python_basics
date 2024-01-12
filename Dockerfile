# FROM python:3.10

# # the following line may not work bc have not built image from docker file in this repo yet?
# LABEL org.opencontainers.image.source https://github.com/julietcohen/docker_python_basics

# # use the following line if working on local computer:
# # WORKDIR /Users/jcohen/Documents/docker/repositories/docker_python_basics
# # use the following line if working from Datateam server:
# WORKDIR /home/jcohen/docker_python_basics/app-data

# # copy files from the dir that contains the Dockerfile to the destination relative to the WORKDIR
# # example: copy parsl_workflow.py from the directory of the Dockerfile to /home/jcohen/docker_python_basics/app-data
# COPY parsl_workflow.py .
# COPY parsl_config.py .
# COPY requirements.txt .
# # for run with LC data on local computer:
# #ADD /Users/jcohen/Documents/PDG/lake_change_GD_2022-11-04_cleaned/cleaned_files/data_products_32635-32640 ./data_products_32635-32640
# # ADD ./LC_data .
# # for run with LC data from /var/data/submission/ on Datateam:
# # COPY /var/data/submission/pdg/nitze_lake_change/data_2022-11-04/lake_change_GD_cleaned/cleaned_files/data_products_32635-32640 .
# # for run with sample of LC data in home dir on Datateam:
# # ADD data/test_polygons.gpkg .

# RUN pip install -r requirements.txt

# # maybe we don't want to run a command bc we need to use the terminal to
# # do it now that we are using parsl and k8s
# # CMD [ "python", "./parsl_workflow.py" ]

# -----------------------------------------------------

# for simple_workflow.py:

# base image
FROM python:3.9

#WORKDIR /Users/jcohen/Documents/docker/viz-workflow-practice/workflow
WORKDIR /home/jcohen/docker_python_basics

# python script to run
ADD simple_workflow.py .
# add the input data
COPY data/test_polygons.gpkg .
#COPY /data/test_polygons.gpkg /Users/jcohen/Documents/docker/viz-workflow-practice/workflow
COPY requirements.txt .

# packages to install
RUN pip install -r requirements.txt

CMD [ "python", "./simple_workflow.py" ]

# after this command completes, the container shuts down
# if there is a time-consuming process in the script, like a loop 
# so in order to use interactive session you need a time-consuming process
# install vi in the container (in the command line) for interactivity
# for example, ubuntu base image (which is huge) would already have vi

