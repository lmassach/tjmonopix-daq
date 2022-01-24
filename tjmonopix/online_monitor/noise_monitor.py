import logging
import time
import numpy as np


"""Save setted parameters (ith, icasn, ecc...) and some information about noisy pixel. Need to be passed: parameteters in dac units, parameters in physical units, number of noisy pixels, number of enabled pixels, outputfile.txt"""  
def save_param_and_noise(param_dac, param, noisy_pixels, disabled_pixels, output_file):
    if not output_file.endswith('.txt'):
        logger.error(".txt file needed \n")
        return
    header ='parameters setting and number of noisy pixels\n date, vl_dac, vh_dac, vreset_dac, icasn_dac, ireset_dac, ithr_dac, idb_dac, ibias_dac, vl[V], vh[V], vreset[V], icasn[nA], ireset[nA], ithr[nA], idb[nA], ibias[nA], noisy_pixels, disabled_pixels\n '
    date = datetime.datetime.now()
    datas = np.array([date, param_dac, param, noisy_pixels, disabled_pixels])
    with open(output_file, "a") as output_file:
        np.savetxt(output_file, datas.reshape(1, datas.shape[0]) , fmt='%s', header=header)
    logger.info("Output file '%s' saved!\n\n" % output_file)         



 

"""Save coordinates of the noisy pixels"""
def save_noisy_pixels(noisy_pixels, output_file):
    if not (of_pixels.endswith('.txt')):  
        logger.error(".txt file needed \n") 
        return
    header ='%s \n %s\n fl  row col' % (datetime.datetime.now(), param_setting())
    fmt = ['%d', '%d', '%d']        
    np.savetxt(output_file, np.transpose([noisy_pixels]) , fmt=fmt, header=header)        
    logger.info("Output file saved!\n\n")         




      
