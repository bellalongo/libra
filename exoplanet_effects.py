import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import seaborn as sns


class ExoplanetEffects(object):
    def __init__(self, lightcurve_data, orb_calculator):
        self.lightcurve_data = lightcurve_data
        self.orb_calculator = orb_calculator

        # List of the possible effects to be found 
        self.effects = ['Eclipsing', 'Doppler beaming', 'Flares']

        # List of effects found in the lightcurve data
        self.effects_found = [] # [Eclipsing, Doppler beaming, Flares, Irradiation, Ellipsodial]

        # Iterate through all effects
        for effect in self.effects:
            self.effects_plots(effect)
            plt.show()
        
        # Check for irradiation and ellispodial
        self.irradiation_ellipsodial_check()


    def irradiation_ellipsodial_check(self):
        """
            Checks if the lightcurve shows irradiation or ellipsodial effects 
            Name:       irradiation_ellipsodial_check()
            Parameters:
                        None
            Returns:
                        None
        """
        # Irradiation of literature period = period at max power
        if math.isclose(np.abs(self.lightcurve_data.lit_period - self.lightcurve_data.period_at_max_power), 0, rel_tol=1e-2):
            self.effects_found.append(True)
        else:
            self.effects_found.append(False)

        # Eclipsing if the literature period is twice the period at max power -> check me
        if math.isclose(np.abs(self.lightcurve_data.lit_period - self.lightcurve_data.period_at_max_power), 2, rel_tol=1e-2):
            self.effects_found(True)
        else:
            self.effects_found.append(False)
             

    def eclipsing_plot(self, fig):
        """
            Presents a plot of the lightcurve with sine fit, periodogram, and binned lightcurve to be used to see if eclisping 
            Name:       eclipsing_plot()
            Parameters:
                        fig: current plot figure 
            Returns:
                        None
        """
        # Plot title and axis
        plt.suptitle("Press 'y' if there are eclipses, 'n' if not", fontweight = 'bold')

        # Plots for Eclipsing
        gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1]) 
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        plt.subplots_adjust(hspace=0.5)

        # Plot lightcurve with sine fit
        self.orb_calculator.plot_lightcurve_and_sine(ax1)

        # Plot the periodogram
        self.orb_calculator.plot_periodogram(ax2)

        # Plot the binned lightcurve
        self.orb_calculator.plot_binned_lightcurve(ax3)


    def doppler_beaming_plot(self, fig):
        """
            Presents a plot of the binned lightcurve, but with two folds instead of one to see if there is doppler beaming
            Name:       doppler_beaming_plots()
            Parameters:
                        fig: current plot figure 
            Returns:
                        None
        """
        # Plot title and axis
        plt.suptitle("Press 'y' if there is doppler beaming, 'n' if not", fontweight = 'bold')
        ax = fig.add_axes([0.1, 0.2, 0.8, 0.6])

        # Bin the lightcurve, but with 2 folds
        binned_lightcurve = self.orb_calculator.fold_lightcurve(num_folds = 2)

        # Bin the sine wave, but with 2 folds
        binned_sine, _ = self.orb_calculator.fold_sine_wave(self.orb_calculator.time, self.orb_calculator.sine_fit.params['frequency'].value, 
                                           self.orb_calculator.sine_fit.best_fit, num_folds = 2)
        
        # Plot the binned lightcurve
        ax.vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#9AADD0', lw = 2)
        
        # Plot the binned sine wave
        ax.plot(binned_sine.phase.value, binned_sine.flux.value, color = '#101935', label = 'Folded Sine Wave')

        # Add legend 
        ax.legend()


    def flares_plot(self, fig):
        """
            Presents a plot of the lightcurve and residuals to see if there are flares
            Name:       eclipsing_plot()
            Parameters:
                        fig: current plot figure 
            Returns:
                        None
        """
        # Plot title and axis 
        plt.suptitle("Press 'y' if there are flares, 'n' if not", fontweight = 'bold')

        # Plots for Flares
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[1, 0])
        plt.subplots_adjust(hspace=0.5)

        # Plot the lightcurve with the fit
        self.orb_calculator.plot_lightcurve_and_sine(ax1)

        # Plot the residuals
        self.orb_calculator.plot_residuals(ax2)

    
    def effects_plots(self, effect):
        """
            Presents an effects plot depending on the given effect
            Name:       eclipsing_plot()
            Parameters:
                        effect: lightcurve effect
            Returns:
                        None
        """
        # Plot basics
        sns.set_style("darkgrid")
        sns.set_theme(rc={'axes.facecolor':'#F8F5F2'})
        fig = plt.figure(figsize=(14, 8))
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: self.on_key(event))
        fig.text(0.5, 0.928, fr'$P_{{\text{{orb, max power}}}}={np.round(self.lightcurve_data.period_at_max_power, 4)}$ days', ha='center', fontsize=12)
        fig.text(0.5, 0.02, fr'{self.lightcurve_data.name}, $i_{{\text{{mag}}}}={self.lightcurve_data.imag}$', ha='center', fontsize=16)
        
        # Eclipsing plot
        if effect == 'Eclipsing':
            self.eclipsing_plot(fig)

        # Doppler beaming plot
        if effect == 'Doppler beaming':
            self.doppler_beaming_plot(fig)

        # Flares plot
        if effect == 'Flares':
            self.flares_plot(fig)



    def on_key(self, event):
        """
            Event function that determines if a key was clicked
            Name:       on_key()
            Parameters: 
                        event: key press event
            Returns:
                        None
        """
        y_n_keys = {'y', 'n'}

        if event.key not in y_n_keys:
                print("Invalid key input, select 'y' or 'n'")
        else:
            self.effects_found.append(event.key == 'y') 
            plt.close()