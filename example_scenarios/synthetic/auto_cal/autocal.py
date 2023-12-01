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
best_diff = 1000000.0


def autocal(X):

    fiberlookup_starting = int(X["fiberlookup_starting"])
    fiberlookup_stop_latency = int(X["fiberlookup_stop_latency"])
    fiberlookup_initial = int(X["fiberlookup_initial"])
    fiberlookup_latency = int(X["fiberlookup_latency"])
    fiberlookup_ii = int(X["fiberlookup_ii"])
    incr_type = int(X["incr_type"])
    fiberlookup_numerator_factor = int(X["fiberlookup_numerator_factor"])
    fiberlookup_denominator_factor = int(X["fiberlookup_denominator_factor"])
    fiberlookup_miss_latency = int(X["fiberlookup_miss_latency"])

    # TODO: Change to user input maybe
    rust_binary = "/home/rubensl/Documents/repos/comal/target/release/deps/comal-c5d2583e53b91909"

    with open(home + "/sam_config.toml", "r") as f:
        config = toml.load(f)

    config["sam_config"]["fiberlookup_latency"] = fiberlookup_latency
    config["sam_config"]["fiberlookup_ii"] = fiberlookup_ii
    config["sam_config"]["fiberlookup_initial"] = fiberlookup_initial
    config["sam_config"]["fiberlookup_starting"] = fiberlookup_starting
    config["sam_config"]["fiberlookup_stop_latency"] = fiberlookup_stop_latency
    config["sam_config"]["fiberlookup_numerator_factor"] = fiberlookup_numerator_factor
    config["sam_config"]["fiberlookup_denominator_factor"] = fiberlookup_denominator_factor
    config["sam_config"]["fiberlookup_miss_latency"] = fiberlookup_miss_latency
    config["sam_config"]["incr_type"] = incr_type

    with open(home + "/sam_config.toml", "w") as f:
        toml.dump(config, f)

    # cmd = rust_binary + " -d " + dataset_name + " --par_factor " + str(x1.astype(np.int32))
    cmd = [rust_binary, "--nocapture", "rd_scanner",
           "--test-threads=1"]

    proc = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE)

    diff_lst = []

    # TODO: Hacky way of getting diffs, fix
    for line in proc.stdout.split("\n"):
        if not line.startswith("test templates"):
            continue
        item = line.split("... ")[1]
        diff_lst.append(abs(int(item.split("Diff: ")[1])))

    avg_diff = 0.0
    for i, diff in enumerate(diff_lst):
        avg_diff += float(diff)
    avg_diff /= len(diff_lst)
    print("Avg diff: ", avg_diff)

    global best_diff
    if avg_diff < best_diff:
        best_diff = avg_diff
    print("Best diff: ", best_diff)
    

    # TODO: Maybe add in unknown constraints to output
    return {
        "diff1": avg_diff,
        # "diff1": float(diff_lst[0]),
        # "diff2": float(diff_lst[1]),
        # "diff3": float(diff_lst[2]),
        # "diff4": float(diff_lst[3]),
        # "diff5": float(diff_lst[4]),
        # "diff6": float(diff_lst[5]),
        # "diff7": float(diff_lst[6]),
        # "diff8": float(diff_lst[7]),
        # "diff9": float(diff_lst[8]),
        # "diff10": float(diff_lst[9]),
    }


def main():
    parameters_file = "example_scenarios/synthetic/auto_cal/autocal.json"
    optimize(parameters_file, autocal)
    print("End of known constraints")


if __name__ == "__main__":
    main()
