import astropy.units as u
import lightkurve as lk
import math
import matplotlib.pyplot as plt
import os
from os.path import exists
import pandas as pd

from file_editing import *
from prerun import *
from period_finding import *


def main():
    # Choose how to run
    preload = False # if you want to preload all plots before selecting periods
    autopilot = False # have the computer do all the work for you 

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
    if preload:
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
            
            # Get period at max power
            best_period = periodogram.period_at_max_power.value

            # Make period plot
            sine_fit, residuals = period_selection_plots(lightcurve, periodogram, best_period, literature_period, star_name, star_imag)
            plt.show()
            if not period_bool_list[len(period_bool_list) - 1]: continue

            # Make lightcurve effects plot
            for effect in lightcurve_effects:
                effects_selection_plot(effect, lightcurve, periodogram, best_period, sine_fit, residuals, star_name, star_imag)
                plt.show()
            
            # Check for irradidation and ellipsodial
            irradiation, ellipsodial = False, False
            if literature_period != 0.0:
                # Irradiation if literature period = best_period
                if math.isclose(np.abs(best_period - literature_period), 0, rel_tol=1e-2): # maybe change tolerance
                    irradiation = True
                elif math.isclose(np.abs(best_period / literature_period), 0.5, rel_tol=1e-2):
                    ellipsodial = True

            # Save data to csv
            curr_index = len(doppler_beaming_bool_list) - 1
            row = {'Star' : star_name, 
                   'Orbital Period(days)' : best_period,
                   'Literature Period(days)': literature_period,
                   'i Magnitude': star_imag,
                   'Eclipsing': eclipsing_bool_list[curr_index],
                   'Flares': flare_bool_list[curr_index],
                   'Irradiation': irradiation,
                   'Doppler beaming': doppler_beaming_bool_list[curr_index],
                   'Ellipsoidal': ellipsodial} # will only hit this line if the period is real
            append_to_csv(porb_filename, row)


if __name__ == '__main__':
    main()