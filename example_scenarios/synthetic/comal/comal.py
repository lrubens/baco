#!/usr/bin/python
from pathlib import Path
import toml
import math
import numpy as np
import os
import sys
import warnings
from collections import OrderedDict
import time
import subprocess
import json


sys.path.append(".")
from baco.run import optimize  # noqa
home = str(Path.home())


def mha(X):

    par_factor = X["par_factor"]
    fiberlookup_latency = int(X["fiberlookup_latency"])
    fiberlookup_ii = int(X["fiberlookup_ii"])

    print(fiberlookup_ii)
    print(fiberlookup_latency)

    # rust_binary = "/home/rubensl/Documents/repos/comal/target/release/comal"
    rust_binary = "/home/rubensl/comal/target/release/comal"
    dataset_name = "tensor4_mha256"

    with open(home + "/sam_config.toml", "r") as f:
        config = toml.load(f)

    config["sam_config"]["fiberlookup_latency"] = fiberlookup_latency
    config["sam_config"]["fiberlookup_ii"] = fiberlookup_ii

    with open(home + "/sam_config.toml", "w") as f:
        toml.dump(config, f)

    # cmd = rust_binary + " -d " + dataset_name + " --par_factor " + str(x1.astype(np.int32))
    cmd = [rust_binary, "-d", dataset_name,
           "--par_factor", str(par_factor.astype(np.int32))]

    print(cmd)
    print()

    # start = time.time()

    proc = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE)

    valid = True
    cycle_num = 0
    primitive_count = ''
    # print(proc.stdout)
    try:
        cycle_num = int(proc.stdout.split("\n")[3].split(": ")[1])
        primitive_count = proc.stdout.split("\n")[0].split("Node count: ")[1]
    except:
        valid = False
        print("Invalid config")

    counts = json.loads(primitive_count)
    print(primitive_count)

    # end = time.time()
    # elapsed_time = end - start
    print("Time elapsed: ", cycle_num)

    # exit(0)
    fiberlookup_count = counts["CompressedCrdRdScan"]
    fiberwrite_count = counts["CompressedWrScan"] + counts["ValsWrScan"]
    intersect_count = counts["Intersect"]
    repeat_count = counts["Repeat"]
    reduce_count = counts["Reduce"] + counts["Spacc1"] + counts["MaxReduce"]
    alu_count = counts["PCU"]
    repsiggen_count = counts["RepeatSigGen"]
    array_count = counts["Array"]

    # TODO: Add in unknown constraints to output
    return {
        "compute_time": cycle_num,
        "fiberlookup_count": fiberlookup_count,
        "fiberwrite_count": fiberwrite_count,
        "intersect_count": intersect_count,
        "repeat_count": repeat_count,
        "reduce_count": reduce_count,
        "alu_count": alu_count,
        "repsiggen_count": repsiggen_count,
        "array_count": array_count
    }


def main():
    parameters_file = "example_scenarios/synthetic/comal/comal.json"
    optimize(parameters_file, mha)
    print("End of known constraints")


if __name__ == "__main__":
    main()
