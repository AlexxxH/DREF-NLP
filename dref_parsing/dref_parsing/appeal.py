"""
Appeal Class - IFRC GO appeal
"""
from functools import cached_property
import requests
from dref_parsing import definitions, utils
from dref_parsing.appeal_document import AppealDocument


class Appeal:
    """
    Parameters
    ----------
    mdr_code : string (required)
        The MDR code for the appeal.
    """
    def __init__(self, mdr_code):
        self.mdr_code = mdr_code

        # Get appeal data from GO, and get info from the results
        self.appeal_data = self.get_appeal_data()
        self.id = self.appeal_data['id']
        self.name = self.appeal_data['name']
        self.disaster_type = self.appeal_data['dtype']['name']
        self.country = self.appeal_data['country']['name']
        self.region = self.appeal_data['region']['region_name']
        self.start_date = self.appeal_data['start_date'][:10]
        

    def get_appeal_data(self):
        """
        Get appeal data from the IFRC GO API.
        """
        # Get the data for that appeal defined by MDR code
        appeal_response = requests.get(
            'https://goadmin.ifrc.org/api/v2/appeal/', 
            params={'code': self.mdr_code, 'format': 'json'}
        )
        appeal_response.raise_for_status()
        appeal_data = appeal_response.json()

        # Check only one appeal
        if appeal_data['count'] != 1:
            if appeal_data['count'] < 1:
                raise RuntimeError(f'No appeals found for MDR code {self.mdr_code}')
            elif appeal_data['count'] > 1:
                raise RuntimeError(f'More than one appeal found for MDR code {self.mdr_code}')

        return appeal_data['results'][0]


    @cached_property
    def official_hazard_name(self):
        """
        """
        # If the disaster type is a recognised hazard name, return
        if self.disaster_type in definitions.OFFICIAL_HAZARD_NAMES:
            return self.disaster_type

        # Try getting the hazard from the name
        hazard_from_title = self.split_report_title(str(self.name))[1].replace('Floods','Flood').replace('Storms','Storm')
        if hazard_from_title in definitions.OFFICIAL_HAZARD_NAMES:
            return hazard_from_title
        if hazard_from_title in ['Flash Flood','Pluvial']: 
            return 'Pluvial/Flash Flood'

        # Check values
        hazard_titles_map = {
            'hailstorm': 'Cold Wave',
            'strong wind': 'Storm Surge',
            'attack': 'Civil Unrest',
            'outbreak': 'Epidemic'
        }
        for hazard in hazard_titles_map:
            if hazard_from_title.lower().count(hazard) > 0:
                return hazard_titles_map[hazard]

        # Get common words between the title and official hazard names
        hazards_with_commons = [h for h in definitions.OFFICIAL_HAZARD_NAMES if len(utils.get_common_words(h, hazard_from_title)) > 0]
        if len(hazards_with_commons) > 0:
            return hazards_with_commons[0]

        return 'Other'
        
    
    def split_report_title(self, title):
        """
        Title usually consists of country, separator, and hazard description
        """
        seps = [' - ','-',': ',':',' ']
        for sep in seps:
            try:
                if title.count(sep)>0:
                    splitted = title.split(sep,1)
                    return [t.strip(' ') for t in splitted]
            except:
                print('ERROR ', title)
        return title, '' 


    def get_dref_final_report(self):
        """
        Get a single DREF final report for the appeal.
        """
        appeal_documents = self.get_appeal_documents()

        # Filter the documents to only DREF final reports
        dref_final_reports = list(filter(
            lambda document: document.name.lower() in map(str.lower, definitions.DREF_FINAL_REPORT_NAMES), 
            appeal_documents
        ))

        # Check exactly one final report
        if len(dref_final_reports) != 1:
            if len(dref_final_reports) == 0:
                raise RuntimeError(f'No DREF final reports found for appeal {self.mdr_code}')
            else:
                raise RuntimeError(f'More than one DREF final report found for appeal {self.mdr_code}')

        return dref_final_reports[0]

    
    def get_appeal_documents(self):
        """
        Get all Appeal Documents for this appeal.
        """
        # Get the appeal documents for the appeal
        appeal_documents_response = requests.get(
            'https://goadmin.ifrc.org/api/v2/appeal_document/', 
            params={'appeal': self.id, 'format': 'json'}
        )
        appeal_documents_response.raise_for_status()
        appeal_documents_data = appeal_documents_response.json()['results']

        # Convert to AppealDocument type
        appeal_documents = []
        for document_data in appeal_documents_data:
            document_data['document_type'] = document_data.pop('type')
            appeal_documents.append(
                AppealDocument(**document_data)
            )
        return appeal_documents