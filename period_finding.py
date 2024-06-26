import astropy.units as u
from lightkurve import LightCurve
import lmfit
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.interpolate import interp1d
import seaborn as sns


# Global variables
best_period_list = []
period_bool_list = []
eclipsing_bool_list = []
doppler_beaming_bool_list = []
flare_bool_list = []


"""
    Appends all lightcurves of the desired cadence
    Name:       append_lightcurves()
    Parameters:
                result: star lightkurve query result
                result_exposures: star lightkurve query exposures
                cadence: desired lightcurve cadence
    Returns:
            None: if no lightcurves are of the desired cadence
            combined_lightcurve: appended lightcurves
"""
def append_lightcurves(result, result_exposures, cadence):
    all_lightcurves = []

    # Get the data whose exposure is the desired cadence
    for i, exposure in enumerate(result_exposures):
        # Check to see if exposure matches cadence 
        if exposure.value == cadence:
            lightcurve = result[i].download().remove_nans().remove_outliers().normalize() - 1
            all_lightcurves.append(lightcurve)
    
    # Check if there are lightcurves
    if all_lightcurves:
        combined_lightcurve = all_lightcurves[0]
        # Iterate through all of the lightcurves
        for lc in all_lightcurves[1:]:
            combined_lightcurve = combined_lightcurve.append(lc)
    else:
        return None
    
    return combined_lightcurve  


"""
    Determines if the period at max power of a periodogram is real based off of standard deviation
    Name:       is_real_period()
    Parameters: 
                periodogram: periodogram of the lightcurve
    Returns:
                boolean: True if the period is real, False if not real
                cutoff: 5 sigma line cut off
"""
def is_real_period(periodogram, period):
    # Remove NaNs from the periodogram
    nan_mask = ~np.isnan(periodogram.power)
    periodogram_power = periodogram.power[nan_mask]
    periodogram_period = periodogram.period[nan_mask].value
    
    # Calculate period at max power
    std_dev = np.std(periodogram_power)

    # Check if within 5 sigma range
    if (abs(period - np.median(periodogram_period)) > 5 * std_dev):
        return True, 5*std_dev
    else:
        return False, 5*std_dev
    

"""
    Calculates the best bin value based off of the duration of the lightcurve
    Name:       find_bin_value()
    Parameters:
                lightcurve: current star's lightcurve
                num_bins: desired number of bins
    Returns:
                bin_value: number of minutes for each bin
"""
def find_bin_value(lightcurve, num_bins):
    total_points = len(lightcurve.time.value)
    total_duration_mins = ((lightcurve.time.value[total_points - 1] - lightcurve.time.value[0]) * u.day).to(u.minute)
    bin_value = (total_duration_mins/num_bins).value
    return bin_value


