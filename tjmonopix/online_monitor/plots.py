import matplotlib.pyplot as plt
import numpy as np

def tj_plot(chip, dt=0.2, wait_inj=False):
    """Matrix plotter"""
    chip.enable_data_rx()
    hits, pixels, hits_per_pixel = chip.recv_data_summary(dt, wait_inj)
    
    print("Got %d hits in %g s" % (len(hits), dt))
    
    # Plot of the pixel matrix (2D histogram of number of hits vs row/col)
    plt.figure()
    plt.hist2d(hits["col"], hits["row"], bins=[112,224], range=[[0,112],[0,224]],
               )#norm=matplotlib.colors.LogNorm(vmin=1))
    plt.colorbar()

    # Histogram of the hits-per-pixel distribution (to choose noise threshold)
    plt.figure()
    plt.hist(hits_per_pixel, bins=min(100,np.max(hits_per_pixel)+1), range=[-0.5,np.max(hits_per_pixel)+0.5])
    plt.yscale('log')
    plt.grid(axis="y")
    return hits, pixels, hits_per_pixel
