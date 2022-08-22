"""TJMonopix acquisition scan for a fixed time."""
import datetime
import argparse

from tjmonopix.tjmonopix import TJMonoPix
from tjmonopix.scans.simple_scan import SimpleScan

NOISY_PIXELS = [(62, 97)]  # TODO Acquire noise and put a list of noisy pixels here as (col, row) tuples
# [(1, 141), (1, 203), (3, 210), (11, 68), (18, 27), (23, 142), (28, 0), (30, 66), (31, 165), (38, 186), (41, 31), (42, 16), (43, 17), (53, 60), (53, 124), (56, 187), (62, 97), (64, 183), (65, 114), (66, 152), (71, 64), (73, 221), (76, 44), (79, 154), (79, 155), (79, 162), (85, 106), (86, 61), (88, 164), (89, 12), (89, 178), (91, 78), (92, 50), (93, 129), (93, 167), (95, 141), (97, 152), (98, 18), (99, 76), (104, 79), (104, 118), (108, 123), (108, 129), (108, 207), (109, 64), (111, 156)]
HITOR_COL, HITOR_ROW = 50, 102


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--data', required=True,
                        type=lambda x: x + datetime.datetime.now().strftime("_%Y-%m-%d_%H-%M-%S"),
                        help='Name of data file without extension (date and time will be appended)')
    parser.add_argument("-t", '--scan-timeout', type=int, default=10,
                        help="Scan time in seconds (default 10, 0 means forever)")
    parser.add_argument("-a", '--automasking', default=True,
                        help="If True the standard automasking mode il selected")
    args = parser.parse_args()

    chip = TJMonoPix(conf=r"C:\Users\belle2\tjmonopix-daq\tjmonopix\tjmonopix_mio3.yaml", no_power_reset=False)
    chip.init(fl="EN_PMOS")
    chip['data_rx'].CONF_START_FREEZE = 64  #default 3
    chip['data_rx'].CONF_START_READ = 66  #default 6
    chip['data_rx'].CONF_STOP_READ = 68  #default 7
    chip['data_rx'].CONF_STOP_FREEZE = 100  #default 40
    chip['data_rx'].CONF_STOP = 105  #default 45

    ####### MASK NOISY PIXELS ######
    chip.unmask_all()
    if args.automasking is True:
        chip.standard_auto_mask()    
    else: 
        for col, row in NOISY_PIXELS:
            chip.mask(1, col, row)
    # Enable hitor on a single pixel (must be unmasked by MASKD and/or MASKV)
    chip.enable_hitor(1, HITOR_COL, HITOR_ROW)
    chip.write_conf()

    ####### CONFIGURE THE FRONT END ######
    chip.set_vreset_dacunits(43, 1)
    chip.set_icasn_dacunits(0, 1)
    chip.set_ireset_dacunits(127, 1, 1)
    chip.set_ithr_dacunits(10, 1)
    chip.set_idb_dacunits(50, 1)
    chip.set_ibias_dacunits(45, 1)
    chip.write_conf()

    scan = SimpleScan(dut=chip, filename=args.data)
    output_filename = scan.start(scan_timeout=args.scan_timeout, with_tdc=False, with_timestamp=True, with_tlu=True, with_tj=True)
    # scan.analyze(data_file=output_filename)
