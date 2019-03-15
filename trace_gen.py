import sys
import csv
import json
import math
import random
import argparse
from argparse import ArgumentParser
from factory import obj_factory, json_to_obj
from cls import Group
from constants.opt_consts import GROUP

def parse_args():
    parser = ArgumentParser(description = 'Process cmd args for placements')
    parser.add_argument('-f','--file-name', dest='file_name', required=True)
    parser.add_argument('-o','--out-file', dest='outfile', required=False)
    parser.add_argument('-i','--out-id', dest='outid', required=False)
    args = parser.parse_args()
    return args

def process_input(file_name):
    datacenters = []
    groups = []
    with open(file_name, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    for grp in data.get("input_groups"):
        grp_obj = json_to_obj(grp, GROUP)
        groups.append(grp_obj)
    return groups

def main(args, groups):
    out_file = args.outfile
    if out_file is None:
        out_file = './tests/traces/trace_%s/trace.csv'%args.outid
    num_dcs = len(groups[0].client_dist)
    client_files = ['./tests/traces/trace_%s/dc_%s.csv'%(args.outid, i) \
                        for i in range(num_dcs)]
    start_key_id = 0
    trace = []
    cl_trace = {}
    for i, grp in enumerate(groups):
        keys = [j for j in range(start_key_id, start_key_id+int(grp.num_objects))]
        reads = math.ceil(grp.read_ratio*grp.arrival_rate*grp.duration)
        writes = math.ceil(grp.write_ratio*grp.arrival_rate*grp.duration)
        reqs = ['r' for _ in range(reads)]+['w' for _ in range(writes)]
        random.shuffle(reqs)
        itr = math.ceil(len(reqs)/int(grp.num_objects))
        keys = keys*itr
        reqs = [list(_req)+[i] for _req in zip(keys, reqs)]
        # Divide into per client trace
        random.shuffle(reqs)
        start_idx = 0
        for client, dist in enumerate(grp.client_dist):
            length = math.ceil(len(reqs)*dist)
            cl_reqs = reqs[start_idx:start_idx+length]
            cl_reqs = [x+[client] for x in cl_reqs]
            random.shuffle(cl_reqs)
            cl_trace.setdefault(client, []).extend(cl_reqs)
            start_idx += length
            print(client, len(cl_reqs), cl_reqs[0:2])
        start_key_id += int(grp.num_objects)
        #print(cl_trace)
    # Write to files
    for c in cl_trace:
        trace += cl_trace[c]
    print(trace[0:10], len(trace))
    with open(out_file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(trace)
    for k, val in cl_trace.items():
        with open(client_files[int(k)], "w") as f:
            writer = csv.writer(f)
            writer.writerows(val)

if __name__ == "__main__":
    args = parse_args()
    groups = process_input(args.file_name)
    main(args, groups)
