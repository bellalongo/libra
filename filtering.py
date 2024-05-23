import astropy.units as u
import csv
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import sys


# Global variables
period_bool_list = []
best_period_list = []


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
def is_real_period(periodogram, period):
    # Remove NaNs from the periodogram
    nan_mask = ~np.isnan(periodogram.power)
    periodogram_power = periodogram.power[nan_mask]
    periodogram_period = periodogram.period[nan_mask].value
    
    # Calculate period at max power
    std_dev = np.std(periodogram_power)

    # Check if within 5 sigma range
    if (abs(period - np.median(periodogram_period)) > 5 * std_dev) or (abs(period - np.median(periodogram_period)) > 4 * std_dev):
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


def select_period(lightcurve, periodogram, row):
    period = periodogram.period_at_max_power.value 

    # Plot basics
    sns.set_style("darkgrid")
    sns.set_theme(rc={'axes.facecolor':'#F8F5F2'})
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    plt.subplots_adjust(hspace=0.35)
    plt.suptitle(f"Press the number corresponding with the best period candidate (1,2,3)", fontweight = 'bold') # add option NONE
    fig.text(0.5, 0.94, "If none are good, press 'n'", ha='center', fontsize=12, fontweight = 'bold')
    cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, 'Period selection'))

    # Plot the periodogram 
    axs[0, 0].set_title('Periodogram', fontsize=12)
    axs[0, 0].set_xlabel('Period (days)', fontsize=10)
    axs[0, 0].set_ylabel('Power', fontsize=10)
    axs[0, 0].plot(periodogram.period, periodogram.power, color = '#4B644A')
    axs[0, 0].axvline(x=row['porb']/24, color = '#4F000B', label = 'Literature period')
    axs[0, 0].axvline(x=period, color = '#D36135', ls = 'solid', lw = 2, label = 'Period at max power')
    axs[0, 0].axvline(x=period/2, color = '#DD882C', ls = 'dashed', lw = 2, label = '1/2 * Period at max power')
    axs[0, 0].axvline(x=2*period, color = '#E3BE4F', ls = 'dashed', lw = 2, label = '2 * Period at max power')
    axs[0, 0].set_xscale('log') 
    axs[0, 0].legend(loc = 'upper left')

    # Fold on period at 1/2 * max power
    phase_lightcurve = lightcurve.fold(period = periodogram.period_at_max_power/2)
    binned_lightcurve = phase_lightcurve.bin(4*u.min) 
    axs[1, 0].set_title('PLOT 1: Folded on Period at 1/2 * Max Power', fontsize=12)
    axs[1, 0].set_xlabel('Phase', fontsize = 10)
    axs[1, 0].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 0].vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#DD882C', lw=2)
    
    # Fold on max power
    phase_lightcurve = lightcurve.fold(period = periodogram.period_at_max_power)
    binned_lightcurve = phase_lightcurve.bin(4*u.min) 
    axs[0, 1].set_title('PLOT 2: Folded on Period at Max Power', fontsize=12)
    axs[0, 1].set_xlabel('Phase', fontsize = 10)
    axs[0, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[0, 1].vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#D36135', lw=2)
    
    # Fold on 2* max power
    phase_lightcurve = lightcurve.fold(period = 2*periodogram.period_at_max_power)
    binned_lightcurve = phase_lightcurve.bin(4*u.min) 
    axs[1, 1].set_title('PLOT 3: Folded on Period at 2 * Max Power', fontsize=12)
    axs[1, 1].set_xlabel('Phase', fontsize = 10)
    axs[1, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 1].vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#E3BE4F', lw=2)
    
    plt.show()

    # Check which plot was selected
    curr_index = len(best_period_list) - 1
    if best_period_list[curr_index] == '1':
        return period/2
    elif best_period_list[curr_index] == '2':
        return period
    elif best_period_list[curr_index] == '3':
        return 2*period
    else:
        return False


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
def on_key(event, purpose):
    real_period_keys = {'y', 'n'}
    period_selection_keys = {'1', '2', '3', 'n'}

    if purpose == 'Period selection':
        if event.key not in period_selection_keys:
            sys.exit("Invalid key input, select '1', '2', '3', or 'n'")
        else:
            best_period_list.append(event.key)
            print(f'Selected plot {event.key}')
            plt.close()
    elif purpose == 'Real period':
        if event.key not in real_period_keys:
            sys.exit("Invalid key input, select 'y' or 'n'")
        else:
            period_bool_list.append(event.key == 'y')
            print('Loading next plot ... \n')
            plt.close()
    else:
        sys.exit("Invalid purpose, select 'Period selection' or 'Real period'")