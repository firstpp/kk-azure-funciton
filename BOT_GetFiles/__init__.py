# =============================================================================
# Created By: Wattanapong P. (Wattanapong@inteltion.com) 
# Created Date:   29/12/2020
# Updated By: Wattanapong P (Wattanapong@inteltion.com) 
# Updated Date:   29/12/2020
# =============================================================================
# Function: HttpExample 
# Version: 0.0.1

# Description: To get data from BOT website and store in local directory

# Parameters:   url - website url
#               dest_container_name - name of destination container in blob storage
#               report_group_code - name of a group of report such as FC_EI_081 
#               dest_path - directory path in blob storage
#               asat_dt - date of register
#               tr, td, div, a - Name of the element of html structure on the website

# Constants:    DOWNLOAD_PATH - directory path in local


# Return: Excel files from BOT website 
# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     29/12/2020      Wattanapong P.      Initital Version
# =============================================================================

import logging
import azure.functions as func
from bs4 import BeautifulSoup
import os
import cgi
import requests
import Helpers
import json
import glob


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        req_body = req.get_json()
        url = req_body.get('url')
        report_group_code = req_body.get('report_group_code')
        asat_dt = req_body.get('asat_dt')
        dest_container_name = req_body.get('dest_container_name')
        dest_path = req_body.get('dest_path')

    except (Exception, ValueError ) as x :
        status = {'Status' : 404 , 'Number_of_downloaded_files' : 0, 'Description' : x }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404 )

    DOWNLOAD_PATH ='./download/bot/'
    if not os.path.exists(DOWNLOAD_PATH):
        logging.info("Files doesn't exist in download path") 
        
        # initial make a folder of the report
        os.makedirs(DOWNLOAD_PATH)
 
    try :
        page = requests.get(url)
    except :
        status = {'Status' : 404, 'Number_of_downloaded_files' : 0, 'Description' : 'Target website not avaiable' }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404)
    
    soup = BeautifulSoup(page.content, 'html.parser')

    #find only tr elements in html on url website
    trs = soup.find_all('tr')

    #find a list of tr element that contain a report

    trs = [tr for tr in trs if (tr.find('td').text.strip() != 'Report ID' or not tr.find(
        'td').text.strip()) and report_group_code.upper() in tr.find('td').text.strip().upper()]
    
    if trs == []:
        status = {'Status' : 501, 'Number_of_downloaded_files' : 0, 'Description' : 'Not valid report_group_code' }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 501)

    items = []

    for tr in trs:
        report_name = tr.find_all('td')[0].find('div').text.strip()
        link = tr.find_all('td')[2].find('a')['href']
        logging.info(link)
        item = {
            'report_name': report_name,
            'url': link
        }
       
        items.append(item)
     
    
    logging.info('Start downloading process')
    [Helpers.bot_download(item.get('url'), DOWNLOAD_PATH) for item in items]

    number_of_downloaded_files = len(os.listdir(DOWNLOAD_PATH))

    logging.info('Start files uploading to blob storage')
    # upload files to blob storage in  
    for item in os.listdir(DOWNLOAD_PATH):
        try:
            Helpers.upload_to_blob(dest_container_name, DOWNLOAD_PATH+item, dest_path +'/'+report_group_code+'/'+ asat_dt+'/'+item)
        except:
            files = glob.glob(DOWNLOAD_PATH+'/*')
            for item in files:
                os.remove(item)
                number_of_downloaded_files = len(os.listdir(DOWNLOAD_PATH))
            status = {'Status' : 500, 'Number_of_downloaded_files' : number_of_downloaded_files,'Description' : 'Not valid container'}
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 500)
            
    logging.info('Removing all files in DOWNLOAD_PATH')
    # removing all files in DOWNLOAD_PATH
    files = glob.glob(DOWNLOAD_PATH+'/*')
    for item in files:
        os.remove(item)


    logging.info('Python HTTP trigger function completed.')
    status = {'Status' : 200 , 'Number_of_downloaded_files' : number_of_downloaded_files,'Description' : 'The request has succeeded'  }

    return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=200)