#!/usr/bin/env python3
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import os
from os import listdir
import pandas as pd
import csv

#################################################
# this script uses a browser simulator to scrape gofundme comments
# current limitations: only up to 10 comments per page can be grabbed
# needs code to tell the webdriver to click the "see more" button
# if it finds one
#################################################

# create exceptions file
exceptions = open('./exceptions.txt','w+')
# load in local files
commentswriter = csv.writer(open('./comments.csv','w+'))
commentswriter.writerow('campaign, name, donation, comment')
htmldir = os.getcwd()+"/html/"
# # Create your driver
options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)
driver = webdriver.Firefox()
urls = pd.read_csv('./GFMURL.csv', header=None)


def find_comments(soup):
    title = soup.title.get_text()
    try:
        comment_info = []
        comment_scrip = []
        row = []
        row.append(title)
        comment_head = soup.find_all('div', {'class': 'm-comment-description'})
        comment_description = soup.find_all('div', {'class': 'm-comment-content'})
        for i in comment_head:
            body = i.get_text()
            comment_info.append(body)
            # more fine-graining is available, but unfinished
            # if '$' in body:
            #     don_split = body.split(' donated ')
            #     for d in don_split:
            #         comment_info.append(d)
            # elif :
            #     don_split = body.split(' commented')
            #     don_split[1] = 0
            #     for d in don_split:
            #         comment_info.append(d)
        for k in comment_description:
            comment_scrip.append(k.get_text())
        for i in range(len(comment_info)):
            row.append(comment_info[i])
            row.append(comment_scrip[i])
            print(row)
            commentswriter.writerow(row)
            row = []
            row.append(title)
    except:
        exceptions.write("no comments for")

# Uncomment this to set up the web scraper
for i in urls[0]:
    driver.get(i)
    driver.execute_script("window.scrollBy(0,5000)")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0,5000)")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0,5000)")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0,5000)")
    soup = BeautifulSoup(driver.page_source, "html5lib")
    find_comments(soup)
    print(soup.title.get_text()+" scraped for comments")

# Uncomment this if your files are local
# htmlfiles = listdir(os.getcwd()+"/html/")
# for f in htmlfiles:
#     with open(os.getcwd()+"/html/"+f, 'r') as html:
#         soup = BeautifulSoup(html.read())
#         find_comments(soup)
