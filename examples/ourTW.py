#!/usr/bin/env python2
"""Automated TW measurement script"""
import os
import subprocess
import time
import datetime
import argparse
import logging
import numpy as np
from tjmonopix.tjmonopix import TJMonoPix
from tjmonopix.scans.injection_scan import InjectionScan

# # Analog front-end (for HV)
# VL_DAC = 40
# VH_DAC = 80
# VRESET_DAC = 35
# ICASN_DAC = 0
# IRESET_DAC = 2
# ITHR_DAC = 5
# IDB_DAC = 50
# IBIAS_DAC = 100
# CALCAP = 33  # For HV-flavored pixels

# For PMOS
VL_DAC = 40
VH_DAC = 100
VRESET_DAC = 43 #35 in default conf #suggested 43 in N_gap
ICASN_DAC = 0
IRESET_DAC = 2
ITHR_DAC = 10 #5 dac in default conf. in N_gapW4R2 ith = 10 dac for both pmos and hv flavor
IDB_DAC = 50
IBIAS_DAC = 45#20 suggested for HV in script N_gapW4R2, 45dac suggested for Pmos flavor
CALCAP = 20


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

SCRIPT_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
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
    parser.add_argument("-n", "--n-cols", type=int, default=10,
                        help="Number of columns to scan at a time.")
    parser.add_argument("--no-mask", action="store_true",
                        help="Skip mask/noisy pixels check.")
    parser.add_argument("--launch_analysis", action="store_true",
                        help="Launch analysis in the background at the end.")
    args = parser.parse_args()
    cols = convert_option_list(args.cols)
    rows = convert_option_list(args.rows)
    injs = convert_option_list(args.injs)
    thrs = convert_option_list(args.thrs)

    logger = logging.getLogger("main")
    f = logging.Formatter("%(asctime)s %(levelname)-8s %(name)-15s %(message)s", '%Y-%m-%d %H:%M:%S')
    h = logging.StreamHandler()  # Log to console (stderr)
    h.setFormatter(f)
    logger.addHandler(h)
    h = logging.FileHandler("ourTW.log")  # and also to file
    h.setFormatter(f)
    logger.addHandler(h)
    logger.info("Launched script with args %s", args)
    logger.info("Scanning %d cols, %d rows, %d injs and %d thrs", len(cols), len(rows), len(injs), len(thrs))

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
        icasn = chip.set_icasn_dacunits(ICASN_DAC,1)
        chip.write_conf()
        logger.info("Analog front-end setup done")
        time.sleep(1)

        # Run automask to check if the chip is behaving (default args are OK)
        if args.no_mask:
            logger.info("Skipping noisy pixels check.")
            chip.unmask_all()
            chip["CONF_SR"].write()
        else:
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
        
        """
        logger.info("Testing injection on pixel (%d,%d)", COL_TO_INJECT, ROW_TO_INJECT)
        chip.select_injection(COL_TO_INJECT, ROW_TO_INJECT)
        chip['data_rx'].set_en(False)
        chip.set_monoread()
        for _ in range(5):
            chip['fifo'].reset()
            time.sleep(0.002)
        chip["inj"].start()
        while not chip['inj'].is_ready:
            time.sleep(0.001)
        time.sleep(0.2)
        ix = chip.interpret_data(chip['fifo'].get_data())
        print('ix', ix)
        mask = (ix["col"] == COL_TO_INJECT) & (ix["row"] == ROW_TO_INJECT)
        if abs(len(ix[mask]) - REPEAT) > MAX_DELTA_CNT:
            logger.critical("Hits on injected pixel (%d) too different from number of injection pulses (%d), aborting", len(ix[mask]), REPEAT)
            raise RuntimeError("Incorrect number of hits on injected pixel")
        if len(ix) - len(ix[mask]) > MAX_RESIDUAL_OCCUPANCY:
            logger.critical("Too high occupancy on non-injected pixels (%d hits), aborting", len(ix) - len(ix[mask]))
            raise RuntimeError("Too high occupancy on non-injected pixels")
        logger.info("Injection check done")
        time.sleep(1)
        """


        logger.info("Launching the scan...")
        scans = InjectionScan(dut=chip)
        start_time = datetime.datetime.now()
        output_filename = scans.start(
            collist=cols, rowlist=rows, injlist=injs, thlist=thrs,
            phaselist=None, with_mon=False, n_mask_col=args.n_cols, debug=4)
        end_time = datetime.datetime.now()
        logger.info("Scan done in %s", end_time - start_time)
        logger.info("Output file: %s", output_filename)

        if args.launch_analysis:
            cmd = [ANA_SCRIPT, output_filename]
            logger.info("Launching analysis in the background, executing: %s" % cmd)
            subprocess.Popen(cmd)

        logger.info("End of script")
    except:
        logger.exception("An unhandled exception occurred.")
        raise
