import numpy as np


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
        print(f'It is LIKELY that the orbital period {period} days is real')
        return True, period
    else:
        print(f'It is NOT likely that the orbital period {period} days is real')
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