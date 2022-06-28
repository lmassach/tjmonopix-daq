#!/usr/bin/env python2

import os
import subprocess
import time
import datetime
import yaml
import tables
import signal
import argparse
import logging
import traceback
import numpy as np
from tjmonopix.tjmonopix import TJMonoPix
from tjmonopix.scans.injection_scan import InjectionScan

# For PMOS
VL_DAC = 40
VH_DAC = 100
VRESET_DAC = 43 #35 in default conf #suggested 43 in N_gap
ICASN_DAC = 0
IRESET_DAC = 2
ITHR_DAC = 10 #5 dac in default conf. in N_gapW4R2 ith = 10 dac for both pmos and hv flavor
IDB_DAC = 50
IBIAS_DAC = 45#20 suggested for HV in script N_gapW4R2, 45dac suggested for Pmos flavor

# Injected pulse
DELAY = 800  # In clock units (40 MHz)
WIDTH = 70
REPEAT = 100  # Number of pulses injected

# Limits for checking that the chip is behaving
MAX_NOISY_PIXELS = 300  # Crash if more than this noisy pixels
MAX_RESIDUAL_OCCUPANCY = 50  # Max hits/0.2s after masking

# Parameters for checking that injection is behaving
COL_TO_INJECT = 66
ROW_TO_INJECT = 10
MAX_DELTA_CNT = 5


