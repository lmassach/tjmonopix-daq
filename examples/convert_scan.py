#!/usr/bin/env python3
"""Converts a TJMonopix fast scan to ROOT.

Requires tables and uproot:
> pip3 install tables uproot awkward
> # OR
> conda install -c anaconda pytables conda-forge uproot
"""
import os
import sys
import argparse
import glob
import tables
import uproot
import numpy


def ensure_str(s):
    """Converts bytes objects to str.

    Written for compatibility with Python2-generated H5 files.
    """
    if isinstance(s, str):
        return s
    return str(s, encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files_prefix",
                        help="The beginning of the name of the input files, e.g."
                             " 20220210_102224. This is also the out file name.")
    parser.add_argument("-f", "--overwrite", action="store_true",
                        help="Overwrite the output file if already present.")
    parser.add_argument("-s", "--short", action="store_true",
                        help="Skip raw data and other entries to save space.")
    args = parser.parse_args()

    # Find the three files that start with the given prefix
    input_filenames = glob.glob(f"{args.files_prefix}*.h5")
    try:
        input_filename_ev = next(
            fn for fn in input_filenames if fn.endswith("_ev.h5"))
        input_filename_hit = next(
            fn for fn in input_filenames if fn.endswith("_hit.h5"))
        input_filename_scan = next(
            fn for fn in input_filenames if fn.endswith("_scan.h5"))
    except StopIteration:
        print("Could not find one of the scan output files.")
        print("You need 3 files: *_ev.h5 *_hit.h5 *_scan.h5")
        sys.exit(1)
    # Find the common prefix of all three files, and use it for the output file
    input_prefix = os.path.commonprefix([
        input_filename_ev, input_filename_hit, input_filename_scan])
    output_filename = f"{input_prefix}.root"

    # Print what files we are operating on
    print("Reading data from:")
    print(input_filename_ev)
    print(input_filename_hit)
    print(input_filename_scan)
    print()
    print("Writing data to:")
    print(output_filename)
    print()

    # Check if the output file already exists
    if (not args.overwrite) and os.path.isfile(output_filename):
        print("Output file already exist, aborting.")
        print("Use the -f option to overwrite.")
        sys.exit(2)

    # Open the files
    with (uproot.recreate(output_filename) as output_file,
          tables.open_file(input_filename_ev) as input_file_ev,
          tables.open_file(input_filename_hit) as input_file_hit,
          tables.open_file(input_filename_scan) as input_file_scan):
        # Tables from the h5 files -> TTrees in the root file
        output_file["Cnts"] = input_file_ev.root.Cnts[:]
        output_file["Hits"] = input_file_ev.root.Hits[:]
        if not args.short:
            output_file["AllHits"] = input_file_hit.root.Hits[:]
            output_file["meta_data"] = input_file_scan.root.meta_data[:]
            output_file["scan_parameters"] = input_file_scan.root.scan_parameters[:]
            # Raw data array from scan.h5 -> TTree with one column in the root file
            output_file["raw_data"] = input_file_scan.root.raw_data[:].astype(
                numpy.dtype([('word', 'u4')]))
            # Occupancy histogram from ev.h5 -> TH1F in the root file
            output_file["HistOcc"] = uproot.to_writable((
                input_file_ev.root.HistOcc[:],  # Histogram, numpy.histogram2d format
                numpy.linspace(0, 112, 113),  # X edges, numpy.histogram2d format
                numpy.linspace(0, 224, 225)  # Y edges, numpy.histogram2d format
            ))
        # KWargs  from scan.h5 -> a single TString in the root file
        output_file["kwargs"] = uproot.to_writable(
            "\n".join(ensure_str(x) for x in input_file_scan.root.kwargs))
