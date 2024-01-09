# docker_python_basics

Testing out how to work with Docker and python scripts to execute geospatial analyses. This repository is initial practice for executing the Permafrost Discovery Gateway visualization workflow with Docker, Kubernetes, and parsl for parallelization.

**Steps to build image and run container on local machine:**

1. clone repository & open Docker Desktop, navigate to repository in VScode
2. edit paths in Dockerfile as needed, and ensure the parsl config does not have line for persistent directory, because that is only needed in the config if running on a remote sever
3. ensure an environment is activated in the terminal that is build from the same `requirements.txt` file as the docker image 
4. `docker build -t image_name` 
5. Run container with persistent directory for input and output data, updating the path as needed: `docker run -v /Users/jcohen/Documents/docker/repositories/docker_python_basics/app:/app image_name`

**Steps to build image from published reporitory package and run container on server:**
1. SSH into server in VScode, clone repo, navigate to repository
2. edit paths in Dockerfile as needed, and update string that represents the published repository package version of image in parsl script if pulling image from repository
- example:
```
htex_kube = config_parsl_cluster(max_blocks=5, image='ghcr.io/julietcohen/docker_python_basics:0.5', namespace='pdgrun')
```
3. add line to parsl config to specify the persistent volume name and mount filepath
- example:
```
persistent_volumes=[('pdgrun-dev-0','/home/jcohen/docker_python_basics/app-data')]
```
3. publish package to repository with new version number by running 3 commands:
```
docker build -t ghcr.io/julietcohen/docker_python_basics:0.3 .

echo $GITHUB_PAT | docker login ghcr.io -u julietcohen --password-stdin

docker push ghcr.io/julietcohen/docker_python_basics:0.3
```
4. ensure an environment is activated in the terminal that is build from the same `requirements.txt` file as the docker image 
5. run the python script for the parsl workflow: `python parsl_workflow.py`

**General Notes:**
- if run is successful, parsl processes should shut down cleanly. If not, you'll need to kill the processes manually
- after each run, if files were output, remove them from the persistent directory before next run