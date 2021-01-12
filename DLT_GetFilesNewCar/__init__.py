# =============================================================================
# Created By: Perath C (perath@inteltion.com) 
# Created Date:   29/12/2020
# Updated By: Perath C (perath@inteltion.com) 
# Updated Date:   12/1/2021
# =============================================================================
# Function: DLT_GetFilesNewCar 
# Version: 0.0.1

# Description: To get data from DLT website function New Car Sold by Region and store in local directory

# Constants:    LINK_WEB - Link of raw data file
#               SLEEP_TIME - Sleep solve animation delay issue
#               DEST_PATH - download folder in local directory 
#               SLEEP_TIME - Need to delay the program for wait the animation of website end

# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     29/12/2020      Perath C            Initital Version
# =============================================================================

import azure.functions as func
import asyncio
from playwright import async_playwright
import os
import time
import logging

import datetime
import dateutil.relativedelta
import calendar
import Helpers
import json
import glob


DEST_LOCAL_PATH = "./download/dlt/newcar/"
LINK_WEB = 'https://web.dlt.go.th/statistics/'
SLEEP_TIME = 1

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # Setup directory
    logging.info('Python HTTP trigger function processed a request.')

    # Get parameter
    try:
        req_body = req.get_json()
        car_type = req_body.get('car_type')
        dest_path = req_body.get('dest_path')
        group = req_body.get('group')
        dest_container_name = req_body.get('dest_container_name')
        asat_dt = req_body.get('asat_dt')
    
    except (Exception, ValueError ) as x :
        status = {'Status' : 404 , 'Number_of_downloaded_files' : 0, 'Description' : x }
        return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code= 404 )

    # Change format of asat_dt for match with raw data date (Logic: if asat_dt is not end of the month minus it 1 month)
    day = int(asat_dt[-2:])
    year = int(asat_dt[:-4])
    month = int(asat_dt[-4:][:-2])
    lastday = calendar.monthrange(year, month)[1]

    # if asatdt = lastday of month no need to minus 1 month
    if day == lastday:
        logging.info('Yes EOM')
        year_param = str(year+543)
        new_asat_dt = asat_dt
    else :
        logging.info('Not EOM')
        date = str(day)+"-"+str(month)+"-"+str(year)
        new_date = datetime.datetime.strptime(date, "%d-%m-%Y")
        one_month = dateutil.relativedelta.relativedelta(months=1)
        date_minus_month = new_date - one_month
        month = date_minus_month.month
        year_param = str(int(date_minus_month.year)+543)
        new_lastday = calendar.monthrange(date_minus_month.year, date_minus_month.month)[1]
        new_asat_dt = str(date_minus_month.year)+str(date_minus_month.month)+str(new_lastday)

    async with async_playwright() as p:

            browser = await p.chromium.launch(headless = True)
            context = await browser.newContext()
            page = await context.newPage()
            page.setDefaultNavigationTimeout(0)
            client = await context.newCDPSession(page)
            await client.send('Page.setDownloadBehavior', {
             'behavior': 'allow',
             'downloadPath': DEST_LOCAL_PATH
             }
             )
            # Link of raw data website
            try:
                await page.goto(LINK_WEB, waitUntil="load")
            except:
                # Target website not avaiable
                status = {'StatusCode' : 404,'NumberOfFiles': 0, 'Description' : "Target website not avaiable" }
                return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=404)

            # Click for close popup banner
            try:
                await page.click("span[class='closes btn btn-danger']")
            except Exception:
                logging.error("Not found pop up banner to close")
                pass

            # Click รายงานรถจดทะเบียนใหม่ป้ายแดง
            await page.click("button[name='btn-all2']")

            # Click ข้อมูลจำนวนรถใหม่ (ป้ายแดง) ที่จดทะเบียนโดยแยกยี่ห้อ รายเดือน
            await page.click("div[id='heading2']")
            time.sleep(SLEEP_TIME)

            logging.info('before select download file')

            temp_car_list = []
            listcar = await page.querySelectorAll('select[name="cartype2"]>option')
            # Loop all values in to list
            for x in range(len(listcar)): 
                c = await page.evaluate('(cartype2) => cartype2.innerHTML',listcar[x])                 
                temp_car_list.append(c)

            full_cartype = 0
            for i in range(len(temp_car_list)): 
                try:
                    list_type = temp_car_list[i].split(" ")[0].split(".")[1]
                    if list_type == car_type:
                        full_cartype = temp_car_list[i]
                        break
                except:
                    pass
            
            if full_cartype == 0:
                # Not find target on website
                status = {'StatusCode' : 500,'NumberOfFiles': 0 , 'Description' : 'Invalid cartype on website'}
                return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=500)

            temp_year_list = []
            await page.selectOption('select#cartype2', { 'label': full_cartype })   
            # For delay of year option list to appear 
            time.sleep(SLEEP_TIME)
            # Get list item in drop down and choose the secound choice
            listyear = await page.querySelectorAll('select[name="year_search2"]>option')

            # Loop all values in to list
            for x in range(len(listyear)): 
                y = await page.evaluate('(year) => year.innerHTML',listyear[x])                 
                temp_year_list.append(y)

            # Check that asatdt have in list
            if year_param in str(temp_year_list):
                logging.info('Found new file')
            
                # Select option by using passing parameter
                await page.selectOption('select#year_search2', { 'label': year_param })
                
                # Check status file start and finish download
                logging.info('Check Download Finished')

                # Sleep for protect last file download incomplete (for os.list detect the last file)
                time.sleep(SLEEP_TIME) 

                while (True):
                    Newest_Folder = os.listdir(DEST_LOCAL_PATH)
                    if all(item.endswith('.xls') for item in Newest_Folder): 
                            break
                    else:
                        time.sleep(SLEEP_TIME)

                export_filename = Newest_Folder[0]
                try:
                    Helpers.upload_to_blob(dest_container_name,DEST_LOCAL_PATH + export_filename,dest_path+group+"/"+new_asat_dt+"/"+export_filename)
                except:
                    # Not valid container
                    status = {'StatusCode' :500 ,'NumberOfFiles': 0,'Description' : 'Not valid container'}
                    # Delete raw file in docker
                    files = glob.glob(DEST_LOCAL_PATH+"*")
                    for f in files:
                        os.remove(f)
                    return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=500)

            else:
                # Not find target on website
                status = {'StatusCode' : 500,'NumberOfFiles': 0 , 'Description' : 'Invalid year on input car_type'}
                return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=500)

             # Count number of file for return in json form
            list_of_files = os.listdir(DEST_LOCAL_PATH)
            NumberOfFiles = len(list_of_files)

            # Delete raw file in docker
            files = glob.glob(DEST_LOCAL_PATH+"*")
            for f in files:
                os.remove(f)

            logging.info('Python HTTP trigger function completed.')

            await browser.close()

            # Success
            status = {'StatusCode' : 200,'NumberOfFiles': NumberOfFiles,'Description' : 'The request has succeeded' }
            return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=200)