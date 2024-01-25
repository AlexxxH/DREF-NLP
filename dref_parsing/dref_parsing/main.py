import requests
import pandas as pd
from fastapi import FastAPI, Query, HTTPException

from dref_parsing import parser_utils
from dref_parsing.appeal import Appeal

app = FastAPI()

@app.post("/parse/")
async def run_parsing(
    appeal_code: str = Query(
        default=None,
        title="Appeal code",
        description="Starts with 'MDR' followed by 5 symbols. <br> Some available codes: DO013, BO014, CL014, AR017, VU008, TJ029, SO009, PH040, RS014, FJ004, CD031, MY005, LA007, CU006, AM006",
        min_length=8,
        max_length=8,
        pattern="^MDR[A-Z0-9]{5}$",
        required=True
        )
    ):
    """
    App for Parsing PDFs of DREF Final Reports.   
    <b>Input</b>: Appeal code of the report, MDR*****  
    <b>Output</b>:  
    &nbsp;&nbsp; a dictionary of excerpts extracted from the PDF with its features: 'Learning', 'DREF_Sector',  
    &nbsp;&nbsp; and global features: 'Hazard', 'Country', 'Date', 'Region', 'Appeal code'

    The app uses IFRC GO API to determine the global features (call 'appeal')  
    and to get the URL of the PDF report (call 'appeal_document')

    <b>Possible errors</b>:  
    <ul>
    <li> Appeal code doesn't have a DREF Final Report in IFRC GO appeal database 
    <li> PDF URL for Appeal code was not found using IFRC GO API call appeal_document
    <li> PDF Parsing didn't work
    </ul>
    """    
    appeal = Appeal(mdr_code=appeal_code)
    appeal_data = pd.DataFrame([{
        'Appeal code': appeal_code,
        'Hazard': appeal.official_hazard_name, 
        'Country': appeal.country,
        'Region': appeal.region,
        'Date': appeal.start_date
    }])
    appeal_document = appeal.get_dref_final_report()
    exs_parsed, _ = appeal_document.get_challenges_lessons_learned()
    all_parsed = exs_parsed.merge(appeal_data, on='Appeal code')

    df = all_parsed[['Excerpt', 'Learning', 'DREF_Sector', 'Appeal code', 'Hazard', 'Country', 'Date', 'Region']]

    return df.to_dict()


@app.post("/parse_old/")
async def run_parsing(
    Appeal_code: str = Query(
        'MDRDO013',
        title="Appeal code",
        description="Starts with 'MDR' followed by 5 symbols. <br> Some available codes: DO013, BO014, CL014, AR017, VU008, TJ029, SO009, PH040, RS014, FJ004, CD031, MY005, LA007, CU006, AM006",
        min_length=8,
        max_length=8)):
    """
    App for Parsing PDFs of DREF Final Reports.   
    <b>Input</b>: Appeal code of the report, MDR*****  
    <b>Output</b>:  
    &nbsp;&nbsp; a dictionary of excerpts extracted from the PDF with its features: 'Learning', 'DREF_Sector',  
    &nbsp;&nbsp; and global features: 'Hazard', 'Country', 'Date', 'Region', 'Appeal code'

    The app uses IFRC GO API to determine the global features (call 'appeal')  
    and to get the URL of the PDF report (call 'appeal_document')

    <b>Possible errors</b>:  
    <ul>
    <li> Appeal code doesn't have a DREF Final Report in IFRC GO appeal database 
    <li> PDF URL for Appeal code was not found using IFRC GO API call appeal_document
    <li> PDF Parsing didn't work
    </ul>
    """

    # Renaming: In the program we call it 'lead', while IFRC calls it 'Appeal_code'
    lead = Appeal_code 
    
    try:
        all_parsed = parser_utils.parse_PDF_combined(lead)
    except parser_utils.ExceptionNotInAPI:
        raise HTTPException(status_code=404, 
                            detail=f"{lead} doesn't have a DREF Final Report in IFRC GO appeal database")
    except parser_utils.ExceptionNoURLforPDF:
        raise HTTPException(status_code=404, 
                            detail=f"PDF URL for Appeal code {lead} was not found using IFRC GO API call appeal_document")
    except:
        raise HTTPException(status_code=500, detail="PDF Parsing didn't work by some reason")

    df2 = all_parsed[['Modified Excerpt', 'Learning', 'DREF_Sector', 'lead', 'Hazard', 'Country', 'Date', 'Region']]#,'position', 'DREF_Sector_id']]
    df2 = df2.rename(columns={'lead':'Appeal code','Modified Excerpt':'Excerpt'})
    return df2.to_dict()

    # Other possible formats for output:
    return df2.to_csv(sep='|').split('\n')
    return all_parsed.to_csv()
    return list(all_parsed.loc[:,'Excerpt'])



@app.post("/refresh/")
async def reload_GO_API_data():
    try:
        # Get the total number of Appeals from GO API
        response = requests.get(
            url = "https://goadmin.ifrc.org/api/v2/appeal/",
            params = {"format": "json", "limit": 1}
        )
        response.raise_for_status()
        total_appeals = response.json()["count"]

        # Get the total number of Appeals Documents from GO API
        response = requests.get(
            url = "https://goadmin.ifrc.org/api/v2/appeal_document/",
            params = {"format": "json", "limit": 1}
        )
        response.raise_for_status()
        total_appeal_documents = response.json()["count"]

        output = f'GO API Reload: {total_appeals} items in appeal, {total_appeal_documents} items in appeal_documents (only DREF Final Reports are selected)'

    except:
        raise HTTPException(status_code=500, detail="Error while accessing GO API data")
    return output 

    # Command to start API:
    # uvicorn main:app --reload



