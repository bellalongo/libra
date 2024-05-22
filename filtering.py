import csv
import matplotlib.pyplot as plt
import numpy as np
import sys


# Global variables
period_bool_list = []


"""
    Creates a sine wave based off of given parameters
    Name:       sine_wave()
    Parameters: 
                x: data points
                amplitude: desired amplitude
                frequency: desired frequency
                phase: desired phase
    Returns:
                a sine wave
"""
def sine_wave(x, amplitude, frequency, phase):
    return amplitude * np.sin((2 * np.pi * frequency * x) + phase)


"""
    Determines if the period at max power of a periodogram is real based off of standard deviation
    Name:       is_real_period()
    Parameters: 
                periodogram: periodogram of the lightcurve
    Returns:
                boolean: True if the period is real, False if not real
                period: period at max power
"""
def is_real_period(periodogram):
    # Remove NaNs from the periodogram
    nan_mask = ~np.isnan(periodogram.power)
    periodogram_power = periodogram.power[nan_mask]
    periodogram_period = periodogram.period[nan_mask].value

    # Sort the power array in descending order
    max_power = max(periodogram_power)
    std_dev = np.std(periodogram_power)
    index = np.where(periodogram_power == max_power)[0][0]
    period = periodogram_period[index]

    # Check if within 5 sigma range
    if (abs(period - np.median(periodogram_period)) < 5 * std_dev) or (abs(period - np.median(periodogram_period)) < 4 * std_dev):
        return True, period
    else:
        return False, period
    

"""
    Finds the best lightcurve based off of CDPP within a lightcurve query
    Name:
    Parameters:
    Returns:
"""
def best_lightcurve(result, result_exposures, cadence):
    # Initialization
    lightcurve, best_lightcurve, best_cdpp = None, None, float('inf')

    # Get the data whose exposure is the desired cadence
    for i, exposure in enumerate(result_exposures):
        # Check to see if exposure matches cadence 
        if exposure.value == cadence:
            lightcurve = result[i].download().remove_nans().remove_outliers()

            # Check median flux
            median_flux = np.median(lightcurve.flux)
            if median_flux < 0 or np.isclose(median_flux, 0, atol=1e-6):
                continue

            # Normalize lightcurve 
            lightcurve = lightcurve.normalize() - 1

            # Evaluate combined differential photometric precision(CDPP)
            cdpp = lightcurve.estimate_cdpp()

            # Compare and select lightcurve with the best SNR
            if cdpp < best_cdpp:
                best_lightcurve = lightcurve
                best_cdpp = cdpp

    return best_lightcurve if best_lightcurve else lightcurve if lightcurve else None    


"""
    Append row to a CSV file
    Name:       append_to_csv()
    Parameters: 
                filename: CSV file's name 
                row: row to be added to the file
    Returns:
                None
"""
def append_to_csv(filename, row):
    # Check if file already exists
    try:
        with open(filename, 'r') as csvfile:
            pass
        file_exists = True
    except FileNotFoundError:
        file_exists = False
    
    # Open file in append mode
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ["Star", "Orbital Period(hours)"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        # Append row
        writer.writerow(row)


"""
    Event function that determines if a key was clicked
    Name:       on_key()
    Parameters: 
                event: key press event
                purpose: either doppler or noise
    Returns:
                None
"""
def on_key(event):
    valid_keys = {'y', 'n'}

    if event.key not in valid_keys:
        sys.exit("Invalid key input, select 'y' or 'n'")
    else:
        period_bool_list.append(event.key == 'y')
        print('Loading next plot ... \n')
        plt.close()