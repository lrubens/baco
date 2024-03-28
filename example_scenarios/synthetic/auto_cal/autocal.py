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
import argparse


sys.path.append(".")
from baco.run import optimize  # noqa
home = str(Path.home())
best_diff = 1000000.0

config_options = {
    "rust_binary": "",
    "tmp_config_path": "",
}


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
    rust_binary = config_options["rust_binary"]
    node_config_path = config_options["tmp_config_path"]

    with open(home + node_config_path, "r") as f:
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

    with open(home + node_config_path, "w") as f:
        toml.dump(config, f)

    cmd = [rust_binary, "--nocapture", "rd_scanner"]

    proc = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE)

    actual_cycles = [27, 54, 93, 698, 36, 30, 93, 422, 223, 224]
    
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
    

    return {
        "diff1": avg_diff,
    }


def main():

    parser = argparse.ArgumentParser(prog="Automated calibration")
    parser.add_argument('-b', 'rust_binary')
    parser.add_argument('-f', 'config_path')
    args = parser.parse_args()
    config_options["rust_binary"] = args.rust_binary
    config_options["tmp_config_path"] = args.tmp_config_path

    parameters_file = "example_scenarios/synthetic/auto_cal/autocal.json"
    optimize(parameters_file, autocal)
    print("End of known constraints")


if __name__ == "__main__":
    main()
