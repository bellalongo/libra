import lightkurve as lk
import lmfit
import matplotlib.image as mpimg
import os
from os.path import exists
import pandas as pd
from tqdm import tqdm

from file_editing import *
from period_finding import *


star_data_filename = 'preload/all_star_data.csv'
folders = ['transit_plots', 'ellipsoidal_plots', 'radiation_plots', 'doppler_plots']
lightcurve_effects = ['Transits', 'Ellipsoidal', 'Radiation', 'Doppler beaming']


"""
    Saves images of all plots to be iterated through later
    Name:       preload_plots()
    Parameters: 
                df: pandas dataframe holding SDSS query data
                cadence: desied cadence
    Returns:
                None
"""
def preload_plots(df, cadence):
    # Iterate through all rows with an orbital period
    for _, row in tqdm(df.iterrows(), desc="Processing lightcurves", total = len(df)):
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
        period_plot_filename = 'preload/period_plots/' + star_name + '.png'

        # Check if plot already exists
        if exists(period_plot_filename):
            os.remove(period_plot_filename)
            os.remove('preload/transit_plots/' + star_name + '.png')
            os.remove('preload/ellipsoidal_plots/' + star_name + '.png')
            os.remove('preload/radiation_plots/' + star_name + '.png')
            os.remove('preload/doppler_plots/' + star_name + '.png')

        # Get periodogram
        periodogram = lightcurve.to_periodogram(oversample_factor = 10, 
                                                minimum_period = (2*cadence*u.second).to(u.day).value, 
                                                maximum_period = 14)
        
        # Save period plot
        best_period = periodogram.period_at_max_power.value 
        binned_lightcurve, sine_fit, residuals = period_selection_plots(lightcurve, periodogram, best_period, literature_period, star_name, star_imag)
        plt.savefig(period_plot_filename)
        plt.clf()

        # Save effects plots
        for i, effect in enumerate(lightcurve_effects):
                effects_selection_plot(effect, lightcurve, binned_lightcurve, sine_fit, residuals, star_name)
                plt.savefig('preload/' + folders[i] + '/' + star_name + '.png')
                plt.clf()

        # Save star data to the csv
        row = {"Star" : star_name, "Orbital Period(days)" : best_period}
        append_to_csv(star_data_filename, row)


"""
    Loads each plot which will then be used to determine if the period is real or not
    Name:       load_plots()
    Parameters: 
                None
    Returns:
                None
"""
def load_plots():
    # Load all plot images in the directory
    images = [i for i in os.listdir('preload/plots')]

    # Load dataframe
    stars_df = pd.read_csv('preload/star_data.csv')

    # Check if orbital period csv exists
    porb_filename = 'orbital_periods/periods.csv'
    if exists(porb_filename):
        os.remove(porb_filename)

    # Iterate through all the images
    for i, image in enumerate(images): # MAKE SURE CORRECT STAR DATA AND THAT TIC'S FOR IMAGE AND ROW MATCH
        current_image = os.path.join('preload/plots', image)
        image_name, _ = os.path.splitext(image)

        # Show the image
        fig = plt.figure(figsize=(14, 8))
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, 'Real period')) # MAKE SURE I WORK
        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        img = mpimg.imread(current_image)
        plt.imshow(img)
        plt.show()

        # Check if it was marked as real
        if period_bool_list[i]: # CHANGE DATA THAT IS SAVED HERE
            star_name = stars_df.iloc[i]['Star']
            period = stars_df.iloc[i]['Orbital Period(days)']
            row = {"Star" : star_name, "Orbital Period(days)" : period}
            append_to_csv(porb_filename, row)