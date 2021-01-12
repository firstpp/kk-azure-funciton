import logging
import os
import cgi
import requests
from azure.storage.blob import BlobServiceClient, BlobClient
import subprocess
from urllib.request import urlopen
from lxml import etree,html

from bs4 import BeautifulSoup
from datetime import date
import pandas as pd
import datetime as dt
from playwright import async_playwright
import time
import asyncio
import calendar


# def is_downloadable(url: str):
#     # Does the url contain a downloadable resource
#     h = requests.head(url, allow_redirects=True)
#     header = h.headers
#     content_type = header.get('content-type')
#     if 'text' in content_type.lower():
#         return False
#     if 'html' in content_type.lower():
#         return False
#     return True


# def download(url: str, download_path: str, filename=None) -> str:
#     logging.info('Downloading:\t' + url)

#     r = requests.get(url, allow_redirects=True)
#     if not filename:
#         filename = cgi.parse_header(
#             r.headers['Content-Disposition'])[-1]['filename']
#     download_filepath = os.path.join(download_path, filename)
#     open(download_filepath, 'wb').write(r.content)
#     return download_filepath

#     # Create a blob client using the local file name as the name for the blob
#     blob_client = blob_service_client.get_blob_client(
#         container=container_name, blob=filename)

#     # Upload the file to blob
#     logging.info("Uploading to Azure Storage as blob:\t" + filename)
#     with open(filepath, "rb") as data:
#         blob_client.upload_blob(data, overwrite=True)
#         logging.info('Upload:\t' + str(filepath) + '\tComplete!!')


# def get_download_link(url, xpath):
#     logging.info(
#         "python ./Util/get_download_link.py '{0}' '{1}'".format(url, xpath))
#     result = subprocess.check_output(
#         "python ./Util/get_download_link.py '{0}' '{1}'".format(url, xpath), shell=True, encoding='utf-8')
#     return list(result.replace('\n', '').split('|'))


def capture_pdf(url, outputFilePath):
    logging.info(
        "python ./Util/capture_pdf.py '{0}' '{1}'".format(url, outputFilePath))

    os.system(
        "python ./Util/capture_pdf.py '{0}' '{1}'".format(url, outputFilePath))
    # result = subprocess.check_output(
    #     "python ./Util/capture_pdf.py '{0}' '{1}'".format(url, outputFilePath), shell=True, encoding='utf-8')
    # return list(result.replace('\n', '').split('|'))

def extract_element(url, xpath):
    """[execute function for collecting data from url and xpath]

    Args:
        url ([list]): [url that need to extract the data]
        xpath ([str]): [xpath of data that need to be downloaded]

    Returns:
        [list]: [return list of data that from the url and xpath]
    """    
    page = requests.get(url)
    tree = html.fromstring(page.content) 
    root = html.tostring(tree)
    items = tree.xpath(xpath)
    return items

