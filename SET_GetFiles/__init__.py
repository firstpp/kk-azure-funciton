# =============================================================================
# Created By: Wattanapong P. (Wattanapong@inteltion.com) 
# Created Date:   29/12/2020
# Updated By: Wattanapong P (Wattanapong@inteltion.com) 
# Updated Date:   29/12/2020
# =============================================================================
# Function: HttpExample 
# Version: 0.0.1

# Description: To get data from SET website and store in local directory

# Parameters:   url - website url
#               dest_container_name - name of destination container in blob storage
#               bank_code - name of a symbol of report such as scb
#               dest_path - directory path in blob storage
#               asat_dt - date of register
#               tr, td, div, a - Name of the element of html structure on the website
#               download_path - directory path in local

# Constants:    
#               SLEEP_TIME - need to delay the program for starting download process
#               XPATH - xpath parameter for download link in website

# Return: zip files from SET website 
# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     29/12/2020      Wattanapong P.      Initital Version
# =============================================================================

import logging
import azure.functions as func
import os
from bs4 import BeautifulSoup
import requests
from datetime import date
import pandas as pd
import datetime as dt
from lxml import html
from playwright import async_playwright
import time
import asyncio
import Helpers
import json
import glob


# pylint: disable=unsubscriptable-object
async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    dict_list = []
    XPATH_SET = '//*[@id="main-body"]/div/div/div[2]/div/div[1]/div/a' # os.environ["XPATH_SET"]
    time.sleep(os.environ["SLEEP_TIME"])
    
    try:
        req_body = req.get_json()
        bank_code = req_body.get('bank_code')
        asat_dt = req_body.get('asat_dt')
        # format asat_dt = yyyymmdd
        dest_container_name = req_body.get('dest_container_name')
        dest_path = req_body.get('dest_path')

    except (Exception, ValueError ) as x :
        status = {'Status' : 404 , 'Number_of_downloaded_files' : 0, 'Description' : x }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404 )

    # Get a array of dictionaries of url to download files and report name
    try :
        Helpers.get_url_and_report_name(dict_list, bank_code, asat_dt)
        logging.info(dict_list)
        if dict_list == [] :
            status = {'Status' : 501 , 'Number_of_downloaded_files' : 0, 'Description' : "Report isn't available or invalid expected_input" }
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 501 )
    except :
        pass

    # Make initial directory
    download_path = './download/set/'+ dict_list[0]['report_name']+'/'
    if not os.path.exists(download_path):
        logging.info("download_path isn't exist") 
        
        # initial make a folder of the report
        os.makedirs(download_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = True)
        context = await browser.newContext()
        page = await context.newPage()
        page.setDefaultNavigationTimeout(0)
        client = await context.newCDPSession(page)
        await client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_path }
            )
        
        # Going to a url
        try:
            await page.goto(dict_list[0]['url'])

        except:
            status = {'Status' : 404, 'Number_of_downloaded_files' : 0, 'Description' : "Target website not avaiable" }
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404)

        # Click a element on url website to start a download process
        try:
            await page.click(XPATH_SET)
        except:
            status = {'Status' : 501, 'Number_of_downloaded_files' : 0, 'Description' : "Target element isn't valid"}
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 501)

        logging.info('Downloading '+ dict_list[0]['report_name'])

        # Need to delay a program for waiting a download process to start
        time.sleep(os.environ["SLEEP_TIME"])
        check_for_download = True
    
        # While loop to check if download process is completed or not
        # If download process isn't completed then time sleep for waiting download process
        list_of_files = os.listdir(download_path)

        while check_for_download == True :

            list_of_files = os.listdir(download_path)

            if all(item.endswith('.zip') for item in list_of_files): 
                await browser.close()
                check_for_download =False

            else:
                logging.info(dict_list[0]['report_name'] + ' is still being downloaded')
                time.sleep(os.environ["SLEEP_TIME"])
                check_for_download = True         
        
        logging.info('Download Completed')
        number_of_downloaded_files = len(os.listdir(download_path))
        logging.info(number_of_downloaded_files)

        logging.info('Start files uploading to blob storage')
        # upload files to blob storage in
        for item in os.listdir(download_path):
            logging.info(item)
            try:
                Helpers.upload_to_blob(dest_container_name, download_path+item, dest_path + dict_list[0]['ending_date']+'/'+dict_list[0]['report_name']+'/'+item)
            except:
                files = glob.glob(download_path+'/*')
                for item in files:
                    os.remove(item)
                    number_of_downloaded_files = len(os.listdir(download_path))
                status = {'Status' : 500, 'Number_of_downloaded_files' : number_of_downloaded_files,'Description' : 'Not valid container'}
                return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 500)

        logging.info('Removing all files in download_path')
        # removing all files in download_path
        files = glob.glob(download_path+'/*')
        for item in files:  
            os.remove(item)


    logging.info('Python HTTP trigger function completed.')
    status = {'Status' : 200 , 'Number_of_downloaded_files' : number_of_downloaded_files,'Description' : 'The request has succeeded'}

    return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=200)