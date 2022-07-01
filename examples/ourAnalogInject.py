#!/usr/bin/env python2
"""Injects in analog pixels"""
import os
import subprocess
import time
import datetime
import argparse
from itertools import product
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
IDB_DAC = 40
IBIAS_DAC = 45#20 suggested for HV in script N_gapW4R2, 45dac suggested for Pmos flavor
CALCAP = 20

# Injected pulse
DELAY = 800  # In clock units (40 MHz)
WIDTH = 150
REPEAT = 100  # Number of pulses injected
COL_TO_INJECT = 50
# Rows are determined by the analog pixels (220-223)


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
    parser.add_argument("-i", "--injs", default=[80], nargs="+", type=int,
                        help="The injection range or value (default 80).")
    for reg in ["VRESET", "ICASN", "IRESET", "ITHR", "IDB", "IBIAS"]:
        parser.add_argument("--" + reg.lower(), default=[vars()[reg + "_DAC"]],
                            nargs="+", type=int,
                            help="The %s range or value(s) (default %d)" % (
                                reg, vars()[reg + "_DAC"]))
    parser.add_argument("-t", "--thrs", default=[IDB_DAC], nargs="+", type=int,
                        help="The threshold range or value.")
    parser.add_argument("-n", default=1, type=int,
                        help="Number of injections.")
    args = parser.parse_args()
    injs = convert_option_list(args.injs)
    thrs = convert_option_list(args.idb)

    try:
        # Init chip (with power reset, we want a power-cycle to avoid issues)
        print("Initializing chip...")
        chip = TJMonoPix(conf="../tjmonopix/tjmonopix_mio3.yaml", no_power_reset=False)
        chip.init(fl="EN_PMOS")
        chip['data_rx'].CONF_START_FREEZE = 64 #default 3
        chip['data_rx'].CONF_STOP_FREEZE = 100 #default 40
        chip['data_rx'].CONF_START_READ = 66 #default 6
        chip['data_rx'].CONF_STOP_READ = 68 #default 7
        chip['data_rx'].CONF_STOP = 105 #default 45
        print("Chip initialized")
        time.sleep(1)

        # Get and log power status
        ps = chip.get_power_status()
        print("Power status")
        for k in sorted(ps.keys()):
            print("%s: %s", k, ps[k])
        time.sleep(1)

        # Setup analog front-end
        print("Setting up analog front-end...")
        vl = chip.set_vl_dacunits(VL_DAC,1)
        vh = chip.set_vh_dacunits(VH_DAC,1)
        chip.write_conf()
        vreset = chip.set_vreset_dacunits(VRESET_DAC, 1)
        ireset = chip.set_ireset_dacunits(IRESET_DAC,1,1)
        ithr = chip.set_ithr_dacunits(ITHR_DAC,1)
        icasn = chip.set_icasn_dacunits(ICASN_DAC,1)
        idb = chip.set_idb_dacunits(IDB_DAC,1)
        ibias = chip.set_ibias_dacunits(IBIAS_DAC,1)
        chip.write_conf()
        print("Analog front-end setup done")
        time.sleep(1)

        # Setup injection and test it on one pixel
        print("Setting up injection...")
        chip['inj'].set_delay(DELAY)
        chip['inj'].set_width(WIDTH)
        chip['inj'].set_repeat(REPEAT)
        chip['inj'].set_phase(0)
        chip['inj'].set_en(0)
        
        # Mask everything except rows 220-223
        chip.mask_all()
        chip['CONF_SR'][chip.SET['fl']].setall(False)
        chip['CONF_SR']['MASKH'][220] = True
        chip['CONF_SR']['MASKH'][221] = True
        chip['CONF_SR']['MASKH'][222] = True
        chip['CONF_SR']['MASKH'][223] = True
        chip['CONF_SR']['MASKV'][chip.fl_n * 112 + COL_TO_INJECT] = True
        chip.write_conf()
        chip['CONF_SR'][chip.SET['fl']].setall(True)
        chip.write_conf()
        
        # Enable analog output and injection to analog pixels
        chip.enable_analog(col="all")
        chip["inj"].set_repeat(args.n)
        # Also injecti on column COL_TO_INJECT
        chip['CONF_SR']['COL_PULSE_SEL'][(chip.fl_n * 112) + COL_TO_INJECT] = True
        
        # Enable HITOR
        chip.enable_hitor(chip.fl_n, COL_TO_INJECT, 220)
        chip.enable_hitor(chip.fl_n, COL_TO_INJECT, 221)
        chip.enable_hitor(chip.fl_n, COL_TO_INJECT, 222)
        chip.enable_hitor(chip.fl_n, COL_TO_INJECT, 223)
        chip.write_conf()
        
        for vreset, icasn, ireset, ithr, ibias in product(*map(convert_option_list, [args.vreset, args.icasn, args.ireset, args.ithr, args.ibias])):
            chip.set_vreset_dacunits(int(vreset), 1)
            chip.set_ireset_dacunits(int(ireset),1,1)
            chip.set_ithr_dacunits(int(ithr),1)
            chip.set_icasn_dacunits(int(icasn),1)
            chip.set_ibias_dacunits(int(ibias),1)
            for th in thrs:
                chip.set_idb_dacunits(th, 1)
                for inj in injs:
                    chip.set_vl_dacunits(VH_DAC - inj,1)
                    chip.write_conf()
                    time.sleep(0.1)
                    chip.inject()
        
        print("End of script")
    except:
        print("An unhandled exception occurred.")
        raise
