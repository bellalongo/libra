import csv


class SaveData(object):
    def __init__(self, catalog_data, lightcurve_data, exoplanet_effects):
        self.catalog_data = catalog_data
        self.lightcurve_data = lightcurve_data
        self.exoplanet_effects = exoplanet_effects

        # Save the data to a csv
        self.add_to_csv()


    def create_row(self):
        """
            Creates a row of the current lightcurve's date to be added to the porb_dir
            Name:       eclipsing_plot()
            Parameters:
                        None
            Returns:
                        None
        """
        row = {
            'Star': self.lightcurve_data.name,
            'Orbital period (days)': self.lightcurve_data.period_at_max_power,
            'Literature period (days)': self.lightcurve_data.lit_period, 
            'i Magnitude': self.lightcurve_data.imag,
            'Eclipsing': self.exoplanet_effects.effects_found[0],
            'Doppler beaming': self.exoplanet_effects.effects_found[1],
            'Flares': self.exoplanet_effects.effects_found[2],
            'Irradiation': self.exoplanet_effects.effects_found[3],
            'Ellipsoidal': self.exoplanet_effects.effects_found[4]
        }

        return row


    def add_to_csv(self):
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
            with open(self.catalog_data.porb_dir, 'r') as csvfile:
                pass
            file_exists = True
        except FileNotFoundError:
            file_exists = False

        # Create the row
        row = self.create_row()
        
        # Open file in append mode
        with open(self.catalog_data.porb_dir, 'a', newline='') as csvfile:
            fieldnames = [
                'Star', 
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