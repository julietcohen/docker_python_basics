# docker_python_basics

Testing out how to work with Docker and python scripts to execute geospatial analyses. This repository is initial practice for executing the Permafrost Discovery Gateway visualization workflow with Docker, Kubernetes, and parsl for parallelization.

This repository includes 3 scripts that vary from simplest to most complex:
  1. `simple_test.py` - easiest, a simple geopandas operation
  2. `simple_workflow.py` - more complex, a simple version of the visualization workflow
  3. `parsl_workflow.py` - most complex, integrates parallelization with parsl and kubernetes into the visualization workflow

All of these scripts can be run locally on a laptop with Docker Desktop open, _or_ on the Datateam server. Either way, you will have to mount a persistent volume because all scripts write output. The difference in _how_ you mount a persistent volume comes into play when you switch from the simple workflow to the parallel workflow. In the parallel workflow, the `parsl` config ingests the filepath for the persistent volume, instead of specifying it in the `docker run` command.

Before executing any of these scripts with docker, you should create a fresh environment and install all the requirements specified in the `requirements.txt` file. The same `requirements.txt` is used for all 3 scripts.

While any of the scripts in this repo can be run locally or on Datateam, my recommended steps are as follows:

1. Start by getting `simple_test.py` to run on your local computer with a docker container. Since we are writing an output file, even with this very simple script, we will need to mount a volume when we execute the `docker run` command. If we do not mount a volume, the output is lost into the ether with the container when it stops running.

2. Then get `simple_test.py` to run on the Datateam server with a "local" docker container
    - By "local", I mean executing the `docker build` command in the terminal, then the `docker run` command in the terminal, without pushing the image to the GitHub repo and then pointing to it. That comes later.
    - Mounting a volume on the server for the output is done in the same way as we do on our local laptop: we specify the filepath when we execute the `docker run` command! It's just a different filepath because now we are on a different machine.

3. Then get `simple_workflow.py` to run on Datateam, and mount the volume in the same way, with the `docker run` command. This script writes several directories and many more files!

4. Finally, run the `parsl_worfklow.py` on Datateam with a persistent volume specified within the `parsl` config, not in the `docker run` command.

See details for all these steps below:

## 1. For either `simple_test.py` or `simple_workflow.py`: Steps to build an image and run the container on a local machine

1. Clone repository & open Docker Desktop app on your laptop, then navigate to repository in VScode.
2. Edit filepaths in Dockerfile as needed.
3. Ensure an environment is activated in the terminal that is built from the same `requirements.txt` file as the docker image. This requires you to create a fresh environment, activate it, then run `pip install -r requirements.txt` in the command line. 
4. Run `docker build -t image_name .` in the command line.
5. Run the container and specify a persistent directory for input and output data, updating the path as needed: `docker run -v /Users/jcohen/Documents/docker/repositories/docker_python_basics/app:/app image_name`

## 2. For either `simple_test.py` or `simple_workflow.py`: Steps to build an image and run the container on Datateam server

1. SSH into server in VScode, clone the repository, and navigate to the repository.
2. Edit filepaths in Dockerfile as needed.
3. Ensure an environment is activated in the terminal that is built from the same `requirements.txt` file as the docker image 
4. `docker build -t image_name .` 
5. Run the container and specify a persistent directory for input and output data, updating the path as needed: `docker run -v /home/jcohen/docker_python_basics/app:/app image_name`

## 3. For ANY of the scripts: Steps to run a container from a published repository package (a built image) on server:

1. SSH into server in VScode, clone the repository, and navigate to the repository.

2. Make sure your Personal Access Token allows for publishing packages to the repo. Navigate to your token on GitHub, then scroll down to `write:packages` and check the box and save.

3. Edit filepaths in Dockerfile as needed.

4. If running `parsl` script, update the string that represents the published repository package version of image in `parsl_config.py`:
```
image='ghcr.io/julietcohen/docker_python_basics:0.9',
```

5. Add a line to parsl config to specify the persistent volume name and mount filepath. The first item in the list will need to be a persistent volume that is set up by the server admin. The second argument is the location that you want the volume to be mounted within your container.:
```
persistent_volumes=[('pdgrun-dev-0','/home/jcohen/docker_python_basics/app-data')]
```

6. Publish the package to the repository with new version number by running 3 commands one-by-one. Replace `$GITHUB_PAT` with your PAT:
```
docker build -t ghcr.io/julietcohen/docker_python_basics:0.9 .

echo $GITHUB_PAT | docker login ghcr.io -u julietcohen --password-stdin

docker push ghcr.io/julietcohen/docker_python_basics:0.9
```

7. Run `kubectl get pods` to see if any pods are left hanging from the last run. This could be the case if a past run failed to shut down the parsl workers. If there are any hanging, delete them all at once (for the specific namespace you're workin with) by running `kubectl delete pods --all -n {namespace}`.

8. Ensure an environment is activated in the terminal that is build from the same `requirements.txt` file as the docker image. 

9. Run the python script for the parsl workflow: `python parsl_workflow.py`

**General Notes:**
- If the run is successful, parsl processes should shut down cleanly. If not, you'll need to kill the processes manually.
  - You can check your processes in the command line with `ps -ef | grep {username}`
  - In the output, the column next to your username shows the 5-digit identifier for the proess. Run `kill -9 {identifier}` to kill one in particular.
- After each run, if files were output, remove them from the persistent directory before next run. 