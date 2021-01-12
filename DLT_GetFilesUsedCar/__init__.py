# =============================================================================
# Created By: Perath C (perath@inteltion.com) 
# Created Date:   29/12/2020
# Updated By: Perath C (perath@inteltion.com) 
# Updated Date:   12/1/2021
# =============================================================================
# Function: DLT_GetFilesUsedCar 
# Version: 0.0.1

# Description: To get data from DLT website function Used Car Transfer and store in local directory

# Parameter:    dest_container_name - Target container name
#               dest_path - Target path in container
#               asat_dt - ASAT_DT from ETL

# Constants:    LINK_WEB - Link of raw data file
#               SLEEP_TIME - Sleep solve animation delay issue
#               DEST_LOCAL_PATH - Path of file in docker container
#               MATCH - Match number with month in Thai language
                
# =============================================================================
# Changes:
# Version   Date            Updated By          Description
# 0.0.1     29/12/2020      Perath C            Initital Version
# =============================================================================

import azure.functions as func
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

LINK_WEB = 'https://web.dlt.go.th/statistics/'
SLEEP_TIME = 1
DEST_LOCAL_PATH = "./download/dlt/usedcar/"

MATCH = {
       1 : 'มกราคม',
       2 : 'กุมภาพันธ์',
       3 : 'มีนาคม',
       4 : 'เมษายน',
       5 : 'พฤษภาคม',
       6 : 'มิถุนายน',
       7 : 'กรกฎาคม',
       8 : 'สิงหาคม',
       9 : 'กันยายน',
       10 : 'ตุลาคม',
       11 : 'พฤศจิกายน',
       12 : 'ธันวาคม'
      }

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # Setup directory
    logging.info('Python HTTP trigger function processed a request.')

    # Get parameter
    try:
        req_body = req.get_json()
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

    full_date = str(MATCH[month]) + ' '+str(year_param)

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
            #  Link of raw data website
            try:
                await page.goto('https://web.dlt.go.th/statistics/', waitUntil="load")
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
            
            # Click ข้อมูลด้านทะเบียนรถ
            await page.click("//*[@id='cssmenu']/ul/li[4]")
            time.sleep(SLEEP_TIME)
            
            # Click สถิติการดำเนินการเกี่ยวกับทะเบียนและภาษีรถ
            await page.click("//*[@id='stat_car']/span")
            
            # Click drop down
            await page.click('select[name="year_search1"]')

            # Get list item in drop down and choose the secound choice
            listyear = await page.querySelectorAll('select[name="year_search1"]>option')

            # Loop all values in to list
            temp = []
            for x in range(len(listyear)): 
                y = await page.evaluate('(year) => year.innerHTML',listyear[x])                 
                temp.append(y)

            # Check that asatdt have in list
            if full_date in str(temp):
                # For delay of animation
                time.sleep(SLEEP_TIME)

                # Select option by using parameter from above
                logging.info('before select download file')
                await page.selectOption('select#year_search1', { 'label': full_date })

                # Sleep for protect last file download incomplete (for os.list detect the last file)
                time.sleep(SLEEP_TIME) 

                # Loop for protecting download incompleted
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
                    status = {'StatusCode' :500 ,'NumberOfFiles': 0 ,'Description' : 'Not valid container'}
                    # Delete raw file in docker
                    files = glob.glob(DEST_LOCAL_PATH+"*")
                    for f in files:
                        os.remove(f)
                    return func.HttpResponse(json.dumps(status),mimetype = "application/json", status_code=500)
            else:
                # Not find target on website
                status = {'StatusCode' : 500,'NumberOfFiles': 0 }
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