#!/usr/bin/env python3
from bs4 import BeautifulSoup
import re
import csv
import requests
import time
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# load our csvs for input and output
urlreader = csv.reader(open('./GFMURL.csv', 'r'))
htmlwriter = csv.writer(open('./campaigns.csv','w+'))
donationwriter = csv.writer(open('./donations.csv','w+'))
commentswriter = csv.writer(open('./comments.csv','w+'))
exceptions = open('./exceptions.txt','w+')
commentswriter.writerow(['campaign', 'name', 'donation', 'comment', 'url','donors', 'shares','followers'])
htmlwriter.writerow(['organizer', 'location', 'category', 'description', 'created', 'money_raised', 'goal', 'url'])
donationwriter.writerow(['campaign','donation_id', 'amount', 'made_offline', 'is_anonymous', 'name', 'donation_date', 'profile', 'verified_user', 'comments', 'url'])
# Create our web driver to load and scrape the pages 
driver = webdriver.Firefox()

def find_campaign_info(soup, url):
    try:
        created_date = soup.find('span', {'class': 'm-campaign-byline-created'}).get_text().replace('Created ', '')
        organizer_block = soup.find('div', {'class': 'm-campaign-members-main'})
        name = organizer_block.find('div', {'class': 'm-person-info-name'}).get_text()
        location = organizer_block.find('div', {'class': 'm-person-info-content'}).get_text().replace('Organizer', '')
        category = soup.find('a', {'class': 'm-campaign-byline-type'}).get_text()
        try:
            fundraiser_elements = soup.find('div', {'class':'p-campaign-content'}).find_all('span', {'class':'text-stat-value'})
            donors = fundraiser_elements[0].get_text()
            shares = fundraiser_elements[1].get_text()
            followers = fundraiser_elements[2].get_text()
        except:
            donors = "No donors"
            followers = "No followers"
            shares = "No shares"
        try:
            description = soup.find('div', {'class': 'o-campaign-story'}).get_text()
        except:
            description = "No description"
        try:
            sofar, goal = soup.find('h2', {'class': 'm-progress-meter-heading'}).get_text().replace('goal','').split(' raised of ')
        except:
            goal = soup.find('h2', {'class':'m-progress-meter-heading'}).get_text()
            sofar = '0'
        pagerow = [name, location, category, description, created_date, sofar, goal, url, donors, shares, followers]
        htmlwriter.writerow(pagerow)
    except:
        exceptions.write(row[0]+" was unable to be parsed\n")

def find_donations(soup, url):
    # json.loads and ast.literal_eval don't work here, need to split manually
    # this is really, really messy code becaue of the peculiarities of parsing json as a string
    try:
        jsonstring = str(soup.find_all('script')[0])
        donation_row_constructor = []
        campaign_id_index = jsonstring.find("campaign_id")+14
        campaign_id_end = jsonstring.find(',"auto_fb_post_mode":')
        campaign_id = jsonstring[campaign_id_index:campaign_id_end]
        # then same for the title, just to have it
        campaign_title_index = jsonstring.find("fund_name")+12
        campaign_title_end = jsonstring.find(',"goal_amount":')
        campaign_title = jsonstring[campaign_title_index:campaign_title_end]
        # next we find the substring that contains the list of donations
        donation_list_index = jsonstring.find("donation_id")-1
        donation_list_end = jsonstring.find('}],"identity":')
        donation_string = jsonstring[donation_list_index:donation_list_end]
        donation_list = re.split("\},\{", donation_string)
        # now we need to go through the donation list, split them each up individually
        # then by elements 
        for donation in donation_list:
            donation_row_constructor.append(campaign_id)
            donation_row_constructor.append(campaign_title)
            donation = re.split(',', donation)
            for field in donation:
                field.replace('"', '').replace("'", '')
                field = field.split('":')[1]
                field.replace('"', '').replace("'", '')
                donation_row_constructor.append(field)
            donation_row_constructor.append(url)
            donationwriter.writerow(donation_row_constructor)
            donation_row_constructor = []
    except:
        exceptions.write("The campaign at "+url+" has no donations.\n")


def find_comments(soup, url):
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
            row.append(url)
            commentswriter.writerow(row)
            row = []
            row.append(title)
    except:
        exceptions.write("no comments for")

def load_and_parse(csv_reader):
    for i in csv_reader:
        url = i[0]
        driver.get(url)
        print(url)
        for x in range(0, 3):
            driver.execute_script("window.scrollBy(0,5000)")
            time.sleep(1)
        for x in range(0,20):
            try:
                morecomments = driver.find_element_by_x_path("//a[@data-element-id='btn_donate_morecomments']")
                morecomments.click()
                time.sleep(1)
            except:
                break
        for x in range(0,20):
            try:
                moredonations = driver.find_element_by_x_path("//a[@data-element-id='btn_donate_moredonations']")
                moredonations.click()
            except:
                break
        soup = BeautifulSoup(driver.page_source, "html5lib")
        if soup.title.get_text() != "Page Not Found":
            find_campaign_info(soup, url)
            find_donations(soup, url)
            find_comments(soup, url)
            print(soup.title.get_text()+" loaded and scraped.")
        else:
            exceptions.write("The campaign at "+url+" could not be found. It's either been deleted, or the url is incorrect.\n")

if __name__=="__main__":
    load_and_parse(urlreader)