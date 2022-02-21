#!/usr/bin/env python2
"""Automated TW measurement analysis script"""
import datetime
import argparse
import logging
from tjmonopix.scans.injection_scan import InjectionScan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="The _scan.h5 file.")
    args = parser.parse_args()

    logger = logging.getLogger("main")
    f = logging.Formatter("%(asctime)s %(process)5d %(levelname)-8s %(name)-15s %(message)s", '%Y-%m-%d %H:%M:%S')
    h = logging.StreamHandler()  # Log to console (stderr)
    h.setFormatter(f)
    logger.addHandler(h)
    h = logging.FileHandler("ourTWanalysis.log")  # and also to file
    h.setFormatter(f)
    logger.addHandler(h)
    logger.info("Launched script with args %s", args)

    try:
        start_time = datetime.datetime.now()
        output_filename = InjectionScan.analyze(args.input_file)
        end_time = datetime.datetime.now()
        logger.info("Analysis done in %s", end_time - start_time)
        logger.info("Output file: %s", output_filename)
        logger.info("End of script")
    except:
        logger.exception("An unhandled exception occurred.")
        raise
