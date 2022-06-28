"""Launches the analysis and plotting on new files as soon as ready.
Must be run with Python3."""
# **Dependencies on Windows**
# For Phython3: must install numpy+mkl from <https://www.lfd.uci.edu/~gohlke/pythonlibs/>,
# and then install tables (you may need to uninstall numexpr if you had already installed tables).
#  - <https://download.lfd.uci.edu/pythonlibs/archived/cp37/numpy-1.21.6+mkl-cp37-cp37m-win_amd64.whl>
#  - <https://download.visualstudio.microsoft.com/download/pr/6b6923b0-3045-4379-a96f-ef5506a65d5b/426A34C6F10EA8F7DA58A8C976B586AD84DD4BAB42A0CFDBE941F1763B7755E5/VC_redist.x64.exe>
#
# Complete list of dependencies: numpy scipy matplotlib tables colorama
import os
import subprocess
import argparse
import time
import re
import glob
import datetime
import colorama
colorama.init()

PYTHON3_PATH = r'C:\Program Files\Python37\python.exe'
PYTHON2_ACTIVATION_CMD = rf'{os.environ["USERPROFILE"]}\miniconda2\Scripts\activate.bat {os.environ["USERPROFILE"]}\miniconda2'

SCRIPT_DIR = os.path.dirname(__file__)
ANA_SCRIPT = os.path.join(SCRIPT_DIR, "ourTWanalysis.py")
PLOT_SCRIPT = os.path.join(SCRIPT_DIR, r"analysis\launcher.py")
SCAN_FILES = "output_data/*_scan.h5"  # Glob expression for input files
SCAN_TO_ANA_FILES = (r'_scan\.h5$', r'_ev.h5')  # re.sub args to convert input file name to output file name


def escape_argument(arg):
    """See https://stackoverflow.com/a/29215357"""
    if not arg or re.search(r'(["\s])', arg):
        arg = '"' + arg.replace('"', r'\"') + '"'
    return arg


def py3(args, **kwargs):
    if isinstance(args, str):
        args = [args]
    args = [PYTHON3_PATH] + list(args)
    print("\x1b[36m", " ".join(args), "\x1b[0m")
    return subprocess.run(args, **kwargs)


def py2(args, **kwargs):
    if isinstance(args, str):
        args = [args]
    ln = PYTHON2_ACTIVATION_CMD + " && " + " ".join(escape_argument(x) for x in args)
    args = ["cmd", "/C", ln]
    print("\x1b[36m", " ".join(args), "\x1b[0m")
    return subprocess.run(args, **kwargs)


def is_file_open(path):
    """See https://stackoverflow.com/a/37256114"""
    try:
        os.rename(path, path)
        return False
    except OSError:
        return True


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-n", type=float, default=0, help="Repeat every N seconds.")
args = parser.parse_args()

while True:
    print(f"Listing scan files @ {datetime.datetime.now().isoformat(' ')}...", end='\r')
    for scan_file in glob.iglob(SCAN_FILES):
        ana_file = re.sub(*SCAN_TO_ANA_FILES, scan_file)
        if os.path.isfile(ana_file):
            # print(f"Skipping {scan_file} ({ana_file} exists)")
            continue
        if is_file_open(scan_file):
            # print(f"Skipping {scan_file} (still being written)")
            continue
        print(f"Analyzing {scan_file}")
        if py2([ANA_SCRIPT, scan_file]).returncode:
            print(f"ERR Analysis failed, delete {ana_file} to retry")
            continue
        print(f"Plotting  {scan_file}")
        if py3([PLOT_SCRIPT, "-f", ana_file[:-len("_ev.h5")]]).returncode:
            print(f"ERR Plotting failed, delete {ana_file} to retry")

    if args.n > 0:
        time.sleep(args.n)
    else:
        break
