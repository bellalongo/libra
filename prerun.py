import lightkurve as lk
import lmfit
import matplotlib.image as mpimg
import os
from os.path import exists
import pandas as pd
from tqdm import tqdm

from file_editing import *
from refining import *


# Global variables
preload_period_bool_list = []


def preload_plots(df, cadence):
    # Initialize csv where stores all of the star's data
    star_data_filename = 'preload/star_data.csv'

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
        plot_filename = 'preload/plots/' + star_name + '.png'

        # Check if plot already exists
        if exists(plot_filename):
            continue

        # Get periodogram
        periodogram = lightcurve.to_periodogram(oversample_factor = 10, 
                                                minimum_period = (2*cadence*u.second).to(u.day).value, 
                                                maximum_period = 14)
        
        # Determine if the period is probable
        best_period = periodogram.period_at_max_power.value 
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

        # Save plot
        plt.savefig(plot_filename)
        plt.clf()

        # Save star data to the csv
        row = {"Star" : star_name, "Orbital Period(days)" : best_period}
        append_to_csv(star_data_filename, row)


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
    for i, image in enumerate(images):
        current_image = os.path.join('preload/plots', image)
        image_name, _ = os.path.splitext(image)

        # Show the image
        fig = plt.figure(figsize=(14, 8))
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: prerun_onkey(event))
        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        img = mpimg.imread(current_image)
        plt.imshow(img)
        plt.show()

        # Check if it was marked as real
        if preload_period_bool_list[i]:
            star_name = stars_df.iloc[i]['Star']
            period = stars_df.iloc[i]['Orbital Period(days)']
            row = {"Star" : star_name, "Orbital Period(days)" : period}
            append_to_csv(porb_filename, row)


"""
    Event function that determines if a key was clicked
    Name:       on_key()
    Parameters: 
                event: key press event
                purpose: either doppler or noise
    Returns:
                None
"""
def prerun_onkey(event):
    period_keys = {'y', 'n'}

    if event.key not in period_keys:
        print("Invalid key input, select 'y' or 'n'")
    else:
        preload_period_bool_list.append(event.key == 'y')
        print('Loading next plot ... \n')
        plt.close()