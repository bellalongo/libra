import matplotlib.pyplot as plt
from os.path import exists


class PreloadPlots(object):
    def __init__(self, preload):
        self.preload = preload

        # Plot directories
        self.preload_dir = 'preload/'
        self.doppler_dir = self.preload_dir + 'doppler_plots/'
        self.eclipsing_dir = self.preload_dir + 'eclipsing_plots/' 
        self.flare_dir = self.preload_dir + 'flare_plots/'     
        self.period_dir = self.preload_dir + 'period_plots/' 

        # Preload data directories
        self.data_dir = 'stars_periods.csv'


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