def get_url_and_report_name(dict_list, bank_code, asat_dt):
    """[function for collecting a list of dictionaries that contain keys of url to download, report_name and ending_date keys of last quarter]

    Args:
        dict_list ([list]): [empty list parameter to collect a result of this function]

    Returns:
        [list]: [return a list of dictionaries that have url download, report_name and ending_date keys of last quarter]
    """   
    # asat_dt = yyyymmdd -> str
    try:
        day = int(asat_dt[6:8])
        month = int(asat_dt[4:6])
        year = int(asat_dt[0:4])
        quarter = (pd.Timestamp(dt.date(year,month,day)).quarter)
        get_starting_month = {1 : '01', 2 :'04', 3 :'07', 4 :'10'} #get a starting month of present quarter
        mm = get_starting_month[quarter]
        get_last_month = {1 : '12', 2 :'03', 3 :'06', 4 :'09'} #get a last month of last quarter
        last_mm = get_last_month[quarter]
        # get a ending date of the report
        if quarter == 1 :
            lastday = calendar.monthrange(year-1, int(last_mm))[1]
            ending_date = str(year-1)+last_mm+str(lastday)
        else:
            lastday = calendar.monthrange(year, int(last_mm))[1]
            ending_date = str(year)+last_mm+str(lastday)
    except:
        logging.info('Invalid asat_dt format')
        return dict_list

    # Get a url of each symbols from a date of starting of quarter to asat_dt
    url = 'https://www.set.or.th/set/newslist.do?source=&symbol='+bank_code+'&securityType=&newsGroupId=3&headline=&from=01%2F'+str(mm)+'%2F'+str(year)+'&to='+str(day)+'%2F'+str(month)+'%2F'+str(year)+'&submit=Search&language=en&country=US#content'
    logging.info('Going into '+url)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    tbody = soup.find_all('tbody')
    soup2 = BeautifulSoup(str(tbody),'html.parser')

    tds = soup2.find_all('td')
    
    # Get a array of a line that have a report that we needed
    tds = [td for td in tds if ( 'zip'.upper() in td.text.strip().upper())]

    # If have 0 item in tds that mean the report isn't available yet
    # If have 1 item in tds that mean the report have only unreviewed version
    # If have 2 item in tds that mean the report have reviewed and unreviewed version
    if len(tds) == 0:
        logging.info("Report isn't available")
        return dict_list

    elif len(tds) == 1:
        report_name = bank_code + '_unreviewed'
    else:
        report_name = bank_code + '_reviewed'

    # get a url to download a zip files
    link = 'https://www.set.or.th'+tds[0].find('a')['href']
    
    # save a url to download a zip file and report name of the symbol and date of data in report
    url_report_name = {
        'url' : link,
        'report_name' : report_name,
        'ending_date' : ending_date
    }
    
    logging.info('Url to download ' + report_name + ' is ' + url_report_name['url'])

    dict_list.append(url_report_name)
        

    return dict_list

def bot_download(url, download_path):
    r"""[function download files and save as download path]

    Args:
        url ([str]): [url for download files]
        download_path ([str]): [folder path as \download root directory\ report name ]
    """       
    logging.info('Downloading:\t' + url)
    r=requests.get(url, allow_redirects=True)

    filename=cgi.parse_header(
        r.headers['Content-Disposition'])[-1]['filename']
    download_filepath=os.path.join(download_path, filename)

    #write content as binary mode
    open(download_filepath, 'wb').write(r.content)  
    print('Download {} completed'.format(download_filepath))
    
def bot_filter_download(items, download_root_dir):
    """[fillter a version of a report to download and return as a list of url and download path]

    Args:
        items ([list]): [list of dictionary that contain report name and url for download keys]
        download_root_dir ([type]): [download root directory]

    Returns:
        [list]: [list of dictionary that contain url for download and download path keys]
    """    

    result=[]

    for item in items[::-1]:
        
        download_path=os.path.join(download_path, item.get('report_name'))

        item={
            'url': item.get('link'),
            'download_path': download_path
        }
        result.append(item)
        if not os.path.exists(download_path):
            logging.info("Files doesn't exist in download path") 
            print('Make dir')
            #Initial make a folder of the report
            os.makedirs(download_path) 
            result.append(item)
            continue
        else:
            logging.info("File is exist in download path")
            result.append(item)
            continue

    return result

def upload_to_blob(container_name: str, filepath: str, blob_storage_path: str):
    """[function to upload files from local path to container at blob_storage_oath]

    Args:
        container_name (str): [container name]
        filepath (str): [a path of file in local that will be upload to blob storage]
        blob_storage_path (str): [directory path in blob storage]
    """    
    con_string = BlobServiceClient.from_connection_string(os.environ['AzureWebJobsStorage'])
    blob = con_string.get_blob_client(
        container=container_name, blob=blob_storage_path)
    with open(filepath, "rb") as data:
        blob.upload_blob(data, overwrite=True)