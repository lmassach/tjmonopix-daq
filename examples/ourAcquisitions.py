#!/usr/bin/env python2
"""Acquires data and optionally shows it in real time."""
import argparse
import datetime
import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
import tables
import yaml
from tjmonopix.tjmonopix import TJMonoPix

# Analog front-end default values
VRESET_DAC = 35
ICASN_DAC = 0
IRESET_DAC = 2
ITHR_DAC = 5
IDB_DAC = 50
IBIAS_DAC = 100

# Default output file
OUTPUT_FILE = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_acq.h5")

# Hit data type
HIT_DTYPE = np.dtype(
    [("col", "<u1"), ("row", "<u2"), ("le", "<u1"), ("te", "<u1"), ("noise", "<u1")])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seconds", type=float,
                        help="Duration of the acquisition in seconds")
    parser.add_argument("-o", "--output", default=OUTPUT_FILE,
                        help="Output .h5 file, default DATE_TIME_acq.h5")
    parser.add_argument("-f", "--overwrite", action="store_true",
                        help="Overwrite the output file if already present.")
    parser.add_argument("--idb", type=int, default=IDB_DAC,
                        help="The threshold (IDB) value (in DAC)")
    parser.add_argument("--show", action="store_true",
                        help="Shows a plot in realtime.")
    parser.add_argument("--no-automask", dest="automask", action="store_false",
                        help="Skip noisy pixels masking.")
    parser.add_argument("-i", "--interval", type=float, default=2,
                        help="The time between two successive data reads in seconds.")
    args = parser.parse_args()
    if not args.overwrite and os.path.exists(args.output):
        print("Output file exists already, use -f to overwrite")
        sys.exit(2)

    # Init chip (with power reset => power-cycle it)
    print("Initializing chip...")
    chip = TJMonoPix(conf="../tjmonopix/tjmonopix_mio3.yaml", no_power_reset=False)
    chip.init(fl="EN_HV")
    chip['data_rx'].CONF_START_FREEZE = 64  # default 3
    chip['data_rx'].CONF_STOP_FREEZE = 100  # default 40
    chip['data_rx'].CONF_START_READ = 66  # default 6
    chip['data_rx'].CONF_STOP_READ = 68  # default 7
    chip['data_rx'].CONF_STOP = 105  # default 45
    print("Chip initialized")
    time.sleep(1)

    # Get and log power status
    ps = chip.get_power_status()
    print("Power status")
    for k in sorted(ps.keys()):
        print("%s: %s", k, ps[k])

    # Setup analog front-end
    print("Setting up analog front-end...")
    chip.write_conf()
    chip.set_vreset_dacunits(VRESET_DAC, 1)
    chip.set_ireset_dacunits(IRESET_DAC, 1, 1)
    chip.set_ithr_dacunits(ITHR_DAC, 1)
    chip.set_idb_dacunits(args.idb, 1)
    chip.set_ibias_dacunits(IBIAS_DAC, 1)
    chip.write_conf()
    print("Analog front-end setup done")
    time.sleep(1)

    # Run automask to check if the chip is behaving (default args are OK)
    if args.automask:
        print("Masking noisy pixels...")
        noisy_pixels, n_disabled_pixels, mask = chip.auto_mask()
        print("Masking done")
        time.sleep(1)

    # Do the actual acquisition
    print("Opening output file")
    with tables.open_file(args.output, "w") as output_file:
        hit_table = output_file.create_table(
            output_file.root, "Hits", HIT_DTYPE, "Hits")
        # Save chip status and configuration in the Hits table attributes
        print("Saving chip status and configuration to output file")
        hit_table.attrs.power_status = chip.get_power_status()
        hit_table.attrs.config_status = yaml.dump(chip.get_configuration())
        hit_table.attrs.set_status = chip.SET
        if args.show:
            # Enter matplotlib interactive mode and open a figure
            plt.ion()
            fig, ax = plt.subplots()
        # Configure the chip for receiving data
        print("Preparing chip for acquisition")
        chip.enable_data_rx()
        chip.reset_ibias()  # Wait for <mumble mumble> to stabilize
        chip.reset_ibias()
        chip['fifo'].reset()  # Clear everything that was received until now
        start_time = datetime.datetime.now()
        hit_table.start_time = start_time.astimezone().isoformat()
        print("%s BEGINNING ACQUISITION" % start_time.isoformat())
        wanted_end_time = start_time + datetime.timedelta(seconds=args.seconds)
        image, all_data = None, None
        while datetime.datetime.now() < wanted_end_time:
            # Sleep for args.interval seconds, or until the end of the acquisition (whichever comes first)
            sleep_time = min(args.interval, (wanted_end_time - datetime.datetime.now()).total_seconds())
            if args.show:
                plt.pause(sleep_time)  # While waiting, update the plot window
            else:
                time.sleep(sleep_time)
            # Retrieve the hits acquired until now
            end_time = datetime.datetime.now()
            hits = chip.interpret_data(chip['fifo'].get_data())
            # Write the hits to the h5 file
            hit_table.append(hits)
            hit_table.flush()  # Write to file immediately, so data is on disk
            print("Received %d hits" % len(hits))
            if args.show:
                # Update the plot
                data, x, y = np.histogram2d(hits["col"], hits["row"], bins=[112,224],
                                            range=[[0,112],[0,224]])
                if all_data is None:
                    all_data = data
                else:
                    all_data += data
                if image is None:
                    image = plt.imshow(all_data, origin='lower')
                else:
                    image.set_data(all_data)

        hit_table.end_time = end_time.astimezone().isoformat()
        hit_table.duration = (end_time - start_time).total_seconds()
        print("%s ACQUISITION END" % end_time.isoformat())
        print("ACTUAL DURATION %s" % (end_time - start_time))

    print("Output file closed, end of script")
    if args.show:
        # Keep the figure open until it is closed manually
        plt.ioff()
        plt.show()
        plt.close()
