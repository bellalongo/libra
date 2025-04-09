# LIBRA: Lightcurve Investigation for Binary oRbital period Analysis

## Overview

LIBRA is a Python toolkit designed to analyze lightcurve data from White Dwarf-Main Sequence (WDMS) binary star systems. The primary goal is to accurately determine orbital periods and identify various astrophysical phenomena that can be observed in these binary systems through their lightcurves.

## Scientific Background

### WDMS Binary Systems

White Dwarf-Main Sequence binary systems consist of a white dwarf star and a main-sequence companion star orbiting around their common center of mass. These systems are particularly valuable for astronomical research as they:

- Allow us to study post-common envelope evolution
- Provide constraints on stellar evolution models
- Help us understand mass transfer processes between stars
- Can be progenitors of cataclysmic variables and type Ia supernovae

### SDSS Data Source

The project uses data from the Sloan Digital Sky Survey (SDSS), specifically queried with:

```sql
SELECT *
FROM mean_param
JOIN magnitudes ON mean_param.iau_name = magnitudes.iau_name
WHERE magnitudes.i < 18;
```

This query selects WDMS systems with apparent i-band magnitudes brighter than 18, ensuring sufficient brightness for reliable analysis.

## Astrophysical Phenomena

LIBRA detects and analyzes several key phenomena in WDMS binary systems:

### 1. Eclipses

When one star passes in front of the other from our perspective, it causes a characteristic dip in the lightcurve.

- **How it's detected**: LIBRA looks for significant dips in the lightcurve that repeat at regular intervals.
- **Scientific importance**: Eclipsing binaries allow for precise determination of stellar radii, masses, and orbital inclination.

### 2. Doppler Beaming

Also known as relativistic beaming, this effect causes a periodic increase in brightness when a star moves toward the observer and a decrease when it moves away.

- **How it's detected**: LIBRA analyzes the folded lightcurve for asymmetric brightening that occurs once per orbital period.
- **Scientific importance**: Provides an independent method to confirm orbital periods and can be used to estimate the radial velocity amplitude without spectroscopy.

### 3. Irradiation

When the hot white dwarf heats the facing hemisphere of the cooler main sequence star, causing it to appear brighter.

- **How it's detected**: LIBRA looks for cases where the literature period matches the period at maximum power, with a characteristic sinusoidal variation.
- **Scientific importance**: Irradiation levels provide information about the temperature of the white dwarf and the atmospheric properties of the companion star.

### 4. Ellipsoidal Variations

The gravitational pull of each star distorts its companion into an ellipsoidal shape, causing brightness variations as our view of the projected area changes throughout the orbit.

- **How it's detected**: LIBRA identifies cases where the literature period is approximately twice the detected period, as ellipsoidal variations typically cause two brightness peaks per orbital period.
- **Scientific importance**: The amplitude of ellipsoidal variations can constrain the mass ratio and orbital inclination of the system.

### 5. Flares

Sudden, temporary increases in brightness due to magnetic reconnection events on the main sequence star.

- **How it's detected**: LIBRA uses the Stella neural network to identify sharp peaks in the residual lightcurve after subtracting the fitted sine wave.
- **Scientific importance**: Flare activity provides information about the magnetic activity and age of the main sequence companion, and how this activity might be influenced by the white dwarf.

## Code Structure and Functionality

LIBRA consists of several interconnected Python modules:

### Main Components

1. **main.py**: The primary script that orchestrates the analysis pipeline.
2. **catalog_data.py**: Processes the SDSS catalog data.
3. **lightcurve_data.py**: Fetches and preprocesses TESS lightcurve data for each target.
4. **orb_calculator.py**: Calculates orbital periods using periodogram analysis and sine wave fitting.
5. **exoplanet_effects.py**: Detects various astrophysical phenomena in the lightcurves.
6. **save_data.py**: Saves analysis results to CSV files.
7. **preload_plots.py**: Handles plot generation and saving for later review.
8. **input_check.py**: Validates input parameters and file paths.

### Analysis Workflow

1. **Data Import**: The code reads in catalog data from SDSS that contains information about WDMS systems.
2. **Lightcurve Retrieval**: For each target in the catalog, the code retrieves lightcurve data from the TESS mission.
3. **Period Detection**: The code uses periodogram analysis to determine the most likely orbital period.
4. **Sine Wave Fitting**: A sine wave is fitted to the lightcurve to model the periodic variations.
5. **Eclipse Removal**: Eclipses are identified and temporarily removed to improve sine wave fitting.
6. **Phenomena Detection**: The code analyzes the lightcurve and residuals to detect eclipses, Doppler beaming, flares, irradiation, and ellipsoidal variations.
7. **Interactive Verification**: The user can interactively confirm or reject detected phenomena (when not in preload or autopilot mode).
8. **Results Storage**: Final results are saved to a CSV file for further analysis.

## Requirements

- Python 3.7+
- Dependencies:
  - astropy
  - lightkurve
  - lmfit
  - matplotlib
  - numpy
  - pandas
  - scipy
  - seaborn
  - tqdm
  - stella (for flare detection)

## Usage

### Basic Usage

```python
python main.py
```

### Configuration

Edit the parameters in `main.py` to customize:

```python
# Catalog data 
raw_catalog_dir = 'raw_wdss_data.csv'  # Raw query data from https://sdss-wdms.org/ 
catalog_dir = 'wdss_data.csv'          # Query data w/ commas
porb_dir = 'orbital_periods/periods.csv'  # Where final orbital periods will be stored

# Lightcurve data
cadence = 120  # Desired cadence for lightcurves in seconds

# Choose how to run
preload = False  # True if want to save all plots now, and look through them later
```

### Run Modes

1. **Interactive Mode** (default): The code will display plots for each target and prompt the user to confirm whether phenomena are real.
2. **Preload Mode**: All plots are generated and saved for later review.
3. **Autopilot Mode**: Uses machine learning to automatically determine real periods without user input.

## Output

The primary output is a CSV file containing:
- TIC (TESS Input Catalog) identifier
- Calculated orbital period
- Literature orbital period (if available)
- i-band magnitude
- Boolean flags for detected phenomena:
  - Eclipsing
  - Doppler beaming
  - Flares
  - Irradiation
  - Ellipsoidal variations