"""
    Present a series of plots folded on the 'best' period candidates, allowing the user
    to select the best one
    Name:       select_period_plots()
    Parameters:
                lightcurve: current star's lightcurve
                periodogram: current star's periodogram
                literature_period: pre-calculated period, if any 
    Returns:
"""
def select_period_plots(lightcurve, periodogram, literature_period, star_name, star_imag):
    period = periodogram.period_at_max_power.value 
    is_real, cutoff = is_real_period(periodogram, period)

    # Plot basics
    sns.set_style("darkgrid")
    sns.set_theme(rc={'axes.facecolor':'#F8F5F2'})
    fig, axs = plt.subplots(2, 2, figsize=(14, 8))
    plt.subplots_adjust(hspace=0.35)
    plt.suptitle(fr"Press the key corresponding with the best period candidate (1,2,3), if none are good, press 'n'", fontweight = 'bold')
    if is_real:
        fig.text(0.5, 0.928, r'Note: $P_{\text{orb, max}}$ is over 5 sigma, so MIGHT be real', ha='center', fontsize=12, style = 'italic')
    else:
        fig.text(0.5, 0.928, r'Note: $P_{\text{orb, max}}$ is under 5 sigma, so might NOT be real', ha='center', fontsize=12, style = 'italic')
    fig.text(0.5, 0.05, f'{star_name}', ha='center', fontsize=16, fontweight = 'bold')
    fig.text(0.5, 0.02, fr'$i_{{\text{{mag}}}}={star_imag}$', ha='center', fontsize=12, fontweight = 'bold')
    cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, 'Period selection'))

    # Plot the periodogram 
    axs[0, 0].set_title('Periodogram', fontsize=12)
    axs[0, 0].set_xlabel(r'$P_{\text{orb}}$ (days)', fontsize=10)
    axs[0, 0].set_ylabel('Power', fontsize=10)
    axs[0, 0].plot(periodogram.period, periodogram.power, color = '#322820')
    if literature_period != 0.0: axs[0, 0].axvline(x=literature_period, color = '#DF2935', 
                        label = fr'Literature $P_{{\text{{orb}}}}={np.round(literature_period, 2)}$ days')
    axs[0, 0].axvline(x=period, color = '#D36135', ls = 'solid', lw = 2, 
                        label = fr'$P_{{\text{{orb, max}}}}={np.round(period, 2)}$ days')
    axs[0, 0].axvline(x=period/2, color = '#DD882C', ls = 'dashed', lw = 2, 
                        label = fr'$\frac{{1}}{{2}} \times P_{{\text{{orb, max}}}}={np.round(period/2, 2)}$ days')
    axs[0, 0].axvline(x=2*period, color = '#E3BE4F', ls = 'dashed', lw = 2, 
                        label = fr'$2 \times P_{{\text{{orb, max}}}}={np.round(2*period, 2)}$ days')
    axs[0,0].axhline(y = cutoff, color = '#6E8EC4', ls = 'dashed', lw = 2, label = '5-sigma cutoff')
    axs[0, 0].set_xscale('log') 
    axs[0, 0].legend(loc = 'upper left')

    # Fold on period at 1/2 * max power
    phase_lightcurve = lightcurve.fold(period = period/2)
    bin_value = find_bin_value(phase_lightcurve, 50)
    binned_lightcurve = phase_lightcurve.bin(bin_value*u.min) 
    axs[1, 0].set_title(r'$\mathbf{1}$: Folded on $\frac{1}{2} \times P_{\text{orb, max}}$', fontsize=12)
    axs[1, 0].set_xlabel('Phase', fontsize = 10)
    axs[1, 0].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 0].vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, 
                        color = '#DD882C', lw=2, label = fr'$\frac{{1}}{{2}} \times P_{{\text{{orb, max}}}}={np.round(period/2, 2)}$ days')
    axs[1,0].legend()
    
    # Fold on max power
    phase_lightcurve = lightcurve.fold(period = period)
    bin_value = find_bin_value(phase_lightcurve, 50)
    binned_lightcurve = phase_lightcurve.bin(bin_value*u.min) 
    axs[0, 1].set_title(r'$\mathbf{2}$: Folded on $P_{\text{orb, max}}$', fontsize=12)
    axs[0, 1].set_xlabel('Phase', fontsize = 10)
    axs[0, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[0, 1].vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, 
                        color = '#D36135', lw=2, label = fr'$P_{{\text{{orb, max}}}}={np.round(period, 2)}$ days')
    axs[0,1].legend()
    
    # Fold on 2* max power
    phase_lightcurve = lightcurve.fold(period = 2*period)
    bin_value = find_bin_value(phase_lightcurve, 50)
    binned_lightcurve = phase_lightcurve.bin(bin_value*u.min) 
    axs[1, 1].set_title(r'$\mathbf{3}$: Folded on $2 \times P_{\text{orb, max}}$', fontsize=12)
    axs[1, 1].set_xlabel('Phase', fontsize = 10)
    axs[1, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 1].vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, 
                        color = '#E3BE4F', lw=2, label = fr'$2 \times P_{{\text{{orb, max}}}}={np.round(2*period, 2)}$ days')
    axs[1,1].legend()
    
    plt.show()

    # Check which plot was selected
    curr_index = len(best_period_list) - 1
    if best_period_list[curr_index] == '1':
        return period/2
    elif best_period_list[curr_index] == '2':
        return period
    elif best_period_list[curr_index] == '3':
        return 2*period
    else:
        return False  


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
def sine_wave(x, amplitude, frequency, phase):
    return amplitude * np.sin((2 * np.pi * frequency * x) + phase)


