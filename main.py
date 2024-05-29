import astropy.units as u
import lightkurve as lk
import lmfit
import matplotlib.pyplot as plt
import numpy as np
import os
from os.path import exists
import pandas as pd
import seaborn as sns

from file_editing import *
from prerun import *
from refining import *


def main():
    # Choose how to run
    preload = False

    # Cadence wanting to use
    cadence = 120

    # Filenames
    csv_filename = 'wdss_data.csv'
    porb_filename = 'orbital_periods/periods.csv'

    # Check if raw data has been converted
    if not exists(csv_filename):
        commaize('raw_wdss_data.csv', csv_filename)
    # Check if periods were already calculated
    elif exists(porb_filename):
        os.remove(porb_filename) # maybe add somehow to pick up where left off

    # Define SDSS query dataframes
    df = pd.read_csv(csv_filename)
    df = df[['iau_name', 'i', 'porb', 'porbe']] 

    # Check for preload
    if preload: # adjust how im run
        preload_plots(df, cadence)
        load_plots()
    else:
        # Iterate through all rows with an orbital period
        for _, row in df.iterrows():
            # Pull data for that star
            try:
                result = lk.search_lightcurve(row['iau_name'], mission = 'TESS')
                result_exposures = result.exptime
            except Exception as e:
                print(f"Error for {row['iau_name']}: {e} \n")
                continue

            lightcurve = append_lightcurves(result, result_exposures, cadence)
            if not lightcurve: continue # check if there was a result with the cadence needed

            # Star data
            star_name = 'TIC ' + str(lightcurve.meta['TICID'])
            star_imag = row['i']
            literature_period = (row['porb']*u.hour).to(u.day).value
            
            # Get periodogram
            periodogram = lightcurve.to_periodogram(oversample_factor = 10, 
                                                    minimum_period = (2*cadence*u.second).to(u.day).value, 
                                                    maximum_period = 14)
            
            # Choose the best period candidate
            best_period = select_period(lightcurve, periodogram, literature_period, cadence, star_name, star_imag)
            if not best_period:
                continue

            # Determine if the period is probable
            is_real = is_real_period(periodogram, best_period)

            # Define folded and binned lightcurve
            phase_lightcurve = lightcurve.fold(period = best_period)
            bin_value = find_bin_value(phase_lightcurve, cadence)
            binned_lightcurve = phase_lightcurve.bin(bin_value*u.min) 

            # Lightcurve data
            time = lightcurve.time.value
            flux = lightcurve.flux.value

            # Make an lmfit object and fit it
            model = lmfit.Model(sine_wave)
            params = model.make_params(amplitude=max(periodogram.power.value) , # FIX ME!!!!!! to match girilie found 
                                    frequency = 1/periodogram.period_at_max_power.value, 
                                    phase=0.0)
            result = model.fit(flux, params, x=time)

            # Plot basics
            sns.set_theme()
            fig, axs = plt.subplots(2, 2, figsize=(14, 8))
            plt.subplots_adjust(hspace=0.35)
            plt.suptitle(fr"Press the key 'y' if the period {np.round(best_period, 3)} days is real, 'n' if not", fontweight = 'bold')
            fig.text(0.5, 0.05, f'{star_name}', ha='center', fontsize=16, fontweight = 'bold')
            fig.text(0.5, 0.02, fr'$i_{{\text{{mag}}}}={star_imag}$', ha='center', fontsize=12, fontweight = 'bold')
            cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, 'Real period'))
            if is_real:
                fig.text(0.5, 0.928, 'Note: The period is over 5 sigma, so MIGHT be real', ha='center', fontsize=12, style = 'italic')
            else:
                fig.text(0.5, 0.928, 'Note: The period is under 5 sigma, so might NOT be real', ha='center', fontsize=12, style = 'italic')

            # Plot the periodogram 
            axs[0, 0].set_title('Periodogram', fontsize=12)
            axs[0, 0].set_xlabel(r'$P_{\text{orb}}$ (days)', fontsize=10)
            axs[0, 0].set_ylabel('Power', fontsize=10)
            axs[0, 0].plot(periodogram.period, periodogram.power)
            if literature_period != 0.0: axs[0,0].axvline(x=literature_period, color = '#A30015', label = fr'Literature $P_{{\text{{orb}}}}={np.round(literature_period, 2)}$ days')
            axs[0, 0].axvline(x=best_period, color = '#141B41', lw = 2, label = fr'$P_{{\text{{orb, best}}}}={np.round(best_period, 2)}$ days')
            axs[0, 0].set_xscale('log') 
            axs[0, 0].legend(loc = 'upper left')

            # Plot binned lightcurve
            axs[1, 0].set_title(r'Folded on $P_{\text{orb, best}}$', fontsize=12)
            axs[1, 0].set_xlabel('Phase', fontsize = 10)
            axs[1, 0].set_ylabel('Normalized Flux', fontsize = 10)
            axs[1, 0].vlines(binned_lightcurve.phase.value, 
                            binned_lightcurve.flux - binned_lightcurve.flux_err, 
                            binned_lightcurve.flux + binned_lightcurve.flux_err, lw=2)

            # Plot the fitted sin wave
            axs[0, 1].set_title('Lightcurve', fontsize=12)
            axs[0, 1].set_xlabel('Time (days)', fontsize = 10)
            axs[0, 1].set_ylabel('Normalized Flux', fontsize = 10)
            axs[0, 1].vlines(lightcurve.time.value, 
                            lightcurve.flux - lightcurve.flux_err, 
                            lightcurve.flux + lightcurve.flux_err, lw=2)
            axs[0, 1].plot(time, result.best_fit, color= '#051923', label = 'Fitted Sine Wave')
            axs[0, 1].set_xlim(min(time), min(time) + 1)
            axs[0, 1].legend()

            # Subtract sine wave
            subtracted_data = flux - result.best_fit
            axs[1, 1].set_title('Flux - Fitted Sine Wave', fontsize=12)
            axs[1, 1].set_xlabel('Time (days)', fontsize = 10)
            axs[1, 1].set_ylabel('Normalized Flux', fontsize = 10)
            axs[1, 1].plot(time, subtracted_data) # maybe make me into scatter
            axs[1, 1].set_xlim(min(time), min(time) + 1)

            plt.show()

            # Check if the was marked as True -> maybe make into a function
            curr_index = len(period_bool_list) - 1
            if period_bool_list[curr_index]:
                row = {"Star" : star_name, "Orbital Period(days)" : best_period}
                append_to_csv(porb_filename, row)


if __name__ == '__main__':
    main()