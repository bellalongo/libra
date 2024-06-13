import csv


"""
    Add commas to raw CSV file
    Name:       commaize()
    Parameters: 
                raw_filename: raw CSV file
                new_filename: new CSV file
    Returns:
                None
"""
def commaize(raw_filename, new_filename):
    with open(raw_filename, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')

        with open(new_filename, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            
            # Iterate through each row
            for row in reader:
                # Replace spaces for commas for each element
                modified_row = [column.replace(' ', ',') for column in row]
                
                writer.writerow(modified_row)


"""
    Append row to a CSV file
    Name:       append_to_csv()
    Parameters: 
                filename: CSV file's name 
                row: row to be added to the file
    Returns:
                None
"""
def append_to_csv(filename, row):
    # Check if file already exists
    try:
        with open(filename, 'r') as csvfile:
            pass
        file_exists = True
    except FileNotFoundError:
        file_exists = False
    
    # Open file in append mode
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['Star', 'Orbital Period(days)', 'Literature Period(days)', 'i Magnitude', 'Eclipsing', 'Flares', 'Irradiation', 'Doppler beaming', 'Ellipsoidal']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        # Append row
        writer.writerow(row)