"""
    Creates a plot of the periodogram, binned lightcurve, fitted sine wave, and subtracted sine wave
    Name:       period_selection_plots()
    Parameters: 
                lightcurve: current star's lightcurve
                periodogram: current star's periodogram
                best_period: predetermined star's most likely orbital period
                literature_period: current star's documented orbital period
                star_name: current star's TIC name
                star_imag: current star's i magnitude 
    Returns:
                result.best_fit: best fit sine wave for the lightcurve
                residuals: lightcurve flux - best fit sine wave
"""
def period_selection_plots(lightcurve, periodogram, best_period, literature_period, star_name, star_imag):
    # Determine if the period is probable
    is_real, cutoff = is_real_period(periodogram, best_period)

    # Define folded and binned lightcurve
    phase_lightcurve = lightcurve.fold(period = best_period)
    bin_value = find_bin_value(phase_lightcurve, 50)
    binned_lightcurve = phase_lightcurve.bin(bin_value*u.min) 

    # Lightcurve data
    time = lightcurve.time.value
    flux = lightcurve.flux.value

    # Get the power at the best period
    interp_func = interp1d(periodogram.period.value, periodogram.power.value, kind='linear', bounds_error=False, fill_value=np.nan)
    power_at_best_period = interp_func(best_period)

    # Make an lmfit object and fit it
    model = lmfit.Model(sine_wave)
    params = model.make_params(amplitude = power_at_best_period , 
                            frequency = 1/best_period, 
                            phase=0.0)
    result = model.fit(flux, params, x=time)

    # Calculate the time points for the period lines
    sine_period = 1 / (result.params['frequency'].value)
    time_points = np.arange(min(time), max(time), sine_period)

    # Fold sine wave
    sine_lightcurve = LightCurve(time = time, flux = result.best_fit)
    sine_phase_lightcurve = sine_lightcurve.fold(period = best_period)
    sine_binned_lightcurve = sine_phase_lightcurve.bin(bin_value*u.min)

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
    axs[0, 0].plot(periodogram.period, periodogram.power, color = '#9AADD0')
    axs[0, 0].axvline(x=best_period, color = "#101935", ls = (0, (4,5)), lw = 2, label = fr'$P_{{\text{{orb, best}}}}={np.round(best_period, 3)}$ days') 
    if literature_period != 0.0: axs[0, 0].axvline(x=literature_period, color = '#A30015', label = fr'Literature $P_{{\text{{orb}}}}={np.round(literature_period, 3)}$ days')
    axs[0, 0].axhline(y = cutoff, color = '#4A5D96', ls = (0, (4,5)), lw = 2, label = '5-sigma cutoff')
    axs[0, 0].set_xscale('log') 
    axs[0, 0].legend(loc = 'upper left')

    # Plot binned lightcurve
    axs[1, 0].set_title(r'Lightcurve Folded on $P_{\text{orb, max power}}$', fontsize=12)
    axs[1, 0].set_xlabel('Phase', fontsize = 10)
    axs[1, 0].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 0].vlines(binned_lightcurve.phase.value, 
                    binned_lightcurve.flux - binned_lightcurve.flux_err, 
                    binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#9AADD0', lw = 2)
    axs[1, 0].plot(sine_binned_lightcurve.phase.value, sine_binned_lightcurve.flux.value, color = '#101935', label = 'Folded Sine Wave')
    axs[1, 0].legend()

    # Plot the fitted sin wave
    axs[0, 1].set_title('Lightcurve', fontsize=12)
    axs[0, 1].set_xlabel('Time (days)', fontsize = 10)
    axs[0, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[0, 1].vlines(lightcurve.time.value, 
                    lightcurve.flux - lightcurve.flux_err, 
                    lightcurve.flux + lightcurve.flux_err, color = '#9AADD0')
    # Add vertical lines at each period interval
    for tp in time_points:
        axs[0, 1].axvline(tp, color = '#4A5D96', ls = (0, (4,5)), lw = 2, label = fr'$P_{{\text{{orb, sine}}}}={np.round(sine_period, 3)}$ days' if tp == time_points[0] else "")
    axs[0, 1].plot(time, result.best_fit, color= '#101935', label = 'Fitted Sine Wave')
    axs[0, 1].set_xlim(min(time) + 1 + best_period, min(time) + 1 + 4*best_period)
    axs[0, 1].legend()

    # Subtract sine wave
    residuals = flux - result.best_fit
    axs[1, 1].set_title('Flux - Fitted Sine Wave', fontsize=12)
    axs[1, 1].set_xlabel('Time (days)', fontsize = 10)
    axs[1, 1].set_ylabel('Normalized Flux', fontsize = 10)
    axs[1, 1].plot(time, residuals, color = '#9AADD0') # maybe make me into scatter
    axs[1, 1].set_xlim(min(time) + 1 + best_period, min(time) + 1 + 4*best_period)

    return result.best_fit, residuals


'''
    Creates a plot of the binned lightcurve, fitted sine wave, and residuals which are used to show lightcurve effects, if any
    Name:       effects_selection_plot()
    Parameters: 
                effect: lightcurve effect ('Transits', 'Ellipsoidal', 'Radiation', or 'Doppler beaming')
                lightcurve: current star's appended lightcurve
                periodogram: current star's periodogram
                best_period: current star's best period
                binned_lightcurve: lightcurve folded on best period, put into 50 bins
                sine_fit: best fit sine wave for the lightcurve
                sine_binned_lightcurve: best fit sine wave folded on the period, put into 50 bins
                residuals: lightcurve flux - best fit sine wave
                star_name: current star's TIC name
                star_imag: current stars i magnitude
    Returns:
                None
'''
def effects_selection_plot(effect, lightcurve, periodogram, best_period, sine_fit, residuals, star_name, star_imag):
    # Lightcurve data
    time = lightcurve.time.value

    # Plot basics
    sns.set_style("darkgrid")
    sns.set_theme(rc={'axes.facecolor':'#F4F6F3'})
    fig = plt.figure(figsize=(14, 8))
    cid = fig.canvas.mpl_connect('key_press_event', lambda event: on_key(event, effect))
    fig.text(0.5, 0.928, fr'$P_{{\text{{orb, max power}}}}={np.round(best_period, 4)}$ days' , ha='center', fontsize=12)
    fig.text(0.5, 0.02, fr'{star_name},  $i_{{\text{{mag}}}}={star_imag}$', ha='center', fontsize=16)

    if effect == 'Eclipsing':
        plt.suptitle("Press 'y' if there are eclipses, 'n' if not", fontweight = 'bold')

        # Plots for Eclipsing
        gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1]) 
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        plt.subplots_adjust(hspace=0.5)

        # Bin lightcurve
        phase_lightcurve = lightcurve.fold(period = best_period)
        bin_value = find_bin_value(phase_lightcurve, 50)
        binned_lightcurve = phase_lightcurve.bin(bin_value*u.min)

        # Bin Sine Wave
        sine_lightcurve = LightCurve(time = time, flux = sine_fit)
        sine_phase_lightcurve = sine_lightcurve.fold(period = best_period)
        sine_binned_lightcurve = sine_phase_lightcurve.bin(bin_value*u.min)

        # Plot the lightcurve with sine fit
        ax1.set_title('Lightcurve', fontsize=13)
        ax1.set_xlabel('Time (days)', fontsize = 10)
        ax1.set_ylabel('Normalized Flux', fontsize = 10)
        ax1.scatter(lightcurve.time.value, lightcurve.flux.value, color = '#98A391', s = 2)
        ax1.plot(time, sine_fit, color= '#000000', lw = 1.5, label = 'Fitted Sine Wave')
        ax1.legend()

        # Plot the periodogram
        ax2.set_title('Periodogram', fontsize=12)
        ax2.set_xlabel(r'$P_{\text{orb}}$ (days)', fontsize=10)
        ax2.set_ylabel('Power', fontsize=10)
        ax2.plot(periodogram.period, periodogram.power, color = '#98A391')
        ax2.axvline(x=best_period, color = '#000000', ls = (0, (4,5)), lw = 2,
                            label = fr'$P_{{\text{{orb, max}}}}={np.round(best_period, 3)}$ days')
        ax2.set_xscale('log') 
        ax2.legend(loc = 'upper left')

        # Plot the binned lightcurve
        ax3.set_title(r'Folded on $P_{\text{orb, max power}}$', fontsize=13)
        ax3.set_xlabel('Phase', fontsize = 10)
        ax3.set_ylabel('Normalized Flux', fontsize = 10)
        ax3.vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#98A391', lw=2)
        ax3.plot(sine_binned_lightcurve.phase.value, sine_binned_lightcurve.flux.value, color = '#000000', lw = 2, label = 'Folded Sine Wave')
        ax3.legend()

    elif effect == 'Flares':
        plt.suptitle("Press 'y' if there are flares, 'n' if not", fontweight = 'bold')

        # Plots for Flares
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[1, 0])
        plt.subplots_adjust(hspace=0.5)

        # Plot lightcurve w/ fit
        ax1.set_title('Lightcurve', fontsize=13)
        ax1.set_xlabel('Time (days)', fontsize = 10)
        ax1.set_ylabel('Normalized Flux', fontsize = 10)
        ax1.scatter(lightcurve.time.value, lightcurve.flux.value, color = '#98A391', s = 2)
        ax1.plot(time, sine_fit, color= '#000000', lw = 1.5, label = 'Fitted Sine Wave')
        ax1.legend()

        # Plot residuals
        ax2.set_title('Flux - Fitted Sine Wave', fontsize=13)
        ax2.set_xlabel('Time (days)', fontsize = 10)
        ax2.set_ylabel('Normalized Flux', fontsize = 10)
        ax2.plot(time, residuals, color= '#98A391', lw = 1)

    elif effect == 'Doppler beaming':
        plt.suptitle("Press 'y' if there is doppler beaming, 'n' if not", fontweight = 'bold')
        ax = fig.add_axes([0.1, 0.2, 0.8, 0.6])

        # Bin lightcurve
        phase_lightcurve = lightcurve.fold(period = 2*best_period) # CHECK ME MISS GIRL
        bin_value = find_bin_value(phase_lightcurve, 100)
        binned_lightcurve = phase_lightcurve.bin(bin_value*u.min)

        # Bin sine wave
        sine_lightcurve = LightCurve(time = time, flux = sine_fit) # CHECK ME MISS GIRL
        sine_phase_lightcurve = sine_lightcurve.fold(period = 2*best_period)
        sine_binned_lightcurve = sine_phase_lightcurve.bin(bin_value*u.min)

        # Plot the binned lightcurve
        ax.set_title(r'Folded on $P_{\text{orb, max power}}$', fontsize=13)
        ax.set_xlabel('Phase', fontsize = 10)
        ax.set_ylabel('Normalized Flux', fontsize = 10)
        ax.vlines(binned_lightcurve.phase.value, 
                        binned_lightcurve.flux - binned_lightcurve.flux_err, 
                        binned_lightcurve.flux + binned_lightcurve.flux_err, color = '#98A391', lw=2)
        ax.plot(sine_binned_lightcurve.phase.value, sine_binned_lightcurve.flux.value, color = '#000000', lw = 2, label = 'Folded Sine Wave')
        ax.legend()

    else: 
        print("Invalid effect, must be 'Eclipsing', 'Flares', or 'Doppler beaming'")


