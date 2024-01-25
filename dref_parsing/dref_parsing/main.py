from fastapi import FastAPI, Query, HTTPException

from dref_parsing.parser_utils import *
from dref_parsing.appeal import Appeal


app = FastAPI()


@app.post("/test/")
async def run_parsing(
    Appeal_code: str = Query(
        'MDRDO013',
        title="Appeal code",
        description="Starts with 'MDR' followed by 5 symbols. <br> Some available codes: DO013, BO014, CL014, AR017, VU008, TJ029, SO009, PH040, RS014, FJ004, CD031, MY005, LA007, CU006, AM006",
        min_length=8,
        max_length=8)):
    
    # Renaming: In the program we call it 'lead', while IFRC calls it 'Appeal_code'
    #lead = Appeal_code 
    test_mdr_codes = ['DO013', 'BO014', 'CL014', 'AR017', 'VU008', 'TJ029', 'SO009', 'PH040', 'RS014', 'FJ004', 'CD031', 'MY005', 'LA007', 'CU006', 'AM006']
    results = {}
    for lead in test_mdr_codes:
        lead = f'MDR{lead}'

        # Get alex new
        def parse_PDF_combined_new(lead):
            appeal = Appeal(mdr_code=lead)
            gf_parsed = {
                'lead': lead,
                'Hazard': appeal.official_hazard_name, 
                'Country': appeal.country,
                'Region': appeal.region,
                'Date': appeal.start_date
            }
            dref_document = appeal.get_dref_final_report()
            exs_parsed, _ = dref_document.get_challenges_lessons_learned()
            all_parsed = exs_parsed.merge(pd.DataFrame([gf_parsed]), on='lead')
            return all_parsed
        all_parsed_new = parse_PDF_combined_new(lead)

        # Get old version
        all_parsed = parse_PDF_combined(lead)

        # Check if the same as old version
        results[lead] = all_parsed_new.equals(all_parsed)
        print(all_parsed_new)
        print(all_parsed)
        print(f'{lead}: {("Pass" if results[lead] else "FAIL")}')
        if not results[lead]:
            compare = all_parsed.compare(all_parsed_new)
            print(compare)
            
    failed_mdr_codes = [code for code in results if not(results[code])]
    passed_mdr_codes = [code for code in results if results[code]]
    print(f"\n\nPASS for codes: {failed_mdr_codes}")
    print(f"\n\nFAIL for codes: {passed_mdr_codes}")
    
    return all(results)


@app.post("/parse/")
async def run_parsing(
    appeal_code: str = Query(
        default=None,
        title="Appeal code",
        description="Starts with 'MDR' followed by 5 symbols. <br> Some available codes: DO013, BO014, CL014, AR017, VU008, TJ029, SO009, PH040, RS014, FJ004, CD031, MY005, LA007, CU006, AM006",
        min_length=8,
        max_length=8,
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
    try:
        appeal = Appeal(mdr_code=appeal_code)
        appeal_data = pd.DataFrame([{
            'lead': appeal_code,
            'Hazard': appeal.official_hazard_name, 
            'Country': appeal.country,
            'Region': appeal.region,
            'Date': appeal.start_date
        }])
        appeal_document = appeal.get_dref_final_report()
        exs_parsed, _ = appeal_document.get_challenges_lessons_learned()
        all_parsed = exs_parsed.merge(appeal_data, on='lead')
    except ExceptionNotInAPI:
        raise HTTPException(status_code=404, 
                            detail=f"{appeal_code} doesn't have a DREF Final Report in IFRC GO appeal database")
    except ExceptionNoURLforPDF:
        raise HTTPException(status_code=404, 
                            detail=f"PDF URL for Appeal code {appeal_code} was not found using IFRC GO API call appeal_document")
    except:
        raise HTTPException(status_code=500, detail="PDF Parsing didn't work by some reason")

    df = all_parsed[['Modified Excerpt', 'Learning', 'DREF_Sector', 'lead', 'Hazard', 'Country', 'Date', 'Region']]
    df = df.rename(columns={'lead': 'Appeal code', 'Modified Excerpt': 'Excerpt'})

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
        all_parsed = parse_PDF_combined(lead)
    except ExceptionNotInAPI:
        raise HTTPException(status_code=404, 
                            detail=f"{lead} doesn't have a DREF Final Report in IFRC GO appeal database")
    except ExceptionNoURLforPDF:
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
        initialize_apdo(refresh=True)
        initialize_aadf(refresh=True)

        # NB: we need to do import again, 
        # otherwise updated apdo, aadf won't be accessible here
        # (even though they got updated in parser_utils)
        from dref_parsing.parser_utils import apdo, aadf
        output = f'GO API Reload: {len(aadf)} items in appeal, {len(apdo)} items in appeal_documents'
        output += ' (only DREF Final Reports are selected)'
    except:
        raise HTTPException(status_code=500, detail="Error while accessing GO API data")
    return output 

    # Command to start API:
    # uvicorn main:app --reload



