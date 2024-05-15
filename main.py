# Necessary imports
import lightkurve as lk
import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys


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
    star_result = lk.search_lightcurve(row['iau_name'], mission = 'TESS')
    star_result_exposures = star_result.exptime

    # Get the data whose exposure is 120
    for i, exposure in enumerate(star_result_exposures):
        # Check to see if exposure matches cadence 
        if exposure.value == cadence:
            star_lightcurve = star_result[i].download().remove_nans().remove_outliers().normalize() - 1
            min_period_days = (2*star_result[i].exptime.value)[0] / (60*60*24) # 2 * cadence in days
            max_period_days = 14 # 14 days
            break
    
    # Get periodogram
    star_periodogram = star_lightcurve.to_periodogram(oversample_factor = 10, minimum_period = min_period_days)

    # Calculate if the period is 'real'
    period_at_max_power = star_periodogram.period_at_max_power.value 
    max_power = star_periodogram.max_power.value 
    std_dev = np.std(star_periodogram.power)

    # Calculate the "real orbital period range"
    five_sigma_range = 5 * std_dev
    four_sigma_range = 4 * std_dev

    # Check if the maximum power is above the 5-sigma range
    if max_power > five_sigma_range:
        print(f"The period at max power {period_at_max_power} days is likely real (above 5-sigma range)")
    else:
        print(f"The period at max power {period_at_max_power} days is likely NOT real (below 5-sigma range)")


    star_periodogram.plot(view = 'period', scale = 'log', unit = u.hr)
    plt.title('Lombe-Scargle Periodogram')
    plt.legend()
    plt.show()


    # sys.exit()

