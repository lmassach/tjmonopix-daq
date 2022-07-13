import time
import tables as tb
import numpy as np
import yaml
import os
import logging
import datetime

from tjmonopix.scan_base import ScanBase
from tjmonopix.tjmonopix import TJMonoPix
#from tjmonopix.analysis.interpreter import interpret_h5
from tjmonopix.scans.simple_scan import SimpleScan


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='TJ-MONOPIX simple scan \n example: simple_scan --scan_time 10 --data simple_0', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--data', default=None,
                        type=lambda x: x + datetime.datetime.now().strftime("_%Y-%m-%d_%H-%M-%S"),
                        help='Name of data file without extension (date and time will be appended)')
    parser.add_argument("-t", '--scan_timeout', type=int, default=10,
                        help="Scan time in seconds. Default=10, disable=0")
    #parser.add_argument('--config_file', type=str, default=None,
    #                    help="Name of config file(yaml)")
    args = parser.parse_args()    

    chip = TJMonoPix(conf=r"C:\Users\belle2\tjmonopix-daq\tjmonopix\tjmonopix_mio3.yaml", no_power_reset=False)
    chip.init(fl="EN_PMOS")
    chip['data_rx'].CONF_START_FREEZE = 64 #default 3
    chip['data_rx'].CONF_STOP_FREEZE = 100 #default 40
    chip['data_rx'].CONF_START_READ = 66 #default 6
    chip['data_rx'].CONF_STOP_READ = 68 #default 7
    chip['data_rx'].CONF_STOP = 105 #default 45

    # scan.dut and chip are the same thing
    scan = SimpleScan(dut=chip, filename=args.data)

    ####### CONFIGURE mask ######
    scan.dut.unmask_all()

    # # TO USE THE MASK FUNCTION YOU MUST INPUT THE FLAVOR, COLUMN AND ROW
    # # THE FLAVOR NUMERS IS: 0 FOR PMOS_NOSF, 1 FOR PMOS, 2 FOR COMP, 3 FOR HV
    # scan.dut.mask(1, 33, 72)
    # scan.dut.mask(1, 17, 30)
    # scan.dut.mask(1, 19, 31)
    # scan.dut.mask(1, 41, 66)
    # scan.dut.mask(1, 97, 94)
    # scan.dut.mask(1, 34, 151)
    # scan.dut.mask(1, 40, 123)
    # scan.dut.mask(1, 82, 193)
    # scan.dut.mask(1, 71, 31)
    # scan.dut.mask(1, 71, 111)
    # scan.dut.mask(1, 38, 188)
    # scan.dut.mask(1, 97, 214)
    # scan.dut.mask(1, 86, 104)
    # scan.dut.mask(1, 35, 212)
    # scan.dut.mask(1, 35, 88)
    # scan.dut.mask(1, 43, 14)
    # scan.dut.mask(1, 38, 177)
    # scan.dut.mask(1, 17, 57)
    # scan.dut.mask(1, 54, 1)
    # scan.dut.mask(1, 38, 21)
    # scan.dut.mask(1, 71, 9)
    # scan.dut.mask(1, 58, 46)
    # scan.dut.mask(1, 74, 84)
    # scan.dut.mask(1, 53, 167)
    # scan.dut.mask(1, 35, 158)
    # scan.dut.mask(1, 72, 77)
    # scan.dut.mask(1, 14, 54)
    # scan.dut.mask(1, 78, 196)
    # scan.dut.mask(1, 88, 96)
    # scan.dut.mask(1, 78, 209)
    # scan.dut.mask(1, 62, 66)
    # scan.dut.mask(1, 53, 117)
    # scan.dut.mask(1, 103, 132) #8:19 28.03
    # scan.dut.mask(1, 109, 58) #8:19 28.03
    # scan.dut.mask(1, 21, 147) #8:19 28.03
    # #scan.dut['CONF_SR']['EN_PMOS'][54]= False
    
    #This sets up the hit_or in a single pixel
    col = 50
    row = 102
    # scan.dut['CONF_SR']['EN_HITOR_OUT'][1]=False
    # scan.dut.enable_column_hitor(1,col)
    # scan.dut['CONF_SR']['MASKH'][row]=False
    # scan.dut.write_conf()

    ####### CONFIGURE THE FRONT END ######
    scan.dut.set_vreset_dacunits(43,1)
    scan.dut.set_icasn_dacunits(0,1) #4.375nA # approx 1.084V at -3V backbias, 600mV at 0V backbias
    scan.dut.set_ireset_dacunits(2,1,1) #270pA, HIGH LEAKAGE MODE, NORMAL SCALING, 0 = LOW LEAKAGE MODE, SCALING*0.01
    scan.dut.set_ithr_dacunits(10,1) #680pA
    scan.dut.set_idb_dacunits(50,1) #500nA
    scan.dut.set_ibias_dacunits(45,1) #500nA OF THE FRONT END THAT PROVIDES AMPLIFICATION
    scan.dut.write_conf()
    
    output_filename = scan.start(scan_timeout=args.scan_timeout, with_tdc=False, with_timestamp=True, with_tlu=True, with_tj=True)
    scan.analyze(data_file=output_filename)
