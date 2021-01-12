# =============================================================================
# Created By: Perath C (perath@inteltion.com) 
# Created Date:   29/12/2020
# Updated By: Saris K (saris@inteltion.com) 
# Updated Date:   29/12/2020
# =============================================================================
# Function: Tide_GetFiles
# Version: 0.0.2

# Description: To get data from Tide website and store in local directory

# Parameters:   url - website url
#               filename - filename extracted from url
#              
# Constants:    XPATH - XPATH parameter for download link in website
#               COL_NUM - columns number (default equal to 2) 
#               DEST_PATH - path to download file
# Return: Csv files from Tide websites 
# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     29/12/2020      Perath C           Initital Version
# 0.0.2     29/12/2020      Saris K            Add comment 
# =============================================================================
import logging
import azure.functions as func
import Helpers
import json

import azure.functions as func
import numpy as np
import Helpers
import pandas as pd

#Constants
XPATH = '//*[@id="list-data"]/ul/li[position()>=2]/text()' 
COL_NUM = 2 
DEST_PATH = "./download/tide/" 

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    # Get url and filename from postman by using POST method
    try:
        req_body = req.get_json()
        url = req_body.get('url')
        filename = req_body.get('name')
    
    except ValueError:
        logging.error(ValueError)
        return func.HttpResponse(
        "No Url in body",
        status_code=400
        )
    
    data = Helpers.extract_element(url, XPATH)
    np.array(data)
    changed_out = np.array_split(data,COL_NUM)
    df = pd.DataFrame(index=changed_out[0:][0:])
    # change dataframe to csv file 
    df.to_csv(path_or_buf = DEST_PATH + filename+".csv", header=False)
   
    logging.info('Python HTTP trigger function processed a request.')
    status = {'Status' : 'Success'}
    return func.HttpResponse(
        json.dumps(status),
        mimetype = "application/json",
        status_code=200
    )