"""
Generate results from the DREF parsing API.
Save results in the test folder.
"""
import os 
import requests
import argparse
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"
TESTS_DIR = os.path.dirname(os.path.realpath(__file__))

# Initialize parser
parser = argparse.ArgumentParser()
parser.add_argument(
    "-o", 
    "--overwrite", 
    help="Overwrite files", 
    action='store_true'
)
args = parser.parse_args()

# Loop through MDR codes to generate results for, and parse results
test_mdr_codes = ['DO013', 'BO014', 'CL014', 'AR017', 'VU008', 'TJ029', 'SO009', 'PH040', 'RS014', 'FJ004', 'CD031', 'MY005', 'LA007', 'CU006', 'AM006']
for mdr_code in test_mdr_codes:
    response = requests.post(
        url=BASE_URL+"/parse_old/", 
        params={'Appeal_code': f'MDR{mdr_code}'}
    )
    response.raise_for_status()
    results = pd.DataFrame(response.json())

    # Save the results
    save_path = f'{TESTS_DIR}/results/MDR{mdr_code}.csv'
    if os.path.isfile(save_path) and not args.overwrite:
        print(f'WARNING: data for MDR{mdr_code} not saved as already exists. Run with -o flag to overwrite.')
    else:
        results.to_csv(save_path, index=True)