# python3 launcher.py -f 20220622_154229
import argparse
import os
import glob
import subprocess
import time

SCRIPT_DIR = os.path.dirname(__file__)
SCURVE_TOT_HISTO = os.path.join(SCRIPT_DIR, "scurve_tot_histo.py")
TOT_FIT = os.path.join(SCRIPT_DIR, "tot_fit.py")
TOT_CHARGE_PLOTTING = os.path.join(SCRIPT_DIR, "tot_charge_plotting.py")

description = ''
options_parser = argparse.ArgumentParser(description = description)
options_parser.add_argument('-input_inj_file_data', '-f', required=True, help='input_inj_file_data')
# TODO The number of injection does not make sense for the test beam
options_parser.add_argument('-injection_max', '-i', default=100, type=int, help='injection_max')
options_parser.add_argument('-col_selected', '-c', default=25, type=int, help='col_selected')
options_parser.add_argument('-row_selected', '-r', default=25, type=int, help='row_selected')

options = vars(options_parser.parse_args())
input_inj_file_data = options['input_inj_file_data']
injection_max = options['injection_max']
col_selected = options['col_selected']
row_selected = options['row_selected']

start_time = time.time()

print("     RUNNING scurve_tot_histo.py,  %s SECONDS " % (time.time() - start_time))
subprocess.run(['python', SCURVE_TOT_HISTO, '-f', input_inj_file_data, '-i', '1', str(injection_max)])


print("     RUNNING tot_fit.py,  %s SECONDS " % (time.time() - start_time))
subprocess.run(['python', TOT_FIT, '-f', input_inj_file_data, '-i', '1', str(injection_max)])


print("     RUNNING tot_charge_plotting.py,  %s SECONDS " % (time.time() - start_time))
subprocess.run(['python', TOT_CHARGE_PLOTTING, '-f', input_inj_file_data, '-c', str(col_selected), '-r', str(row_selected)])


