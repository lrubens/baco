#!/usr/bin/python
import math
import numpy as np
import os
import sys
import warnings
from collections import OrderedDict
import time
import subprocess


sys.path.append(".")
from baco.run import optimize  # noqa


def mha(X):

    x1 = X["par_factor"]

    rust_binary = "/home/rubensl/Documents/repos/comal/target/release/comal"
    dataset_name = "tensor4_mha"

    # cmd = rust_binary + " -d " + dataset_name + " --par_factor " + str(x1.astype(np.int32))
    cmd = [rust_binary, "-d", dataset_name, "--par_factor", str(x1.astype(np.int32))]

    print(cmd)
    print()

    start = time.time() 

    subprocess.run(cmd) 

    end = time.time()
    elapsed_time = end - start
    print("Time elapsed: ", elapsed_time)

    return {
        "compute_time": elapsed_time
    }


def main():
    parameters_file = "example_scenarios/synthetic/comal/comal.json"
    optimize(parameters_file, mha)
    print("End of known constraints")


if __name__ == "__main__":
    main()
