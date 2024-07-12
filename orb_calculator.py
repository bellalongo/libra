import astropy.units as u
from lightkurve import LightCurve
import lmfit 
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


class OrbCalculator(object):
    def __init__(self, lightcurve_data):
        self.lightcurve_data = lightcurve_data

        # Initialize boolean list for if the period is real and a list in format [Eclipsing, Doppler beaming, Flares] if real
        self.is_real_period_list, self.effects_list = [], []

        # Determine if the period is plausible
        self.is_plausible, self.cutoff = self.plausible_period()

        # Lightcurve data
        self.time = self.lightcurve_data.lightcurve.time.value
        self.flux = self.lightcurve_data.lightcurve.flux.value

        # Fit a sine wave to the lightcurve
        self.sine_fit = self.fit_sine_wave(self.time, self.flux)

        # Fold and bin lightcurve
        self.binned_lightcurve = self.fold_lightcurve()

        # Fold and bin sine fit
        self.binned_sine, self.sine_period = self.fold_sine_wave(self.time, self.sine_fit.params['frequency'].value, self.sine_fit.best_fit)

        # Calculate time points of the sine wave
        self.time_points = np.arange(min(self.time), max(self.time), self.sine_period)

        # Calculate plot xmin and xmax
        self.xmin = min(self.time) + 1 + self.lightcurve_data.period_at_max_power
        self.xmax = min(self.time) + 1 + 4*self.lightcurve_data.period_at_max_power

        # Create plots for determing if the period is real
        self.is_real_period_plot()
        plt.show()


    def plausible_period(self):
        """
            Determines if the period at max power of a periodogram is plausible based off of standard deviation
            Name:       is_real_period()
            Parameters: 
                        periodogram: periodogram of the lightcurve
            Returns:
                        boolean: True if the period is plausible, False if not real
                        cutoff: 5 sigma line cut off

        """
        # Remove NaNs from the periodogram
        nan_mask = ~np.isnan(self.lightcurve_data.periodogram.power)
        periodogram_power = self.lightcurve_data.periodogram.power[nan_mask]
        periodogram_period = self.lightcurve_data.periodogram.period[nan_mask].value
        
        # Calculate standard deviaition of the periodogram
        std_dev = np.std(periodogram_power)

        # Check period at max power is greater than 5 sigma 
        if (abs(self.lightcurve_data.period_at_max_power - np.median(periodogram_period)) > 5 * std_dev):
            return True, 5*std_dev
        else:
            return False, 5*std_dev


    def sine_wave(self, x, amplitude, frequency, phase):
        """
            Creates a sine wave based off of given parameters
            Name:       sine_wave()
            Parameters: 
                        x: data points
                        amplitude: desired amplitude
                        frequency: desired frequency
                        phase: desired phase
            Returns:
                        a sine wave
        """
        return amplitude * np.sin((2 * np.pi * frequency * x) + phase)


    def find_bin_value(self, lightcurve, num_bins):
        """
            Calculates the best bin value based off of the duration of the lightcurve
            Name:       find_bin_value()
            Parameters:
                        num_bins: desired number of bins
            Returns:
                        bin_value: number of minutes for each bin
        """
        total_points = len(lightcurve.time.value)
        total_duration_mins = ((lightcurve.time.value[total_points - 1] - lightcurve.time.value[0]) * u.day).to(u.minute)
        bin_value = (total_duration_mins/num_bins).value
        return bin_value
         
    
    def fit_sine_wave(self, time, flux):
        """

        """
        # Make an lmfit object and fit it
        model = lmfit.Model(self.sine_wave)
        params = model.make_params(amplitude = self.lightcurve_data.period_at_max_power , 
                                frequency = 1/self.lightcurve_data.period_at_max_power, 
                                phase=0.0)
        result = model.fit(flux, params, x=time)

        return result

    
    def fold_lightcurve(self):
        """

        """
        # Fold lightcurve
        folded_lightcurve = self.lightcurve_data.lightcurve.fold(period = self.lightcurve_data.period_at_max_power)

        # Calculate bin value
        bin_value = self.find_bin_value(folded_lightcurve, 50)

        # Bin the folded lightcurve
        binned_lightcurve = folded_lightcurve.bin(bin_value*u.min) 

        return binned_lightcurve
    

    def fold_sine_wave(self, x, frequency, sine_wave):
        """

        """
        # Calculate the time points for the period lines
        sine_period = 1 / frequency

        # Make the sine wave into a lightcurve 
        sine_lightcurve = LightCurve(time = x, flux = sine_wave)

        # Fold sine wave
        folded_sine = sine_lightcurve.fold(period = self.lightcurve_data.period_at_max_power)

        # Calculate bin value
        bin_value = self.find_bin_value(folded_sine, 50)

        binned_sine = folded_sine.bin(bin_value * u.min)

        return binned_sine, sine_period
    

    def plot_periodogram(self, axis):
        """
            axis: where it will be plotted
        """
        # Plot title
        axis.set_title('Periodogram', fontsize=12)
        axis.set_xlabel(r'$P_{\text{orb}}$ (days)', fontsize=10)
        axis.set_ylabel('Power', fontsize=10)
        axis.plot(self.lightcurve_data.periodogram.period, self.lightcurve_data.periodogram.power, color = '#9AADD0')
        axis.axvline(x = self.lightcurve_data.period_at_max_power, color = "#101935", ls = (0, (4,5)), lw = 2, 
                          label = fr'$P_{{\text{{orb, best}}}}={np.round(self.lightcurve_data.period_at_max_power, 3)}$ days') 
        
        # Plot literature period if there is one
        if self.lightcurve_data.literature_period != 0.0: 
            axis.axvline(x = self.lightcurve_data.literature_period, color = '#A30015', 
                              label = fr'Literature $P_{{\text{{orb}}}}={np.round(self.lightcurve_data.literature_period, 3)}$ days')

        # Plot 5 sigma cutoff
        axis.axhline(y = self.cutoff, color = '#4A5D96', ls = (0, (4,5)), lw = 2, label = '5-sigma cutoff')

        # Change scale to be log
        axis.set_xscale('log') 

        # Add legend
        axis.legend(loc = 'upper left')


    def plot_binned_lightcurve(self, axis):
        """

        """
        # Plot title
        axis.set_title(r'Lightcurve Folded on $P_{\text{orb, max power}}$', fontsize=12)
        axis.set_xlabel('Phase', fontsize = 10)
        axis.set_ylabel('Normalized Flux', fontsize = 10)

        # Plot the binned lightcurve
        axis.vlines(self.binned_lightcurve.phase.value, 
                        self.binned_lightcurve.flux - self.binned_lightcurve.flux_err, 
                        self.binned_lightcurve.flux + self.binned_lightcurve.flux_err, color = '#9AADD0', lw = 2)
        
        # Plot the binned sine fit 
        axis.plot(self.binned_sine.phase.value, self.binned_sine.flux.value, color = '#101935', label = 'Folded Sine Wave')

        # Add legend 
        axis.legend()


    def plot_lc_and_fit(self, axis):
        """

        """
        # Plot title 
        axis.set_title('Lightcurve', fontsize=12)
        axis.set_xlabel('Time (days)', fontsize = 10)
        axis.set_ylabel('Normalized Flux', fontsize = 10)

        # Plot lightcurve
        axis.vlines(self.lightcurve_data.lightcurve.time.value, 
                        self.lightcurve_data.lightcurve.flux - self.lightcurve_data.lightcurve.flux_err, 
                        self.lightcurve_data.lightcurve.flux + self.lightcurve_data.lightcurve.flux_err, color = '#9AADD0')
        
        # Add vertical lines at each period interval of the sine wave
        for tp in self.time_points:
            axis.axvline(x = tp, color = '#4A5D96', ls = (0, (4,5)), lw = 2, 
                         label = fr'$P_{{\text{{orb, sine}}}}={np.round(self.sine_period, 3)}$ days' if tp == self.time_points[0] else "")
        
        # Plot sine wave
        axis.plot(self.time, self.sine_fit.best_fit, color= '#101935', label = 'Fitted Sine Wave')

        # Set xlim and plot legend 
        axis.set_xlim(self.xmin, self.xmax)
        axis.legend()

    
    def plot_residuals(self, axis):
        """

        """
        # Calculate residuals (lightcurve flux - sine wave flux)
        residuals = self.flux - self.sine_fit.best_fit

        # Plot title
        axis.set_title('Flux - Fitted Sine Wave', fontsize=12)
        axis.set_xlabel('Time (days)', fontsize = 10)
        axis.set_ylabel('Normalized Flux', fontsize = 10)

        # Plot the residuals
        axis.plot(self.time, residuals, color = '#9AADD0') 

        # Set xlim (no legend needed)
        axis.set_xlim(self.xmin, self.xmax)


    def is_real_period_plot(self):
        """
            
        """
        # Plot basics
        sns.set_style("darkgrid")
        sns.set_theme(rc={'axes.facecolor':'#F8F5F2'})
        fig, axs = plt.subplots(2, 2, figsize=(14, 8))
        plt.subplots_adjust(hspace=0.35)
        plt.suptitle(fr"Press the key corresponding with the best period candidate (1,2,3), if none are good, press 'n'", fontweight = 'bold')
        if self.is_plausible:
            fig.text(0.5, 0.928, r'Note: $P_{\text{orb, max}}$ is over 5 sigma, so MIGHT be real', ha='center', fontsize=12, style = 'italic')
        else:
            fig.text(0.5, 0.928, r'Note: $P_{\text{orb, max}}$ is under 5 sigma, so might NOT be real', ha='center', fontsize=12, style = 'italic')
        fig.text(0.5, 0.05, f'{self.lightcurve_data.name}', ha='center', fontsize=16, fontweight = 'bold')
        fig.text(0.5, 0.02, fr'$i_{{\text{{mag}}}}={self.lightcurve_data.imag}$', ha='center', fontsize=12, fontweight = 'bold')
        cid = fig.canvas.mpl_connect('key_press_event', lambda event: self.on_key(event, 'Real period'))

        # Plot the periodogram
        self.plot_periodogram(axs[0, 0]) # see if can do this

        # Plot the binned lightcurve
        self.plot_binned_lightcurve(axs[1, 0])

        # Plot the lightcurve with the sine fit
        self.plot_lc_and_fit(axs[0,1])
        
        # Plot residuals
        self.plot_residuals(axs[1,1])


    def on_key(self, event, purpose):
        """
            Event function that determines if a key was clicked
            Name:       on_key()
            Parameters: 
                        event: key press event
                        purpose: either doppler or noise
            Returns:
                        None
        """
        curr_index = len(self.effects_list) - 1
        y_n_keys = {'y', 'n'}

        if purpose == 'Real period':
            if event.key not in y_n_keys:
                print("Invalid key input, select 'y' or 'n'")
            else:
                self.is_real_period_list.append(event.key == 'y')
                if event.key == 'n':
                    print('Period is not real, loading next plot ... \n')
                plt.close()

        elif purpose == 'Eclipsing':
            if event.key not in y_n_keys:
                print("Invalid key input, select 'y' or 'n'")
            else:
                self.effects_list.append(event.key == 'y') 
                plt.close()

        elif purpose == 'Doppler beaming':
            if event.key not in y_n_keys:
                print("Invalid key input, select 'y' or 'n'")
            else:
                self.effects_list.append(event.key == 'y')
                plt.close()

        elif purpose == 'Flares':
            if event.key not in y_n_keys:
                print("Invalid key input, select 'y' or 'n'")
            else:
                self.effects_list.append(event.key == 'y')
                plt.close()
                print(f'Loading next plot ... \n')

        else:
            print("Invalid purpose, select 'Period selection' or 'Real period'")
        