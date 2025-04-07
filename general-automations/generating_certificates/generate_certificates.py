import pandas as pd
import os, glob
from fillpdf import fillpdfs

# Define constants
TEMPLATE_PATH = 'icorps-completion-certificate-template-nsf.pdf'
OUTPUT_FOLDER = 'generated-pdfs'
DATE = 'February 3, 2024' 
COHORT = 'UMD I-Corps January 2025 Cohort'  

def create_certificates(csv_path):
    # Create output folder if it doesn't exist
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_path)
    
    # Check if the required columns exist
    required_columns = {'First Name' , 'Last Name', 'Program Status'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"CSV must contain {required_columns} columns.")
    
    for _, row in df.iterrows():
        name = row['First Name'] + " " + row['Last Name']
        status = row['Program Status']
        
        if status.strip().lower() == 'completed':  # Ensure status check is case insensitive
            output_pdf_path = os.path.join(OUTPUT_FOLDER, f'{name}.pdf')
            
            # Create and flatten the PDF with the filled form
            fill_and_flatten_pdf(TEMPLATE_PATH, output_pdf_path, name, DATE, COHORT)

def fill_and_flatten_pdf(template_path, output_path, name, date, cohort):
    # Prepare data dictionary with form field names and values
    data_dict = {
        'name': name,
        'date': date,
        'cohort': cohort,
    }
    
    # Temporary path to save the filled PDF
    temp_pdf_path = output_path.replace('.pdf', '_temp.pdf')
    
    # Fill the PDF form
    fillpdfs.write_fillable_pdf(template_path, temp_pdf_path, data_dict)
    print(f'Filled PDF saved as {temp_pdf_path}')
    
    # Flatten the PDF form
    fillpdfs.flatten_pdf(temp_pdf_path, output_path)
    print(f'Flattened PDF saved as {output_path}')

if __name__ == "__main__":
    csv_path = 'data/generate_certificate_input-2025-02-03-15-53-32.csv'
    
    create_certificates(csv_path)
    [os.remove(f) for f in glob.glob('generated-pdfs/*_temp.pdf')]
