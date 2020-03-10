#!/usr/bin/env python3
from bs4 import BeautifulSoup 
import re
import csv
import requests
import time
import json
import os

urlreader = csv.reader(open('./GFMURL.csv', 'r'))
htmlwriter = csv.writer(open('./all-pages.csv','w+'))
donationwriter = csv.writer(open('./donations.csv','w+'))
exceptions = open('./exceptions.txt','w+')
htmlwriter.writerow(['organizer', 'location', 'category', 'description', 'created', 'money_raised', 'goal'])
donationwriter.writerow(['campaign','donation_id', 'amount', 'made_offline', 'is_anonymous', 'name', 'donation_date', 'profile', 'verified_user', 'comments'])

def parse_html(soup):
    try: 
        created_date = soup.find('span', {'class': 'm-campaign-byline-created'}).get_text().replace('Created ', '')
        organizer_block = soup.find('div', {'class': 'm-campaign-members-main'})
        name = organizer_block.find('div', {'class': 'm-person-info-name'}).get_text()
        location = organizer_block.find('div', {'class': 'm-person-info-content'}).get_text().replace('Organizer', '')
        category = soup.find('a', {'class': 'm-campaign-byline-type'}).get_text()
        description = soup.find('div', {'class': 'o-campaign-story'}).get_text()
        try:
            sofar, goal = soup.find('h2', {'class': 'm-progress-meter-heading'}).get_text().replace('goal','').split(' raised of ')
        except:
            goal = soup.find('h2', {'class':'m-progress-meter-heading'}).get_text()
            sofar = '0'
        pagerow = [name, location, category, description, created_date, sofar, goal]
        # comment_row = find_comments(soup)
        # print(comment_row)
        htmlwriter.writerow(pagerow)
    except:
        exceptions.write(row[0]+" was unable to be parsed\n")
    
def find_donations(soup):
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
        for donation in donation_list:
            donation_row_constructor.append(campaign_id)
            donation_row_constructor.append(campaign_title)
            donation = re.split(',', donation)
            for field in donation:
                field.replace('"', '').replace("'", '')
                field = field.split('":')[1]
                field.replace('"', '').replace("'", '')
                donation_row_constructor.append(field)
            donationwriter.writerow(donation_row_constructor)
            donation_row_constructor = []
    except:
        exceptions.write("no donations")
        
def find_comments(soup):
    try:
        comment_info = []
        comment_soup = soup.find_all('div', {'class': 'm-comment'})
        for comment in comment_soup:
            comment_info.append(comment.get_text())
        return comment_info
    except:
        exceptions.write("no comments")

for row in urlreader:
    time.sleep(1)
    response = requests.get(row[0], headers = {'User-agent': 'webscraper'})
    soup = BeautifulSoup(response.text)
    parse_html(soup)
    find_donations(soup)
    print(soup.title.get_text()+" has been parsed.")
