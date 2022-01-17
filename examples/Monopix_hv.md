# Auto-mask pseudocode
```python
def mask(pixel):
    MASKD, MASKH, MASKV = whatever_is_needed_to_mask_the_given_pixel

def intepret_data(...):
    ...
    return list((col, row, hit_time, time_over_threshold, noise) for each_hit)

def auto_mask(th=2, step=10, exp=0.2):
    # Keep a list of all noisy pixels (store row, col, diag coordinates)
    noisy_pixels = []

    # Mask all pixels and loop over MASKH (rows)
    MASKD = MASKH = MASKV = all_zeros
    for i in (step:NROWS:step):
        # Unmask rows from 0 to i
        MASKH[0:i] = all_ones
        # Re-mask pixels that were previously found to be noisy
        for pixel in noisy_pixels:
            mask(pixel)
        # Wait for hits to happen
        sleep(exp)
        # Read the data, i.e. get the detected hits
        data = intepret_data(...)
        # Get a list of pixels that were hit, and how many times each pixel was hit
        hit_pixels, hit_counts = np.unique(data, ...)
        total_hit_count = len(data)
        print(f"Enable MASKH {i} Noise data {total_hit_count}")
        # Check that there aren't too many noisy pixels among the unmasked ones
        if len(hit_pixels) > 100:
            print("Too many noisy pixels, try smaller step.")
            return
        # Add pixels hit more than th times to the list of noisy pixels
        for pixel, n_hits in zip(hit_pixels, hit_counts):
            if n_hits >= th:
                noisy_pixels.append(pixel)
        # Print number of noisy pixels found
        print(f"Number of noisy pixels {len(noisy_pixels)}")

    # Loop over MASKV (columns) -> same as the loop above
    # Loop over MASKD (diagonals) -> same as the loop above

    # Mask previously found noisy pixels and check if noise is gone
    MASKD = MASKH = MASKV = all_ones
    for pixel in noisy_pixels:
        mask(pixel)
    # Read the data, i.e. get the detected hits
    data = intepret_data(...)
    # Get a list of pixels that were hit, and how many times each pixel was hit
    hit_pixels, hit_counts = np.unique(data, ...)
    print("Checking noisy pixels after masking...")
    # Check that there aren't too many noisy pixels among the unmasked ones
    if len(hit_pixels) > 100:
        print("Too many noisy pixels, try smaller step.")
        return
    # Add pixels hit more than th times to the list of noisy pixels
    for pixel, n_hits in zip(hit_pixels, hit_counts):
        if n_hits >= th:
            noisy_pixels.append(pixel)
    # Print number of noisy pixels found
    print(f"Number of noisy pixels {len(noisy_pixels)}")

    # Mask additionally found noisy pixels
    MASKD = MASKH = MASKV = all_ones
    for pixel in noisy_pixels:
        mask(pixel)

    print(f"Number of enabled pixels {...}")
    print(f"Number of disable pixels (noisy plus unintentionally masked) {...}")
    return noisy_pixels
```
