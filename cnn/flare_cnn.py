import numpy as np
import matplotlib.pyplot as plt

# Parameters
num_points = 1000       # Number of data points in the lightcurve
orbital_period = 1.5    # Orbital period in days
amplitude = 0.1         # Amplitude of the sine wave
noise_level = 0.01      # Noise level
flare_probability = 0.05 # Probability of a flare occurring at a given point

# Generate time array
time = np.linspace(0, 10, num_points)  # 10 days of observation

# Generate the sine wave for the binary system
flux = amplitude * np.sin((2 * np.pi / orbital_period) * time)

# Add noise
flux += np.random.normal(0, noise_level, num_points)

# Add random flares (steep decrease followed by exponential decay)
for i in range(num_points):
    if np.random.rand() < flare_probability:
        flare_start = i
        flare_decay = np.arange(0, 10)  # Exponential decay length
        flare_magnitude = np.random.uniform(0.05, 0.1)  # Flare magnitude
        flux[flare_start:flare_start+len(flare_decay)] -= flare_magnitude * np.exp(-0.1 * flare_decay)

# Plot the simulated lightcurve as a line plot
plt.plot(time, flux, 'k-', linewidth=0.5)
plt.xlabel('Time (days)')
plt.ylabel('Normalized Flux')
plt.title('Simulated Lightcurve with Flares')
plt.show()
