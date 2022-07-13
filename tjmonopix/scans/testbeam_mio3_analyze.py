"""Analysis script for testbeam_mio3."""
from tjmonopix.scans.simple_scan import SimpleScan

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file', help="The h5 file produced by testbeam_mio3.py")
    args = parser.parse_args()

    SimpleScan.analyze(args.input_file)
