# docker_python_basics

Testing out how to work with Docker and python scripts to execute geospatial analyses. This repository is initial practice for executing the Permafrost Discovery Gateway visualization workflow with Docker and Kubernetes.

**Steps to build and run locally:**

1. clone repo & open Docker Desktop
2. navigate to repo in VScode
3. `docker build -t image_name` 
4. Run with persistent directory, replacing the path as needed: `docker run -v /Users/jcohen/Documents/docker/repositories/docker_python_basics/app:/app image_name`

If using parsl, ensure an environment is activated in the terminal that is build from the same `requirements.txt` file as the docker image. 
