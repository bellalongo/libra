import lightkurve as lk
import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import lmfit
from filtering import *


# Define SDSS query dataframes
df = pd.read_csv('testing/query_data/comma_test_query.csv')
filterd_df = df[['iau_name', 'i', 'porb', 'porbe']]
porb_df = filterd_df[filterd_df['porb'] != 0].reset_index()
no_porb_df = filterd_df[filterd_df['porb'] == 0].reset_index()

# Remove csv file with old OB calculations (use ones with calculated period first)
cadence = 120

# Iterate through all rows with an orbital period
for i, row in porb_df.iterrows():
    # Pull data for that star
    try:
        result = lk.search_lightcurve(row['iau_name'], mission = 'TESS')
        result_exposures = result.exptime
    except Exception as e:
        print(f"Error for {row['iau_name']}: {e} \n")
        continue

    # Get the best lightcurve
    lightcurve = best_lightcurve(result, result_exposures, cadence)
    if not lightcurve: continue # check if there was a result with the cadence needed

    # Period bounds
    min_period_days = (2*cadence) / (60*60*24) # 2 * cadence in days
    max_period_days = 14 # 14 days
    
    # Get periodogram
    periodogram = lightcurve.to_periodogram(oversample_factor = 10, minimum_period = min_period_days) # units are days

    # Period
    is_real, period = is_real_period(periodogram)

    # Define folded and binned lightcurve
    phase_lightcurve = lightcurve.fold(period = periodogram.period_at_max_power)
    binned_lightcurve = phase_lightcurve.bin(4*u.min) 

    # Define phase, flux, and lower and upper flux bounds 
    binned_phase = binned_lightcurve.phase.value
    binned_flux = binned_lightcurve.flux.value
    binned_flux_lower_err = binned_lightcurve.flux - binned_lightcurve.flux_err
    binned_flux_upper_err = binned_lightcurve.flux + binned_lightcurve.flux_err

    # Lightcurve data
    time = lightcurve.time.value
    flux = lightcurve.flux.value
    flux_lower_err = lightcurve.flux - lightcurve.flux_err
    flux_upper_err = lightcurve.flux + lightcurve.flux_err

    # Make an lmfit object and fit it
    max_power = max(periodogram.power.value)
    model = lmfit.Model(sine_wave)
    params = model.make_params(amplitude=max_power, frequency = 1/periodogram.period_at_max_power.value, phase=0.0)
    result = model.fit(flux, params, x=time)

    # Plot the periodogram 
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    plt.subplots_adjust(hspace=0.3)
    axs[0, 0].set_title('Periodogram', fontsize=12)
    axs[0, 0].set_xlabel('Period (hours)', fontsize=10)
    axs[0, 0].set_ylabel('Power', fontsize=10)
    axs[0, 0].plot(periodogram.period, periodogram.power)
    axs[0, 0].axvline(x=row['porb']/24, color = 'red', ls = 'dotted', label = 'Literature period')
    axs[0, 0].axvline(x=period, color = 'blue', ls = 'dotted', label = 'Period at max power')
    axs[0, 0].set_xscale('log') 
    axs[0, 0].legend()

    # Plot binned lightcurve
    axs[1, 0].set_title('Folded on Period at Max Power', fontsize=12)
    axs[1, 0].set_xlabel('Phase', fontsize = 10)
    axs[1, 0].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 0].vlines(binned_phase, binned_flux_lower_err, binned_flux_upper_err, lw=1)

    # Plot the fitted sin wave
    axs[0, 1].set_title('Lightcurve', fontsize=12)
    axs[0, 1].set_xlabel('Time (hours)', fontsize = 10)
    axs[0, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[0, 1].vlines(time, flux_lower_err, flux_upper_err, lw=2)
    axs[0, 1].plot(time, result.best_fit, color= 'black', label = 'Fitted Sine Wave')
    axs[0, 1].set_xlim(min(time), min(time) + 1)
    axs[0, 1].legend()

    # Subtract sine wave
    flare_data = flux - result.best_fit
    axs[1, 1].set_title('Flux - Sine Wave', fontsize=12)
    axs[1, 1].set_xlabel('Time (hours)', fontsize = 10)
    axs[1, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 1].plot(time, flare_data)
    axs[1, 1].set_xlim(min(time), min(time) + 1)

    plt.show()