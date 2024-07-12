import csv 
import os
from os.path import exists
import pandas as pd


class CatalogData(object):
    def __init__(self, raw_catalog_dir, catalog_dir, porb_dir):
        self.raw_catalog_dir = raw_catalog_dir
        self.catalog_dir = catalog_dir
        self.porb_dir = porb_dir

        # Preprocess files
        self.preprocess()

        # Create catalofg dataframes
        self.catalog_df = self.create_dataframe()

    
    def preprocess(self):
        """
            Replaces the spaces in the raw data with commas and removes porb_dir if it already exists
            Parameters: 
                        None
            Returns:
                        None
        """
        # Check if query has already been commaized
        if not exists(self.catalog_dir):
            self.commaize()
        
        # Check if orbital period directory already exists
        if exists(self.porb_dir):
            os.remove(self.porb_dir)

    
    def commaize(self):
        """
            Replaces the spaces in the raw data with commas
            Parameters: 
                        None
            Returns:
                        None
        """
        # Open raw file
        with open(self.raw_catalog_dir, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')

            # Open new file
            with open(self.catalog_dir, 'w', newline='') as outfile:
                writer = csv.writer(outfile)
                
                # Iterate through each row
                for row in reader:
                    # Replace spaces for commas for each element
                    modified_row = [column.replace(' ', ',') for column in row]
                    
                    writer.writerow(modified_row)

    
    def create_dataframe(self):
        """
            Creates a pandas dataframe to store the catalog data
            Parameters: 
                        None
            Returns:
                        catalog_df: pandas dataframe of the catalog data
        """
        df = pd.read_csv(self.catalog_dir)
        catalog_df = df[['iau_name', 'i', 'porb', 'porbe']] 

        return catalog_df