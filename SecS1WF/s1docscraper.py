# -*- coding: utf-8 -*-
"""S1DocScraper.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KGbLKHHkgg7d7GHv5F49gJlcCiZPUCxt

# S1 data scraping 
Scraping data from sec.gov to get updated data about various companies that are going public in the US.

## Libraries import
"""

from datetime import date
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import re

headers={'User-Agent':"Vishwajeet Hogale (vishwajeethogale307@gmail.com"}

"""### Scraping Sec 
This function scrapes sec form to get all the links to the S1 and S1-A docs of the company
"""

def scrape_sec():
  data = []
  download = requests.get(f'https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=s-1&owner=include&count=40&action=getcurrent',headers=headers).content
  soup = BeautifulSoup(download)
  # print(soup.find_all("table")[-2])
  s1_type = []
  for i in soup.find_all("table")[-2].find_all("tr"):
    res = [] 
    for j,val in enumerate(i.find_all("td")):
      
      if j == 1:
        # print(val)
        try:
          li=val.find_all("a")
          # print(li[1]["href"])
          # print("https://www.sec.gov"+val.a["href"])
          res.append("https://www.sec.gov"+li[1]["href"])
          # res.append(val.text)
        except:

           continue
      if j == 0:
        res.append(val.text)
      
      # print(res[1:])
      # print(val.text)
    # res.append("https://www.sec.gov"+str(i.find_all("td")[2].a["href"]))
    # print(res)
    if len(res)!=0:
      data.append(res)
  df = pd.DataFrame(data,columns=["Type","link"])
  df = df.drop_duplicates()
  df = df.iloc[1:,:]
  return df
  # df.to_excel("s1data.xlsx")
  # download = download.decode('latin1')

"""### Fetches basic data 
S1 documnets have a lot of scrambled data. It is not easy to get a lot of fields easily because the html format is not structured well enough to get complex data. 

This function fetches all the basic data that is easily scrapable. The fields are as follows :

1. Link to the document on sec 
2. File Date 
3. CompanyName
4. CIK 
5. Standard Industrial Classification
6. IRS Number
7. State of Inc 
8. Business Address 
  - State 
  - City
  - Zip 
  - Street Address
9. Phone number 
10. Mail Address
11. Number of shares of common stock offered
12. Price per share 

Number of shares and price per share needs to be found. 



"""

def get_basic_details(link):
  page = requests.get(link,headers = headers)
  soup = str(BeautifulSoup(page.content,"html.parser"))
  # print(soup[0])
  cleaned_soup=soup.replace('\t',' ')
  item_list=cleaned_soup.split("\n")
  # print(item_list[:50])
  info_dict=dict()
  info_dict["link"]=link
  info_dict["FileDate"]=item_list[6].split()[-1].strip()
  info_dict["CompanyName"]=item_list[12].split(':')[1].strip()
  info_dict["CIK"]=item_list[13].split(':')[1].strip()
  info_dict["STANDARD INDUSTRIAL CLASSIFICATION"]=item_list[14].split(':')[1].strip()
  info_dict["irs_no"]=item_list[15].split(':')[1].strip()
  info_dict["State_of_inc"]=item_list[16].split(':')[1].strip()
  info_dict["BusinessAddress"]=(',').join(item_list[26:31])
  info_dict["MailAddress"]=(',').join(item_list[33:36])
  print(info_dict)
  return info_dict

"""### Loops through the links to the S1 doc to get basic info for multiple companies"""

def get_data(df):
  data=pd.DataFrame(columns=["Type","link","FileDate","CompanyName","CIK","STANDARD INDUSTRIAL CLASSIFICATION","irs_no","State_of_inc","BusinessAddress","MailAddress"])
  all_types = df["Type"].tolist()
  for val,i in enumerate(df["link"].tolist()):
    try:
      datadict = dict(get_basic_details(i))
      datadict["Type"] = str(all_types[val])
      # print(datadict)
      data=data.append(datadict,ignore_index=True)
    except:
      continue
  return data

"""### Data Cleaning
The step cleans the data and gets the file ready for final delivery at EOD.
"""

def correct_file_date(df):
  for i,val in df.iterrows():
    val["FileDate"] = str(val["FileDate"])[0:4] + "-" + str(val["FileDate"])[4:6] + "-" + str(val["FileDate"])[6:]
  return df
def datapreprocess(data):
  state = []
  city = []
  zip = []
  phone = []
  address = []
  streetadd = []
  all_address = data["BusinessAddress"].tolist()
  for i in all_address:
    all_fields = i.split(",")
    tc = tz = tp = ts = tst = " "
    for j in all_fields:
      # j = j.strip(":")
      # print(i)
      if(j.find("CITY")!=-1):
        tc = j.split(":")[1]
      elif(j.find("STATE")!=-1):
        ts = j.split(":")[1]
      elif(j.find("ZIP")!=-1):
        tz = j.split(":")[1]
      elif(j.find("BUSINESS PHONE")!=-1):
        tp = j.split(":")[1]
      elif (j.find("STREET")!=-1):
        tst = ",".join(i.split(",")[0:2])
      # elif(j.find("CITY")!=-1):
      #   city.append(j.split(":")[1])
    city.append(tc)
    zip.append(tz)
    state.append(ts)
    phone.append(tp)
    streetadd.append(tst)
  # print(city)
  data["BusinessCity"] = city
  data["BusinessPhone"] = phone
  data["BusinessZip"] = zip
  data["BusinessState"] = state
  data["BusinessStreetAddress"] = streetadd
  data["No_of_shares"] = ""
  data["Price_per_share"] = ""
  data = data.drop(["BusinessAddress"],axis = 1)
  data = correct_file_date(data)
  return data

def make_report(output_dir):
  df=scrape_sec()
  data = get_data(df)
  df = datapreprocess(data)
  dat = date.today()
  dat = str(dat.strftime("%Y-%m-%d"))
  df.to_csv(output_dir+"S1DOC_Report_"+dat+".csv")
