import calendar
import time
import logging

import datetime
import dateutil.relativedelta
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

asat_dt = "20200111"

day = int(asat_dt[-2:])
year = int(asat_dt[:-4])
month = int(asat_dt[-4:][:-2])
lastday = calendar.monthrange(year, month)[1]
if day == lastday:
    logging.info('Yes EOM')
    year_param = str(year+543)
else :
    logging.info('Not EOM')
    date = str(day)+"-"+str(month)+"-"+str(year)
    new_date = datetime.datetime.strptime(date, "%d-%m-%Y")
    one_month = dateutil.relativedelta.relativedelta(months=1)
    date_minus_month = new_date - one_month
    month = date_minus_month.month
    year_param = str(int(date_minus_month.year)+543)
full_date = str(MATCH[month]) + ' '+str(year_param)
print(full_date)