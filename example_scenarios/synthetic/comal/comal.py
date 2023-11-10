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
import toml
from pathlib import Path
home = str(Path.home())


def mha(X):

    par_factor = X["par_factor"]
    fiberlookup_latency = X["fiberlookup_latency"]
    fiberlookup_ii = X["fiberlookup_ii"]

    rust_binary = "/home/rubensl/Documents/repos/comal/target/release/comal"
    dataset_name = "tensor4_mha"

    with open(home + "/sam_config.toml", "r") as f:
        config = toml.load(f)
    
    config["sam_config"]["fiberlookup_latency"] = fiberlookup_latency
    config["sam_config"]["fiberlookup_ii"] = fiberlookup_ii

    with open(home + "/sam_config.toml", "w") as f:
        toml.dump(config, f)

    # cmd = rust_binary + " -d " + dataset_name + " --par_factor " + str(x1.astype(np.int32))
    cmd = [rust_binary, "-d", dataset_name, "--par_factor", str(par_factor.astype(np.int32))]

    print(cmd)
    print()

    start = time.time() 

    proc = subprocess.run(cmd, universal_newlines = True, stdout = subprocess.PIPE) 

    valid = True
    cycle_num = 0
    try:
        cycle_num = int(proc.stdout.split("\n")[2].split(": ")[1])
    except:
        valid = False
        print("Invalid config")

    end = time.time()
    # elapsed_time = end - start
    print("Time elapsed: ", cycle_num)

    # TODO: Add in unknown constraints to output
    return {
        "compute_time": cycle_num
    }


def main():
    parameters_file = "example_scenarios/synthetic/comal/comal.json"
    optimize(parameters_file, mha)
    print("End of known constraints")


if __name__ == "__main__":
    main()