OUTPUT_FILE = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_tau_scan.h5")
HIT_DTYPE = np.dtype([
    ("col", "<u1"), ("row", "<u2"), ("le", "<u1"), ("te", "<u1"),
    ("noise", "<u1"), ("timestamp", "<u8")])

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-c", "--cols", required=True, nargs="+", type=int,
                        help="The column range or value.")
    parser.add_argument("-r", "--rows", required=False, nargs="+", type=int,
                        help="The row range or value.")
    parser.add_argument("-i", "--injs", required=True, nargs="+", type=int,
                        help="The injection range or value.")
    parser.add_argument("-t", "--thrs", required=True, nargs="+", type=int,
                        help="The threshold range or value.")
    parser.add_argument("-o", "--output", default=OUTPUT_FILE,
                        help="Output .h5 file, default DATE_TIME_acq.h5")

    args = parser.parse_args()
    col_to_inject = convert_option_list(args.cols)
    row_to_inject = convert_option_list(args.rows)
    injs = convert_option_list(args.injs)
    thrs = convert_option_list(args.thrs)

    logger = logging.getLogger("main")
    f = logging.Formatter("%(asctime)s %(levelname)-8s %(name)-15s %(message)s", '%Y-%m-%d %H:%M:%S')
    h = logging.StreamHandler()  # Log to console (stderr)
    h.setFormatter(f)
    logger.addHandler(h)
    h = logging.FileHandler("tau_scan.log")  # and also to file
    h.setFormatter(f)
    logger.addHandler(h)
    #logger.info("Launched script with args %s", args)

    try:
        # Init chip (with power reset, we want a power-cycle to avoid issues)
        logger.info("Initializing chip...")
        chip = TJMonoPix(conf="../tjmonopix/tjmonopix_mio3.yaml", no_power_reset=False)
        chip.init(fl="EN_PMOS")
        chip['data_rx'].CONF_START_FREEZE = 64 #default 3
        chip['data_rx'].CONF_STOP_FREEZE = 100 #default 40
        chip['data_rx'].CONF_START_READ = 66 #default 6
        chip['data_rx'].CONF_STOP_READ = 68 #default 7
        chip['data_rx'].CONF_STOP = 105 #default 45        
        chip['CONF']['EN_RST_BCID_WITH_TIMESTAMP'] = True
        chip['CONF']['RESET_BCID'] = 1
        chip.write_conf()
        logger.info("Chip initialized")
        time.sleep(1)
        
        # Get and log power status
        ps = chip.get_power_status()
        logger.info("Power status")
        for k in sorted(ps.keys()):
            logger.info("%s: %s", k, ps[k])
        time.sleep(1)

        # Setup analog front-end
        logger.info("Setting up analog front-end...")
        vl = chip.set_vl_dacunits(VL_DAC,1)
        vh = chip.set_vh_dacunits(VH_DAC,1)
        chip.write_conf()
        vreset = chip.set_vreset_dacunits(VRESET_DAC, 1)
        ireset = chip.set_ireset_dacunits(IRESET_DAC,1,1)
        ithr = chip.set_ithr_dacunits(ITHR_DAC,1)
        idb = chip.set_idb_dacunits(IDB_DAC,1)
        ibias = chip.set_ibias_dacunits(IBIAS_DAC,1)
        chip.write_conf()
        logger.info("Analog front-end setup done")
        time.sleep(1)

        # Run automask to check if the chip is behaving (default args are OK)
        logger.info("Checking noisy pixels...")
        noisy_pixels, n_disabled_pixels, mask = chip.auto_mask()
        if len(noisy_pixels) > MAX_NOISY_PIXELS:
            logger.critical("Too many noisy pixels (%d), aborting", len(noisy_pixels))
            raise RuntimeError("Too many noisy pixels")
        logger.info("Masking done, checking residual occupancy...")
        pix_tmp, cnt = chip.get_occupancy(0.2)
        if cnt.sum() > MAX_RESIDUAL_OCCUPANCY:
            logger.critical("Too high residual occupancy after masking (%d hits), aborting", cnt.sum())
            raise RuntimeError("Too high residual occupancy")
        logger.info("Noisy pixels check done")
        time.sleep(1)

        # Setup injection and test it on one pixel
        logger.info("Setting up injection...")
        chip['inj'].set_delay(DELAY)
        chip['inj'].set_width(WIDTH)
        chip['inj'].set_repeat(REPEAT)
        chip['inj'].set_phase(0)
        chip['inj'].set_en(0)
        time.sleep(1)

        start_time = datetime.datetime.now()
        print("Opening output file")
        with tables.open_file(args.output, "w") as output_file:
            hit_table = output_file.create_table(
                output_file.root, "Hits", HIT_DTYPE, "Hits")
            # Save chip status and configuration in the Hits table attributes
            print("Saving chip status and configuration to output file")
            hit_table.attrs.power_status = chip.get_power_status()
            hit_table.attrs.config_status = yaml.dump(chip.get_configuration())
            hit_table.attrs.set_status = chip.SET
            hit_table.attrs.start_time = start_time.isoformat()
            print("%s BEGINNING ACQUISITION" % start_time.isoformat())
            
            # Configure Python to not crash when it receives CTRL+C
            CTRL_C_RECEIVED = False
            def handle_ctrl_c(sn, f):
                global CTRL_C_RECEIVED
                CTRL_C_RECEIVED = True
            signal.signal(signal.SIGINT, handle_ctrl_c)

            #logger.info("Testing random injection on pixels ")
            for i in range(10):
                if CTRL_C_RECEIVED:
                    break
                #Set up the injection
                print("col to inject, row to inject", col_to_inject, row_to_inject)
                chip.enable_injection(1, col_to_inject[0], row_to_inject[0])
                #chip.select_injection(col_to_inject, row_to_inject = None, flavor=1)
                print("Preparing chip for acquisition")
                chip.enable_data_rx()
                #inject
                chip.inject()
                while not chip['inj'].is_ready:
                    time.sleep(0.001)        
                time.sleep(0.1)
                
                hits = chip.interpret_data_timestamp(chip['fifo'].get_data())
                hit_table.append(hits)
                hit_table.flush()  # Write to file immediately, so data is on disk
                #print("Received %d injection in %.2f s (%.1f hits/s)" % (len(hits), delta_t, float(len(hits)) / delta_t))
            
                end_time = datetime.datetime.now()
                time.sleep(1)
                
    
    except Exception:
            print(traceback.format_exc())
    except KeyboardInterrupt:
            print(traceback.format_exc())
    except KeyboardInterrupt:
        print(traceback.format_exc())
    # Configure Python to crash on CTRL+C again
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    end_time = datetime.datetime.now()
    #hit_table.attrs.end_time = end_time.isoformat()
    #hit_table.attrs.duration = (end_time - start_time).total_seconds()
    print("%s ACQUISITION END" % end_time.isoformat())
    print("ACTUAL DURATION %s" % (end_time - start_time))




