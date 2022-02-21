import numpy as np
 
 
def find_approx_threshold(injlist, inj_high, cnt, CALCAP, repeat=100):
    """Find the threshold and the sigma as the middle point and the 68% of the width of the s-curve  """
    conversion_factor = np.mean(inj_high/injlist)
    
    approx_threshold_dac = injlist[np.argmin( np.abs(cnt - repeat/2) )]
    approx_threshold = approx_threshold_dac * conversion_factor
    approx_charge_threshold = approx_threshold_dac * CALCAP
    print "approx. th = %d DAC = %.3f V = %g e-" % (approx_threshold_dac, approx_threshold, approx_charge_threshold)

    approx_sigma_dac = injlist[np.argmin( np.abs(cnt - repeat * 0.84) )] - injlist[np.argmin( np.abs(cnt - repeat * 0.16) )]
    approx_sigma = approx_sigma_dac * conversion_factor
    approx_charge_sigma = approx_sigma_dac * CALCAP
    print "sigma %d DAC = %.3f V = %g e-" % (approx_sigma_dac, approx_sigma, approx_charge_sigma)  
    return approx_charge_threshold, approx_charge_sigma
        

