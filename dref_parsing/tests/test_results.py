import os
import unittest
import requests
import pandas as pd


class TestResults(unittest.TestCase):

    def test_mdr_codes_results(self):
        """
        Compare appeal document parse results against previously saved expected results.
        """
        base_url = "http://127.0.0.1:8000"
        test_mdr_codes = ['DO013', 'BO014', 'CL014', 'AR017', 'VU008', 'TJ029', 'SO009', 'PH040', 'RS014', 'FJ004', 'CD031', 'MY005', 'LA007', 'CU006', 'AM006']

        for i, mdr_code in enumerate(test_mdr_codes):
            with self.subTest(msg=f'MDR {mdr_code}', i=i):

                # Get MDR code parse results from API parse
                response = requests.post(
                    url=base_url+"/parse/", 
                    params={'appeal_code': f'MDR{mdr_code}'}
                )
                response.raise_for_status()
                results = pd.DataFrame(response.json()).reset_index(drop=True)

                # Read in expected results from file
                TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
                expected_results = pd.read_csv(
                    f'{TESTS_DIR}/results/MDR{mdr_code}.csv', 
                    index_col=0
                )

                # Compare results
                print(results)
                print(expected_results)
                self.assertTrue(
                    expected_results.equals(results), 
                    f'Results do not match expected results for MDR code {mdr_code}\n\nResults:\n{results}\n\nExpected results:\n{expected_results}\n\nComparison:\n{expected_results.compare(results)}'
                )