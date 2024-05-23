import astropy.units as u
import lightkurve as lk
import lmfit
import matplotlib.pyplot as plt
import numpy as np
import os
from os.path import exists
import pandas as pd
import seaborn as sns

from filtering import *


def main():
    # Filenames
    porb_filename = 'orbital_periods/porb_periods.csv'
    no_porb_filename = 'orbital_periods/no_porb_periods.csv'

    # Remove previous csv if exists
    if exists(porb_filename):
        os.remove(porb_filename)

    # Define SDSS query dataframes
    df = pd.read_csv('testing/query_data/comma_test_query.csv')
    filterd_df = df[['iau_name', 'i', 'porb', 'porbe']] # update at some point so it uses just filtereddf
    porb_df = filterd_df[filterd_df['porb'] != 0].reset_index()
    no_porb_df = filterd_df[filterd_df['porb'] == 0].reset_index() 

    # Cadence wanting to use
    cadence = 120

    # Iterate through all rows with an orbital period
    for _, row in porb_df.iterrows():
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
        
        # Get periodogram
        periodogram = lightcurve.to_periodogram(oversample_factor = 10, 
                                                minimum_period = (2*cadence) / (60*60*24), 
                                                maximum_period = 14)
        
        # Choose the best period candidate
        period = select_period(lightcurve, periodogram, row)
        if not period:
            continue

        # Determine if the period is probable
        is_real, period = is_real_period(periodogram, period)

        # Define folded and binned lightcurve
        phase_lightcurve = lightcurve.fold(period = period)
        binned_lightcurve = phase_lightcurve.bin(4*u.min) 

        # Lightcurve data
        time = lightcurve.time.value
        flux = lightcurve.flux.value

        # Make an lmfit object and fit it
        model = lmfit.Model(sine_wave)
        params = model.make_params(amplitude=max(periodogram.power.value), 
                                   frequency = 1/periodogram.period_at_max_power.value, 
                                   phase=0.0)
        result = model.fit(flux, params, x=time)

        # Plot basics
        sns.set_theme()
        fig, axs = plt.subplots(2, 2, figsize=(12, 8))
        plt.subplots_adjust(hspace=0.35)
        plt.suptitle(f"Press 'y' if the orbital period {np.round(period, 3)} days is real, 'n' if not", fontweight = 'bold')
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, 'Real period'))
        if is_real:
            fig.text(0.5, 0.94, 'Note: The period is over 5 sigma, so MIGHT be real', ha='center', fontsize=10, style = 'italic')
        else:
            fig.text(0.5, 0.94, 'Note: The period is under 5 sigma, so might NOT be real', ha='center', fontsize=10, style = 'italic')

        # Plot the periodogram 
        axs[0, 0].set_title('Periodogram', fontsize=12)
        axs[0, 0].set_xlabel('Period (days)', fontsize=10)
        axs[0, 0].set_ylabel('Power', fontsize=10)
        axs[0, 0].plot(periodogram.period, periodogram.power)
        axs[0, 0].axvline(x=period, color = '#F0803C', ls = 'dotted', lw = 3, label = 'Period at max power')
        axs[0,0].axvline(x=row['porb']/24, color = 'red', label = 'Literature period')
        axs[0, 0].set_xscale('log') 
        axs[0, 0].legend()

        # Plot binned lightcurve
        axs[1, 0].set_title('Folded on Period at Max Power', fontsize=12)
        axs[1, 0].set_xlabel('Phase', fontsize = 10)
        axs[1, 0].set_ylabel('Normalized Flux', fontsize = 10)
        axs[1, 0].vlines(binned_lightcurve.phase.value, 
                         binned_lightcurve.flux - binned_lightcurve.flux_err, 
                         binned_lightcurve.flux + binned_lightcurve.flux_err, lw=2)

        # Plot the fitted sin wave
        axs[0, 1].set_title('Lightcurve', fontsize=12)
        axs[0, 1].set_xlabel('Time', fontsize = 10)
        axs[0, 1].set_ylabel('Normalized Flux', fontsize = 10)
        axs[0, 1].vlines(lightcurve.time.value, 
                         lightcurve.flux - lightcurve.flux_err, 
                         lightcurve.flux + lightcurve.flux_err, lw=2)
        axs[0, 1].plot(time, result.best_fit, color= '#F0803C', label = 'Fitted Sine Wave')
        axs[0, 1].set_xlim(min(time), min(time) + 1)
        axs[0, 1].legend()

        # Subtract sine wave
        subtracted_data = flux - result.best_fit
        axs[1, 1].set_title('Flux - Sine Wave', fontsize=12)
        axs[1, 1].set_xlabel('Time', fontsize = 10)
        axs[1, 1].set_ylabel('Normalized Flux', fontsize = 10)
        axs[1, 1].plot(time, subtracted_data)
        axs[1, 1].set_xlim(min(time), min(time) + 1)

        plt.show()

        # Check if the was marked as
        curr_index = len(period_bool_list) - 1
        if period_bool_list[curr_index]:
            # Row data
            star_name = 'TIC ' + str(lightcurve.meta['TICID'])
            row = {"Star" : star_name, "Orbital Period(hours)" : period}

            # Append to csv
            append_to_csv(porb_filename, row)
            

if __name__ == '__main__':
    main()