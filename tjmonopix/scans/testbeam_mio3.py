"""TJMonopix acquisition scan for a fixed time."""
import datetime
import argparse

from tjmonopix.tjmonopix import TJMonoPix
from tjmonopix.scans.simple_scan import SimpleScan

NOISY_PIXELS = []  # TODO Acquire noise and put a list of noisy pixels here as (col, row) tuples
HITOR_COL, HITOR_ROW = 50, 102


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--data', required=True,
                        type=lambda x: x + datetime.datetime.now().strftime("_%Y-%m-%d_%H-%M-%S"),
                        help='Name of data file without extension (date and time will be appended)')
    parser.add_argument("-t", '--scan-timeout', type=int, default=10,
                        help="Scan time in seconds (default 10, 0 means forever)")
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

    for col, row in NOISY_PIXELS:
        chip.mask(1, col, row)

    # Enable hitor on a single pixel (must be unmasked by MASKD and/or MASKV)
    chip.enable_hitor(1, HITOR_COL, HITOR_ROW)
    chip.write_conf()

    ####### CONFIGURE THE FRONT END ######
    chip.set_vreset_dacunits(43, 1)
    chip.set_icasn_dacunits(0, 1)
    chip.set_ireset_dacunits(2, 1, 1)
    chip.set_ithr_dacunits(10, 1)
    chip.set_idb_dacunits(50, 1)
    chip.set_ibias_dacunits(45, 1)
    chip.write_conf()

    scan = SimpleScan(dut=chip, filename=args.data)
    output_filename = scan.start(scan_timeout=args.scan_timeout, with_tdc=False, with_timestamp=True, with_tlu=True, with_tj=True)
    # scan.analyze(data_file=output_filename)
