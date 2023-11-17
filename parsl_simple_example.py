# Example script for executing parsl apps on kubernetes

import math
import datetime
import os.path
import time

import parsl
from parsl import python_app
from parsl_config import config_parsl_cluster

def main():
    '''Main program to execute all stats.'''

    parsl.set_stream_logger()
    htex_kube = config_parsl_cluster(max_blocks=5, image='ghcr.io/mbjones/k8sparsl:0.3', namespace='pdgrun')
    parsl.load(htex_kube)

    size = 5
    stat_results = []
    for x in range(size):
        for y in range(size):
            current_time = datetime.datetime.now()
            print(f'Schedule job at {current_time} for {x} and {y}')
            stat_results.append(calc_product_long(x, y))
    stats = [r.result() for r in stat_results]
    print("*********************************************************", 
          sum(stats),
          "*********************************************************"
         )
    #htex_kube.executors[0].shutdown()

@python_app
def calc_product_long(x, y):
    '''Fake computation to simulate one that takes a long time'''
    import datetime
    import time
    current_time = datetime.datetime.now()
    print(f'Starting job at {current_time} for {x} and {y}')
    prod = x*y
    time.sleep(5)
    return(prod)


if __name__ == "__main__":
    main()