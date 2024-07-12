from input_check import *
from catalog_data import *
from lightcurve_data import *

def new_main():

    # Catalog data 
    raw_catalog_dir = 'raw_wdss_data.csv' # Raw query data from https://sdss-wdms.org/ 
    catalog_dir = 'wdss_data.csv' # Query data w/ commas (file shouldn't exist on first run)
    porb_dir = 'orbital_periods/periods.csv' # Where final orbital periods will be stored

    # Lightcurve data
    cadence = 120 # Desired cadence for lightcurves

    # Choose how to run
    preload = True # True if want to save all plots now, and look through them later
    autopilot = False # True if want to just use a CNN to find periods

    # Check inputs
    InputCheck(raw_catalog_dir, catalog_dir, porb_dir, preload, autopilot)

    # Process catalog data
    catalog = CatalogData(raw_catalog_dir, catalog_dir, porb_dir)

    # Iterate through each row in the catalog
    for _, row in catalog.catalog_df.iterrows():
        # Get lightcurve data
        lightcurve_data = LightcurveData(row, cadence)

        if not lightcurve_data.lightcurve: continue

        # Present lightcurve plots







if __name__ == '__main__':
    new_main()