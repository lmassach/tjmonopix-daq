import logging
import time
import numpy as np
import datetime

logger = logging.getLogger(__name__)

def save_power_status(power_status, output_file):
    """Save power status """
    if not output_file.endswith('.txt'):
        logger.error(".txt file needed")
        return
    date = datetime.datetime.now().isoformat()
    power_status['date'] = date
    with open(output_file, 'w') as convert_file:
        convert_file.write(str(power_status))    
    logger.info("Output file saved!")          


def save_param_and_noise(param_dac, param, noisy_pixels, disabled_pixels, output_file):
    """Save setted parameters (ith, icasn, ecc...) and some information bout noisy pixel. Need to be passed: parameteters in dac units, parameters in physical units, number of noisy pixels, number of enabled pixels, outputfile.txt"""
    if not output_file.endswith('.txt'):
        logger.error(".txt file needed")
        return
    header ='parameters setting and number of noisy pixels\n date, vl_dac, vh_dac, vreset_dac, icasn_dac, ireset_dac, ithr_dac, idb_dac, ibias_dac, vl[V], vh[V], vreset[V], icasn[nA], ireset[nA], ithr[nA], idb[nA], ibias[nA], noisy_pixels, disabled_pixels'
    date = datetime.datetime.now()
    datas = np.array([date, param_dac, param, noisy_pixels, disabled_pixels])
    with open(output_file, "a") as ofs:
        np.savetxt(ofs, datas.reshape(1, datas.shape[0]) , fmt='%s', header=header)
    logger.info("Output file '%s' saved!" % output_file)


def save_noisy_pixels(noisy_pixels, output_file):
    """Save coordinates of the noisy pixels"""
    if not (output_file.endswith('.txt')):  
        logger.error(".txt file needed") 
        return
    header ='%s\nfl  row col' % datetime.datetime.now().isoformat()     
    np.savetxt(output_file, noisy_pixels, header=header)        
    logger.info("Output file saved!")         


