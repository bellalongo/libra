from os.path import exists


class InputCheck(object):
    def __init__(self, raw_catalog_dir, catalog_dir, 
                 porb_dir, preload, autopilot):

        self.raw_catalog_dir = raw_catalog_dir
        self.catalog_dir = catalog_dir
        self.porb_dir = porb_dir
        self.preload = preload
        self.autopilot = autopilot

        # Check files
        self.check_files()

        # Check booleans
        self.check_booleans()
    

    def check_files(self):
        """
            Checks if files exist and if are of correct variable type
            Parameters: 
                        None
            Returns:
                        None
        """
        # Check types
        if not isinstance(self.raw_catalog_dir, str):
            raise TypeError(f"Variable raw_catalog_dir must be of type 'str'")
        
        if not isinstance(self.catalog_dir, str):
            raise TypeError(f"Variable catalog_dir must be of type 'str'")
        
        if not isinstance(self.porb_dir, str):
            raise TypeError(f"Variable porb_dir must be of type 'str'")

        # Check values
        if not exists(self.raw_catalog_dir):
            raise FileNotFoundError(f"The file for raw_catalog_dir: {self.raw_catalog_dir} does not exist")
        
    
    def check_booleans(self):
        """
            Checks if input booleans are of type bool
            Parameters: 
                        None
            Returns:
                        None
        """
        # Check types
        if not isinstance(self.preload, bool):
            raise TypeError(f"Variable preload must be of type 'bool'")
        
        if not isinstance(self.autopilot, bool):
            raise TypeError(f"Variable autopilot must be of type 'bool'")
