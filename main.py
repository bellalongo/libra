import astropy.units as u
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import os
from os.path import exists
import pandas as pd
import seaborn as sns

from file_editing import *
from prerun import *
from period_finding import *


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
            best_period = select_period(lightcurve, periodogram, literature_period, star_name, star_imag)
            if not best_period:
                continue

            # Make period plot
            period_selection_plots(lightcurve, periodogram, best_period, literature_period, star_name, star_imag)

            plt.show()

            # Check if the was marked as True -> maybe make into a function
            curr_index = len(period_bool_list) - 1
            if period_bool_list[curr_index]:
                row = {"Star" : star_name, "Orbital Period(days)" : best_period}
                append_to_csv(porb_filename, row)


if __name__ == '__main__':
    main()