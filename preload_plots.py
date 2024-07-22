import csv
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import os
from os.path import exists
import pandas as pd


class PreloadPlots(object):
    def __init__(self, preload, porb_dir):
        self.preload = preload

        # Final data directory
        self.porb_dir = porb_dir

        # Plot directories
        self.preload_dir = 'preload/'
        self.doppler_dir = self.preload_dir + 'doppler_plots/'
        self.eclipsing_dir = self.preload_dir + 'eclipsing_plots/' 
        self.flare_dir = self.preload_dir + 'flare_plots/'     
        self.period_dir = self.preload_dir + 'period_plots/' 

        # Preload data directories
        self.preload_data_dir = self.preload_dir + 'preload_data.csv'

        # Lightcurve effects
        self.effects = ['Doppler beaming', 'Eclipsing', 'Flares']

        # Initialize a boolean to determine if the period is real
        self.is_real_period = False

        # List of effects found in the lightcurve data
        self.effects_found = [] # [Eclipsing, Doppler beaming, Flares, Irradiation, Ellipsodial]


    def create_preload_row(self, lightcurve_data):
        """

        """
        row = {
            'TIC': lightcurve_data.name,
            'Orbital period (days)': lightcurve_data.period_at_max_power,
            'Literature period (days)': lightcurve_data.lit_period, 
            'i Magnitude': lightcurve_data.imag,
        }

        return row
    

    def create_row(self, row):
        """
            Creates a row of the current lightcurve's date to be added to the porb_dir
            Name:       eclipsing_plot()
            Parameters:
                        row: current lightcurve's row in the preload_df
            Returns:
                        None
        """
        row = {
            'TIC': row['TIC'].values[0],
            'Orbital period (days)': row['Orbital period (days)'].values[0],
            'Literature period (days)': row['Literature period (days)'].values[0], 
            'i Magnitude': row['i Magnitude'].values[0],
            'Eclipsing': self.effects_found[0],
            'Doppler beaming': self.effects_found[1],
            'Flares': self.effects_found[2],
            'Irradiation': self.effects_found[3],
            'Ellipsoidal': self.effects_found[4]
        }

        return row


    def save_plot(self, plot_type, tic):
        """

        """
        # Get plot directory
        plot_dir = self.create_dir(plot_type, tic)

        # Check if directory exists
        if not exists(plot_dir):
            plt.savefig(plot_dir)
            plt.close()
        else:
            print(f'{plot_type} plot already exists for {tic}')


    def create_dir(self, plot_type, tic):
        """

        """
        # Doppler plot directory
        if plot_type == 'Doppler beaming':
            plot_dir = self.doppler_dir + tic + '_doppler.png'

        # Eclipsing plot directory
        elif plot_type == 'Eclipsing':
            plot_dir = self.eclipsing_dir + tic + '_eclipsing.png'

        # Flare plot directory
        elif plot_type == 'Flares':
            plot_dir = self.flare_dir + tic + '_flares.png'

        # Period directory
        elif plot_type == 'Period':
            plot_dir = self.period_dir + tic + '_period.png'

        return plot_dir
    

    def save_period(self, lightcurve_data):
        """

        """
        # See if file already exists
        try:
            with open(self.preload_data_dir, 'r') as csvfile:
                pass
            file_exists = True
        except FileNotFoundError:
            file_exists = False

        # Create the row
        row = self.create_preload_row(lightcurve_data)
        
        # Open file in append mode
        with open(self.preload_data_dir, 'a', newline='') as csvfile:
            fieldnames = [
                'TIC', 
                'Orbital period (days)', 
                'Literature period (days)', 
                'i Magnitude', 'Eclipsing', 
                'Doppler beaming', 
                'Flares', 
                'Irradiation', 
                'Ellipsoidal'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames = fieldnames)

            # Write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            # Append row
            writer.writerow(row)


    def add_to_csv(self, row):
        """
            Adds the lightcurve's row to the porb_dir
            Name:       eclipsing_plot()
            Parameters:
                        None
            Returns:
                        None
        """
        # See if file already exists
        try:
            with open(self.porb_dir, 'r') as csvfile:
                pass
            file_exists = True
        except FileNotFoundError:
            file_exists = False

        # Create the row
        row = self.create_row(row)
        
        # Open file in append mode
        with open(self.porb_dir, 'a', newline='') as csvfile:
            fieldnames = [
                'TIC', 
                'Orbital period (days)', 
                'Literature period (days)', 
                'i Magnitude', 'Eclipsing', 
                'Doppler beaming', 
                'Flares', 
                'Irradiation', 
                'Ellipsoidal'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames = fieldnames)

            # Write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            # Append row
            writer.writerow(row)


    def get_tics(self):
        """

        """
        # Get star name for every period plot
        plots = [plot for plot in os.listdir('preload/period_plots') if plot.startswith('TIC')]
        tics = [plot.replace('_period.png', '') for plot in plots]

        return tics
    

    def period_plot(self, tic):
        """

        """
        # Get the plot directory
        period_plot = self.create_dir('Period', tic)

        # Show the period plot
        fig = plt.figure(figsize=(14, 8))
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: self.on_key(event, 'Period selection')) 
        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        img = mpimg.imread(period_plot)
        plt.imshow(img)
        plt.show()


    def effects_plots(self, tic):
        """

        """
        # Iterate through each effect
        for effect in self.effects:
            # Get the plot directory
            plot_dir = self.create_dir(effect, tic)

            fig = plt.figure(figsize=(14, 8))
            cid = fig.canvas.mpl_connect('key_press_event', lambda event: self.on_key(event, 'Effects selection')) 
            plt.axis('off')
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            img = mpimg.imread(plot_dir)
            plt.imshow(img)
            plt.show()


    def irradiation_ellipsodial_check(self, row):
        """
            Checks if the lightcurve shows irradiation or ellipsodial effects 
            Name:       irradiation_ellipsodial_check()
            Parameters:
                        row: current tic's row in the df
            Returns:
                        None
        """
        # Irradiation of literature period = period at max power
        if math.isclose(np.abs(row['Literature period (days)'].values[0] - row['Orbital period (days)'].values[0]), 0, rel_tol=1e-2):
            self.effects_found.append(True)
        else:
            self.effects_found.append(False)

        # Eclipsing if the literature period is twice the period at max power -> check me
        if math.isclose(np.abs(row['Literature period (days)'].values[0] - row['Orbital period (days)'].values[0]), 2, rel_tol=1e-2):
            self.effects_found(True)
        else:
            self.effects_found.append(False)


    def run(self):
        """

        """
        # Get all of the tics in the directory
        tics = self.get_tics()

        # Load the saved star data
        preload_df = pd.read_csv(self.preload_data_dir)

        # Check if orbital period csv exists
        porb_filename = 'orbital_periods/periods.csv'
        if exists(porb_filename):
            os.remove(porb_filename)

        # Iterate through every star
        for tic in tics:
            # Load the period plot
            self.period_plot(tic)

            # Check if the period is real
            if not self.is_real_period: continue

            # Load effects plots
            self.effects_found = []
            self.effects_plots(tic)

            # Get the current row of the df
            row = preload_df.loc[preload_df['TIC'] == tic]

            # Check for irradiatin and ellipsodial
            self.irradiation_ellipsodial_check(row)

            # Save the data
            self.add_to_csv(row)


    def on_key(self, event, purpose):
        """
            Event function that determines if a key was clicked
            Name:       on_key()
            Parameters: 
                        event: key press event
                        purpose: either 'Period selection' or 'Effects selection'
            Returns:
                        None
        """
        y_n_keys = {'y', 'n'}

        if event.key not in y_n_keys:
            print("Invalid key input, select 'y' or 'n'")

        else:
            if purpose == 'Period selection':

                if event.key == 'n':
                    print('Period is not real, loading next plot ... \n')
                else:
                    self.is_real_period = True

            elif purpose == 'Effects selection':
                self.effects_found.append(event.key == 'y') 

            plt.close()