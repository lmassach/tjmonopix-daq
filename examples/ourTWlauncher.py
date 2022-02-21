#!/usr/bin/env python2
"""Script to launch ourTW in batch."""
import os
import time
from subprocess import call, Popen
import argparse
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
DAQ_SCRIPT = os.path.join(SCRIPT_DIR, "ourTW.py")
ANA_SCRIPT = os.path.join(SCRIPT_DIR, "ourTWanalysis.py")


def convert_option_list(l, dtype=int):
    """Converts l to a numpy array.
    If l has two items, returns the range between the two items (both included).

    If l has one item, i.e. l = [a], the array is [a].
    If l has two item, i.e. l = [a, b], the array is [a, a+1, ..., b].
    If l has more than two items, the array has the same items as l.
    """
    if len(l) == 1:
        l = np.array([l[0]], dtype=dtype)
    elif len(l) == 2:
        l = np.arange(l[0], l[1] + 1, dtype=dtype)
    else:
        l = np.array(l, dtype=dtype)
    return l


def get_latest_output_file(path="output_data", suffix="_scan.h5"):
    """Returns the most recent file in path that ends in suffix."""
    latest_fp = None
    latest_mtime = 0
    for fn in os.listdir(path):
        if fn.endswith(suffix):
            fp = os.path.join(path, fn)
            mtime = os.path.getmtime(fp)
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_fp = fp
    return latest_fp, latest_mtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-c", "--cols", required=True, nargs="+", type=int,
                        help="The column range or value.")
    parser.add_argument("-r", "--rows", required=True, nargs="+", type=int,
                        help="The row range or value.")
    parser.add_argument("-i", "--injs", required=True, nargs="+", type=int,
                        help="The injection range or value.")
    parser.add_argument("-t", "--thrs", required=True, nargs="+", type=int,
                        help="The threshold range or value.")
    parser.add_argument("--n-cols", type=int, default=5,
                        help="Number of columns to scan at a time.")
    parser.add_argument("--n-runs", type=int, required=True,
                        help="Number of acquisitions to run. Each acquisition covers a different set of rows.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't run anything, but show what would be run.")
    parser.add_argument("--retries", type=int, default=3,
                        help="Number of retry attempts in case of failure.")
    parser.add_argument("--summary", default="summary.txt",
                        help="Output txt file with list of runs.")
    args = parser.parse_args()
    rows = list(convert_option_list(args.rows))

    n_runs = min(args.n_runs, len(rows))
    rows_per_run = int((len(rows) + args.n_runs - 1) / args.n_runs)  # Divide and round up
    print(" !!! Will perform %d runs on %d rows => %d rows per run" % (n_runs, len(rows), rows_per_run))
    for i in range(n_runs):
        # Select the rows for this run
        a = i*rows_per_run
        b = (i+1)*rows_per_run
        if b > len(rows):
            b = len(rows)
        i_rows = rows[a:b]
        print(" !!! Run #%d, rows = %s" % (i, i_rows))
        # Make the command line
        cmd = [DAQ_SCRIPT]
        cmd.append("-c")
        cmd.extend(map(str, args.cols))
        cmd.append("-r")
        cmd.extend(map(str, i_rows))
        cmd.append("-i")
        cmd.extend(map(str, args.injs))
        cmd.append("-t")
        cmd.extend(map(str, args.thrs))
        cmd.append("-n")
        cmd.append(str(args.n_cols))
        print(" !!! Executing: %s" % " ".join(cmd))
        if not args.dry_run:
            start_time = time.time()
            for i in range(args.retries):
                if i > 0:
                    print(" !!! Retrying (attempt #%d)" % (i+1))
                exit_code = call(cmd)
                if exit_code == 0:
                    break
                else:
                    print(" !!! Failed with code %d" % exit_code)
            output_file, output_file_mtime = get_latest_output_file()
            if output_file_mtime < start_time:
                print(" !!! No output file found, skipping analysis")
                continue
            with open(args.summary, "a") as ofs:
                print >> ofs, "%s %s" % (output_file, " ".join(cmd))
        else:
            output_file = "DUMMY"
        print(" !!! Output file: %s" % output_file)
        print(" !!! Launching analysis in the background")
        cmd = [ANA_SCRIPT, output_file]
        print(" !!! Executing: %s" % " ".join(cmd))
        if not args.dry_run:
            Popen(cmd)
