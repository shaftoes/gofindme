#!/usr/bin/env python3
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import os
import pandas as pd
import csv
import wget

# create exceptions file
exceptions = open('./exceptions.txt','w+')
commentswriter = csv.writer(open('./comments.csv','w+'))
htmldir = os.getcwd()+"/html/"
# Create your driver
# options = Options()
# options.headless = True
# driver = webdriver.Firefox(options=options)
driver = webdriver.Firefox()
urls = pd.read_csv('./GFMURL.csv', header=None)


def find_comments(soup):
    try:
        comment_info = []
        comment_description = []
        title = soup.title.get_text()
        row = []
        row.append(title)
        comment_head = soup.find_all('div', {'class': 'm-comment-description'})
        comment_description = soup.find_all('div', {'class': 'm-comment-content'})
        for i in comment_head:
            comment_info.append(i)
        for k in comment_description:
            comment_description.append(i)
        row += comment_info + comment_description
        commentswriter.writerow(row)
    except:
        exceptions.write("no comments for"+soup.title.get_text())

# Get a page
for i in urls[0]:
    driver.get(i)
    driver.execute_script("window.scrollBy(0,2500)")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0,2500)")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0,2500)")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0,2500)")
    soup = BeautifulSoup(driver.page_source, "html5lib")
    with open(htmldir+soup.title.get_text(), 'w+') as f:
        f.write(str(soup))
    print(soup.title.get_text()+" scraped for comments")

htmlfiles = [f for f in listdir(os.getcwd()+"/html/") if isfile(join(os.getcwd()+"/html/", f))]
for f in htmlfiles:
    with open(f, 'r') as html:
        find_comments(html)
