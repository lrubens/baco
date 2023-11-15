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

    fiberlookup_starting = int(X["fiberlookup_starting"])
    fiberlookup_stop_latency = int(X["fiberlookup_stop_latency"])
    fiberlookup_initial = int(X["fiberlookup_initial"])
    fiberlookup_latency = int(X["fiberlookup_latency"])
    fiberlookup_ii = int(X["fiberlookup_ii"])
    fiberlookup_factor = float(X["fiberlookup_factor"])

    print(fiberlookup_ii)
    print(fiberlookup_initial)
    print(fiberlookup_latency)

    rust_binary = "/home/rubensl/Documents/repos/comal/target/debug/deps/comal-7ae5c3f20dbd5329"

    with open(home + "/sam_config.toml", "r") as f:
        config = toml.load(f)

    config["sam_config"]["fiberlookup_latency"] = fiberlookup_latency
    config["sam_config"]["fiberlookup_ii"] = fiberlookup_ii
    config["sam_config"]["fiberlookup_initial"] = fiberlookup_initial
    config["sam_config"]["fiberlookup_starting"] = fiberlookup_starting
    config["sam_config"]["fiberlookup_stop_latency"] = fiberlookup_stop_latency
    config["sam_config"]["fiberlookup_factor"] = fiberlookup_factor

    with open(home + "/sam_config.toml", "w") as f:
        toml.dump(config, f)

    # cmd = rust_binary + " -d " + dataset_name + " --par_factor " + str(x1.astype(np.int32))
    cmd = [rust_binary, "--nocapture", "rd_scanner",
           "--test-threads=1"]

    print(cmd)
    print()

    # start = time.time()

    proc = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE)

    diff_lst = []
    for item in proc.stdout.split("\n"):
        if item.startswith("Diff"):
            diff_lst.append(abs(int(item.split("Diff: ")[1])))

    print(diff_lst)
    

    # TODO: Add in unknown constraints to output
    return {
        "diff1": diff_lst[0],
        "diff2": diff_lst[1],
        "diff3": diff_lst[2],
        "diff4": diff_lst[3],
        "diff5": diff_lst[4],
        "diff6": diff_lst[5],
        "diff7": diff_lst[6],
        "diff8": diff_lst[7],
    }


def main():
    parameters_file = "example_scenarios/synthetic/auto_cal/autocal.json"
    optimize(parameters_file, mha)
    print("End of known constraints")


if __name__ == "__main__":
    main()
