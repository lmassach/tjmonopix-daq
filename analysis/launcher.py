import argparse
import os
import glob
import subprocess
import time

description = ''
options_parser = argparse.ArgumentParser(description = description)
options_parser.add_argument('-input_inj_file_data', '-f', default=None, type=str, help='input_inj_file_data')
options_parser.add_argument('-injection_max', '-i', default=None, type=int, help='injection_max')
options_parser.add_argument('-col_selected', '-c', default=None, type=int, help='col_selected')
options_parser.add_argument('-row_selected', '-r', default=None, type=int, help='row_selected')

options = vars(options_parser.parse_args())
input_inj_file_data = options['input_inj_file_data']
injection_max = options['injection_max']
col_sel = options['col_selected']
row_selected = options['row_selected']

start_time = time.time()
print("     RUNNING scurve_tot_histo.py,  %s SECONDS " % (time.time() - start_time))
cmd = 'python3 scurve_tot_histo.py -f %s -i 1 %d' % (input_inj_file_data, injection_max)
subprocess.run(cmd, shell = True)


print("     RUNNING tot_fit.py,  %s SECONDS " % (time.time() - start_time))
cmd = 'python3 tot_fit.py -f %s -i 1 %d' % (input_inj_file_data, injection_max)
subprocess.run(cmd, shell = True)


print("     RUNNING tot_charge_plotting.py,  %s SECONDS " % (time.time() - start_time))
cmd = 'python3 tot_charge_plotting.py -f %s -c %d -r %d' % (input_inj_file_data, col_selected, row_selected)
subprocess.run(cmd, shell = True)