"""
    Event function that determines if a key was clicked
    Name:       on_key()
    Parameters: 
                event: key press event
                purpose: either doppler or noise
    Returns:
                None
"""
def on_key(event, purpose):
    y_n_keys = {'y', 'n'}
    num_keys = {'1', '2', '3', 'n'}

    if purpose == 'Period selection':
        if event.key not in num_keys:
            print("Invalid key input, select '1', '2', '3', or 'n'")
        else:
            best_period_list.append(event.key)
            if event.key == 'n':
                print(f'None selected, loading next plot ... \n')
            else:
                print(f'Selected plot {event.key}')
            plt.close()

    elif purpose == 'Real period':
        if event.key not in y_n_keys:
            print("Invalid key input, select 'y' or 'n'")
        else:
            period_bool_list.append(event.key == 'y')
            if event.key == 'n':
                print('Period is not real, loading next plot ... \n')
            plt.close()

    elif purpose == 'Eclipsing':
        if event.key not in y_n_keys:
            print("Invalid key input, select 'y' or 'n'")
        else:
            eclipsing_bool_list.append(event.key == 'y') 
            plt.close()

    elif purpose == 'Doppler beaming':
        if event.key not in y_n_keys:
            print("Invalid key input, select 'y' or 'n'")
        else:
            doppler_beaming_bool_list.append(event.key == 'y')
            plt.close()

    elif purpose == 'Flares':
        if event.key not in y_n_keys:
            print("Invalid key input, select 'y' or 'n'")
        else:
            flare_bool_list.append(event.key == 'y')
            plt.close()
            print(f'Loading next plot ... \n')

    else:
        print("Invalid purpose, select 'Period selection' or 'Real period'")