# =============================================================================
# Created By: Perath C (perath@inteltion.com) 
# Created Date:   6/1/2021
# Updated By: Perath C (perath@inteltion.com) 
# Updated Date:   12/1/2021
# =============================================================================
# Function: Bank_CapturePdf 
# Version: 0.0.1

# Description: To get data from bank website of P Loan rate by segment and store in local directory

# Parameter:    url - Target website to export data
#               export_filename - export filename with extension
#               dest_container_name - Target container name
#               dest_path - Target path in container
#               asat_dt - ASAT_DT from ETL

# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     6/1/2021        Perath C            Initital Version
# =============================================================================

import logging

import azure.functions as func
from playwright import async_playwright
import Helpers
import asyncio
import sys
import json
import os
import glob

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get parameter
    try:
        req_body = req.get_json()
        url = req_body.get('url')
        bank_code = req_body.get('bank_code')
        export_filename = req_body.get('export_filename')
        dest_path = req_body.get('dest_path')
        dest_container_name = req_body.get('dest_container_name')
        asat_dt = req_body.get('asat_dt')
    
    except (Exception, ValueError ) as x :
        status = {'Status' : 404 , 'Number_of_downloaded_files' : 0, 'Description' : x }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404 )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = True)
        page = await browser.newPage()
        page.setDefaultNavigationTimeout(0)
        await page.setViewportSize(
            width=1680,
            height=1050
        )
        # Go to website and check is website avaiable
        try:
            await page.goto(url, waitUntil="load")
        except:
            # Target website not avaiable
            status = {'StatusCode' : 404,'NumberOfFiles': 0 , 'Description' : "Target website not avaiable"}
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=404)

        if bank_code == "CITY":
            await page.click("//*[@id='inpagenav-1-1-c-Tab']/span")
            # await page.screenshot(path=f'BBexample.png')

        await page.emulateMedia('screen')
        height = str(await page.evaluate('''() => document.documentElement.offsetHeight ''')) + 'px'
        width = str(await page.evaluate('''() => document.documentElement.offsetWidth ''')) + 'px'

        # Set folder for docker container
        folder = export_filename.split('.')[0]
        dest_local_path = "./download/bank/"+folder+"/"

        # Check download_path if not exist then create it
        if not os.path.exists(dest_local_path):
          os.makedirs(dest_local_path)

        # Page setup
        await page.pdf(
            path= dest_local_path+export_filename,
            printBackground=True,
            width=width,
            height=height
        )

        # Upload file from docker container to blob
        try:
            Helpers.upload_to_blob(dest_container_name,dest_local_path + export_filename,dest_path+bank_code+"/"+asat_dt+"/"+export_filename)
        except:
            # Not valid container
            status = {'StatusCode' :500 ,'NumberOfFiles': 0,'Description' : 'Not valid container' }
            # Delete raw file in docker
            files = glob.glob(dest_local_path+"*")
            for f in files:
                os.remove(f)
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=500)

        # Count number of file for return in json form
        list_of_files = os.listdir(dest_local_path)
        NumberOfFiles = len(list_of_files)

        # Delete raw file in docker
        files = glob.glob(dest_local_path+"*")
        for f in files:
            os.remove(f)
        
        logging.info('Python HTTP trigger function completed.')
        await browser.close()
        # Success
        status = {'StatusCode' : 200,'NumberOfFiles': NumberOfFiles,'Description' : 'The request has succeeded' }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=200)