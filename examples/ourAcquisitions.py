#!/usr/bin/env python2
"""Acquires data and optionally shows it in real time."""
import argparse
import datetime
from math import floor, log10
import os
import sys
import time
from bitarray import bitarray
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import tables
import yaml
from tjmonopix.tjmonopix import TJMonoPix, FakeTJMonoPix

# Analog front-end default values
#Tutte le misure HV flavor fino al 13 marzo avevano i settaggi:
#VRESET_DAC = 35
#ICASN_DAC = 0
#IRESET_DAC = 2
#ITHR_DAC = 5
#IDB_DAC = 60
#IBIAS_DAC = 100

VRESET_DAC = 43 #35 in default conf #suggested 43 in N_gap
ICASN_DAC = 0
IRESET_DAC = 2
ITHR_DAC = 10 #5 dac in default conf. in N_gapW4R2 ith = 10 dac for both pmos and hv flavor
IDB_DAC = 50
IBIAS_DAC = 45#20 suggested for HV in script N_gapW4R2, 45dac suggested for Pmos flavor

# Masks, found during a IDB=60 scan with no source or injection with auto_mask @ 2 hits / 0.2 s
MASKD = bitarray('1011111111111111111000100111111110010111111111110001101101110111111001010010111010010111001101111110110011011110111010110100010110001001110010011000010101100010000010100011001100100100011110010010000010010001011111000000000101000100011000110100111001110100010110010101110110111101001010111111011111101101111111111101011110101111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111')
MASKH = bitarray('10010111100000100010110110001001010101010101100011010000000001000100011001100010110000011101101000000000100010111110101001000011011000111100000000110110010010000110100111010101011011010100011010000111001101000001111010111000')
MASKV = bitarray('0000100010000010001110100001000000000000000101000100000000000000000000111100111011110101001100000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')

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
    parser.add_argument("--mask-cols", nargs="*", type=int, default=None,
                        help="Skip automask, mask this range of columns.")
    parser.add_argument("-i", "--interval", type=float, default=2,
                        help="The time between two successive data reads in seconds.")
    parser.add_argument("--test", action="store_true",
                        help="Use a 'simulated' chip to test the script.")
    args = parser.parse_args()
    if not args.overwrite and os.path.exists(args.output):
        print("Output file exists already, use -f to overwrite")
        sys.exit(2)
    if args.test:
        TJMonoPix = FakeTJMonoPix

    # Init chip (with power reset => power-cycle it)
    print("Initializing chip...")
    chip = TJMonoPix(conf="../tjmonopix/tjmonopix_mio3.yaml", no_power_reset=False)
    #chip.init(fl="EN_HV")
    chip.init(fl="EN_PMOS")
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
        print("%s: %s" % (k, ps[k]))

    # Setup analog front-end
    print("Setting up analog front-end...")
    chip.set_vreset_dacunits(VRESET_DAC, 1)
    chip.set_ireset_dacunits(IRESET_DAC, 1, 1)
    chip.set_ithr_dacunits(ITHR_DAC, 1)
    chip.set_idb_dacunits(args.idb, 1)
    chip.set_ibias_dacunits(IBIAS_DAC, 1)
    chip.set_icasn_dacunits(ICASN_DAC, 1)
    chip.write_conf()
    print("Analog front-end setup done")
    time.sleep(1)

    # Run automask to check if the chip is behaving (default args are OK)
    if args.mask_cols is None:
        print("Masking noisy pixels...")
        chip.standard_auto_mask(th3=2)
        print("Masking done")
        time.sleep(1)
    elif len(args.mask_cols) == 0:
        chip.unmask_all()
    else:
        chip['CONF_SR'][chip.SET['fl']].setall(False)
        chip['CONF_SR']['EN_OUT'][chip.fl_n] = False
        chip['CONF_SR']['MASKD'].setall(False)
        chip['CONF_SR']['MASKH'].setall(False)
        chip['CONF_SR']['MASKV'].setall(True)
        if len(args.mask_cols) == 2:
            cols = range(args.mask_cols[0], args.mask_cols[1]+1)
        else:
            cols = args.mask_cols
        for col in cols:
            chip['CONF_SR']['MASKV'][chip.fl_n*112+col] = False
        chip.write_conf()
        chip['CONF_SR'][chip.SET['fl']].setall(True)
        chip.write_conf()
    # chip['CONF_SR'][chip.SET['fl']].setall(False)
    # chip['CONF_SR']['EN_OUT'][chip.fl_n] = False
    # chip['CONF_SR']['MASKD'] = MASKD
    # chip['CONF_SR']['MASKV'] = MASKV
    # chip['CONF_SR']['MASKH'] = MASKH
    # chip.write_conf()
    # time.sleep(1)
    # chip['CONF_SR'][chip.SET['fl']].setall(True)
    # chip.write_conf()

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
            fig, axs = plt.subplots(ncols=4)
        # Configure the chip for receiving data
        print("Preparing chip for acquisition")
        chip.enable_data_rx()
        chip.reset_ibias()  # Wait for <mumble mumble> to stabilize
        chip.reset_ibias()
        chip['fifo'].reset()  # Clear everything that was received until now
        start_time = datetime.datetime.now()
        hit_table.attrs.start_time = start_time.isoformat()
        print("%s BEGINNING ACQUISITION" % start_time.isoformat())
        wanted_end_time = start_time + datetime.timedelta(seconds=args.seconds)
        all_data, images, colorbars = None, [None, None, None, None], [None, None]
        try:
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
                if args.show and len(hits) != 0:
                    # Update the plot
                    data, x, y = np.histogram2d(hits["col"], hits["row"], bins=[112,224],
                                                range=[[0,112],[0,224]])

                    tot = (hits["te"]- hits["le"])&0x3F 
                    
                    selected_col_pixel = 4
                    selected_row_pixel = 50
                    # mask = (hits["col"] == selected_col_pixel) & (hits["row"] == selected_row_pixel) 
                    mask = (hits["col"] == selected_col_pixel) & (hits["row"] == selected_row_pixel)
                    
                    if all_data is None:
                        all_data = data
                        all_tot = tot
                        all_tot_single_pixel = tot[mask]                                       
                        #all_data += 0.1
                    else:
                        all_data += data
                        all_tot = np.concatenate((all_tot, tot))
                        all_tot_single_pixel = np.concatenate((all_tot_single_pixel, tot[mask]))
                        
                    if images[0] is None:
                        #legend_colormap = '%d hits' % (len(tot))
                        images[0] = axs[0].imshow(all_data.transpose(), origin='lower', norm=LogNorm())
                        colorbars[0] = plt.colorbar(images[0], ax=axs[0])
                        images[1] = axs[1].imshow(all_data.transpose(), origin='lower')
                        colorbars[1] = plt.colorbar(images[1], ax=axs[1])
                        images[2] = axs[2].hist(all_tot, bins = 64, range = (0, 64))          
                        legend_tot = 'col, row: %d %d' % (selected_col_pixel, selected_row_pixel)
                        images[3] = axs[3].hist(all_tot_single_pixel, bins = 64, range = (0, 64))
                        
                    else:
                        # Set the ticks of the colorbar to round numbers
                        top = max(1, all_data.max())
                        o = floor(log10(top))
                        t = max(1, floor(top / 10**o))
                        images[0].set_data(all_data.transpose())
                        colorbars[0].set_clim(vmin=0.1, vmax=top)
                        colorbars[0].set_ticks(np.logspace(-1, o+1, num=o+3, endpoint=True))
                        colorbars[0].draw_all()
                        images[1].set_data(all_data.transpose())
                        colorbars[1].set_clim(vmin=0, vmax=top)
                        colorbars[1].set_ticks(np.linspace(0, t * 10**o, num=t+1, endpoint=True))
                        colorbars[1].draw_all()
                        axs[2].clear()
                        axs[2].hist(all_tot, bins = 64, range = (0, 64))
                        axs[2].set_yscale("log")
                        axs[3].clear()
                        axs[3].hist(all_tot_single_pixel, bins = 64, range = (0, 64))                    
                        axs[3].set_yscale("log")
        except KeyboardInterrupt:
            pass


        hit_table.attrs.end_time = end_time.isoformat()
        

        hit_table.attrs.duration = (end_time - start_time).total_seconds()
        print("%s ACQUISITION END" % end_time.isoformat())
        print("ACTUAL DURATION %s" % (end_time - start_time))

    print("Output file closed, end of script")
    if args.show:
        print("The script will terminate when you close the plot window")
        # Keep the figure open until it is closed manually
        plt.ioff()
        fig.savefig(args.output[:-3] + ".png")
        plt.show()
        plt.close()
