import lightkurve as lk
import math
import matplotlib.image as mpimg
import os
from os.path import exists
import pandas as pd
from tqdm import tqdm

from file_editing import *
from period_finding import *


star_data_filename = 'preload/all_star_data.csv'
folders = ['eclipsing_plots', 'flare_plots', 'doppler_plots'] # make sure lightcurve_effects matches below order!!!
lightcurve_effects = ['Eclipsing', 'Flares', 'Doppler beaming']

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
    # Remove star data if it already exists
    if exists(star_data_filename):
        os.remove(star_data_filename)

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
        if not lightcurve: continue 

        # Star data
        star_name = 'TIC ' + str(lightcurve.meta['TICID'])
        star_imag = row['i']
        literature_period = (row['porb']*u.hour).to(u.day).value
        period_plot_filename = 'preload/period_plots/' + star_name + '.png'

        # Check if plot already exists
        if exists(period_plot_filename):
            os.remove(period_plot_filename)
            os.remove('preload/eclipsing_plots/' + star_name + '.png')
            os.remove('preload/doppler_plots/' + star_name + '.png')
            os.remove('preload/flare_plots/' + star_name + '.png')

        # Get periodogram
        periodogram = lightcurve.to_periodogram(oversample_factor = 10, 
                                                minimum_period = (2*cadence*u.second).to(u.day).value, 
                                                maximum_period = 14)
        
        # Save period plot
        best_period = periodogram.period_at_max_power.value 
        sine_fit, residuals = period_selection_plots(lightcurve, periodogram, best_period, literature_period, star_name, star_imag)
        plt.savefig(period_plot_filename)
        plt.close()

        # Save effects plots
        for i, effect in enumerate(lightcurve_effects):
            effects_selection_plot(effect, lightcurve, periodogram, best_period, sine_fit, residuals, star_name, star_imag)
            plt.savefig('preload/' + folders[i] + '/' + star_name + '.png')
            plt.close()

        # Save star data to the csv
        row = {'Star' : star_name, 'Orbital Period(days)' : best_period, 'Literature Period(days)': literature_period, 'i Magnitude': star_imag}
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
    images = [i for i in os.listdir('preload/period_plots') if i.startswith('TIC')]

    # Load dataframe
    stars_df = pd.read_csv(star_data_filename)

    # Check if orbital period csv exists
    porb_filename = 'orbital_periods/periods.csv'
    if exists(porb_filename):
        os.remove(porb_filename)

    # Iterate through all the images
    for image in images: # MAKE SURE CORRECT STAR DATA AND THAT TIC'S FOR IMAGE AND ROW MATCH -> get csv data w/ tic
        current_image = os.path.join('preload/period_plots/', image)
        star_name, _ = os.path.splitext(image)

        # Show period select plot
        fig = plt.figure(figsize=(14, 8))
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, 'Real period')) 
        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        img = mpimg.imread(current_image)
        plt.imshow(img)
        plt.show()

        # Go to next plot if clicked 'no'
        if not period_bool_list[len(period_bool_list) - 1]: continue

        # Show each effects plot
        for i, effect in enumerate(lightcurve_effects):
            effect_filename = 'preload/' + folders[i] + '/' + star_name + '.png'
            fig = plt.figure(figsize=(14, 8))
            cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, effect)) 
            plt.axis('off')
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            img = mpimg.imread(effect_filename)
            plt.imshow(img)
            plt.show()
        
        # Get star data from csv
        star_row = stars_df.loc[stars_df['Star'] == star_name]

        # Check for irradidation and ellipsodial
        irradiation, ellipsodial = False, False
        literature_period = star_row['Literature Period(days)'].values[0]
        best_period = star_row['Orbital Period(days)'].values[0]
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
                'i Magnitude': star_row['i Magnitude'].values[0],
                'Eclipsing': eclipsing_bool_list[curr_index],
                'Flares': flare_bool_list[curr_index],
                'Irradiation': irradiation,
                'Doppler beaming': doppler_beaming_bool_list[curr_index],
                'Ellipsoidal': ellipsodial} # will only hit this line if the period is real
        append_to_csv(porb_filename, row)