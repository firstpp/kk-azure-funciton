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
#               export_filename - filename extracted from url
#               dest_container_name - name of destination container in blob storage
#               dest_path - directory path in blob storage
#               asat_dt - date of register
#               group - group of each file
#               
#              
# Constants:    XPATH - XPATH parameter for download link in website
#               COL_NUM - columns number (default equal to 2) 
#               DOWNLOAD_PATH - path to download file in local
# Return: Csv files from Tide websites 
# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     29/12/2020      Perath C           Initital Version
# 0.0.2     29/12/2020      Saris K            Add comment 
# 0.0.3     08/01/2021      Saris K            Upload to blob
# =============================================================================
import logging
import azure.functions as func
import Helpers
import json
import numpy as np
import Helpers
import pandas as pd
import os 
import glob

#Constants
XPATH = '//*[@id="list-data"]/ul/li[position()>=2]/text()' 
COL_NUM = 2 
DEST_LOCAL_PATH ='./download/tide/'

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        url = req_body.get('url')
        filename = req_body.get('export_filename')
        dest_container_name = req_body.get('dest_container_name')
        dest_path = req_body.get('dest_path')
        group = req_body.get('group')
        asat_dt = req_body.get('asat_dt')
    except (Exception, ValueError ) as x :
        status = {'Status' : 404 , 'Number_of_downloaded_files' : 0, 'Description' : x }
        logging.error(ValueError)
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404 )

    if not os.path.exists(DEST_LOCAL_PATH):
        logging.info("Files doesn't exist in download path") 
        
        #Initial make a folder of the report
        os.makedirs(DEST_LOCAL_PATH)    
    try:
        data = Helpers.extract_element(url, XPATH)
    except :
        status = {'Status' : 404 , 'Number_of_downloaded_files' : 0, 'Description' : "Target website not avaiable" }
        logging.error(ValueError)
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404 )

    np.array(data)
    changed_out = np.array_split(data,COL_NUM)
    df = pd.DataFrame(index=changed_out[0:][0:])
    # change dataframe to csv file 
    df.to_csv(path_or_buf = DEST_LOCAL_PATH + filename, header=False)
    
    try:
        Helpers.upload_to_blob(dest_container_name,DEST_LOCAL_PATH + filename, dest_path + group + "/" + asat_dt + "/" + filename)
    except ValueError :
        files = glob.glob(DEST_LOCAL_PATH+'*')
        for item in files:
            os.remove(item)
            number_of_downloaded_files = len(os.listdir(DEST_LOCAL_PATH))
        status = {'Status' : 500, 'Number_of_downloaded_files' : number_of_downloaded_files, 'Description' : 'Not valid containner' }
        logging.error(ValueError)
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 500)
    number_of_downloaded_files = len(os.listdir(DEST_LOCAL_PATH))
    logging.info('Python HTTP trigger function processed a request.')
    status = {'Status' : 'Success', 'Number of file' :number_of_downloaded_files }
    
    files = glob.glob(DEST_LOCAL_PATH+'*')
    for item in files:
        os.remove(item)

    status = {'Status' : 200 , 'Number_of_downloaded_files' : number_of_downloaded_files,'Description' : 'The request has succeeded'}
    return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=200)