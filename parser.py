#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import re
import csv
import time
import os
from selenium import webdriver
import sys

# basic usage: call the script with "search term" as an argument

# this is set up to be muted; empty items 1 and 3 are changed per requests call
api_string = ['https://www.gofundme.com/mvc.php?route=homepage_norma/load_more&page=','','&term=','','&country=&postalCode=&locationText=']

def generate_api_call(search_term, page_number):
    api_string[1]=str(page_number)
    api_string[3] = search_term
    api_call = ''.join(api_string)
    return api_call

# need to load in old URLs and not go back over them
# because the PHP api we're plugged into throws random errors at us
# and breaks the script before it captures everything
def load_history(csvname):
    csvfile = open(csvname, 'r')
    reader = csv.reader(csvfile)
    already_scraped = list(reader)
    csvfile.close()
    return already_scraped

def grab_results(search_term):
    url_list = []
    file_reader = './campaign_urls.csv'
    history = load_history(file_reader)
    campaign_url_writer = csv.writer(open('./campaign_urls.csv', 'a'))
    main_page = requests.get('https://www.gofundme.com/mvc.php?route=homepage_norma/search&term='+search_term).text
    main_soup = BeautifulSoup(main_page, "html5lib")
    number_of_results = main_soup.find("div", {'class': 'heading-3'}).get_text().replace(' results found', '')
    print(number_of_results)
    # we can get our page number by dividing by 9 - the amount of posts on a page
    number_of_pages = int(number_of_results) // 9
    for i in range(1,number_of_pages):
        time.sleep(3)
        api_call = generate_api_call(search_term, i)
        # call the php api and parse it
        campaignurls = []
        r = requests.get(api_call)
        soup = BeautifulSoup(r.text, "html5lib")
        campaigntiles = soup.find_all("a", {'class':'campaign-tile-img--contain'})
        # print("Requested page "+str(i)+' and received code '+str(r.status_code)+'. There are '+str(len(campaigntiles))+" on page "+str(i))
        if len(campaigntiles) == 0:
            print(soup)
            break
        for c in campaigntiles:
                url = c.get('href')
                url_list.append(url)
    print('Done search pass for '+search_term)
    for u in url_list:
        if u not in history:
            campaign_url_writer.writerow([u])

# second set of functionaities: scraping the pages themselves

def load_csv(csv):
    urlreader = csv.reader(open(csv, 'r'))
    htmlwriter = csv.writer(open('./campaigns.csv','w+'))
    donationwriter = csv.writer(open('./donations.csv','w+'))
    commentswriter = csv.writer(open('./comments.csv','w+'))

    # next we write the headers of each file
    exceptions = open('./exceptions.txt','w+')
    commentswriter.writerow(['campaign', 'name', 'donation', 'comment', 'url','donors', 'shares','followers'])
    htmlwriter.writerow(['organizer', 'location', 'category', 'description', 'created', 'money_raised', 'goal', 'url'])
    donationwriter.writerow(['campaign','donation_id', 'amount', 'made_offline', 'is_anonymous', 'name', 'donation_date', 'profile', 'verified_user', 'comments', 'url'])

def find_campaign_info(soup, url):
    try:
        created_date = soup.find('span', {'class': 'm-campaign-byline-created'}).get_text().replace('Created ', '')
        category = soup.find('a', {'class': 'm-campaign-byline-type'}).get_text()
        # name and location are in same block, so we parse that
        organizer_block = soup.find('div', {'class': 'm-campaign-members-main'})
        name = organizer_block.find('div', {'class': 'm-person-info-name'}).get_text()
        location = organizer_block.find('div', {'class': 'm-person-info-content'}).get_text().replace('Organizer', '')
        # not all campaigns have donors, so we place this in a try block
        fundraiser_elements = soup.find('div', {'class':'p-campaign-content'}).find_all('span', {'class':'text-stat-value'})
        # the next 3 below strings are the string values of 'text-stat-value'
        # these are all in try blocks because some campaigns do not have them
        try:
            donors = fundraiser_elements[0].get_text()
        except:
            donors = "No donors"
        try:
            shares = fundraiser_elements[1].get_text()
        except:
            shares = "No shares"
        try:
            followers = fundraiser_elements[2].get_text()
        except:
            # what to put in if there are no values
            followers = "No followers"
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
        # campaigns that have a goal but no money display the goal differently
        # so we need a separate assignment for a 'money raised' of 0
            sofar, goal = soup.find('h2', {'class': 'm-progress-meter-heading'}).get_text().replace('goal','').split(' raised of ')
        except:
            goal = soup.find('h2', {'class':'m-progress-meter-heading'}).get_text()
            sofar = '0'
        # write all of these values to a row to be written to the csv
        pagerow = [name, location, category, description, created_date, sofar, goal, url, donors, shares, followers]
        htmlwriter.writerow(pagerow)
    except:
        # catching our exceptions onto the command line
        print(url+" was unable to be parsed\n")

       
def find_donations(soup, url):
    # this finds all donation-related information and scrapes it into donations.csv
    campaign_title = soup.title.get_text()
    # json.loads and ast.literal_eval don't work here, so we need to split manually (pythonically?)
    # this is really, really messy code becaue of the peculiarities of parsing json as a string. If this section throws errors, then the code is out-of-date --
    # probably due to a redesign of the website.
    try:
        jsonstring = str(soup.find_all('script')[0])
        donation_row_constructor = []
        campaign_id_index = jsonstring.find("campaign_id")+14
        campaign_id_end = jsonstring.find(',"auto_fb_post_mode":')
        campaign_id = jsonstring[campaign_id_index:campaign_id_end]
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
            # we've split the donations into separate string values
            for field in donation:
                field.replace('"', '').replace("'", '')
                field = field.split('":')[1]
                field.replace('"', '').replace("'", '')
                donation_row_constructor.append(field)
            donation_row_constructor.append(url)
            donationwriter.writerow(donation_row_constructor)
            donation_row_constructor = []
    except:
        print("The campaign at "+url+" has no donations.\n")

       
def find_comments(soup, url):
    # this finds all comments available and scrapes them into comments.csv
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
        print("no comments for")

def load_and_parse(csv_reader):
    # main wrapper function for the scraper functions - loads the page and calls
    # the scrapers
    for i in csv_reader:
        url = i[0]
        driver.get(url)
        for x in range(0, 3):
        # the choice of 3 window scrolls is arbitrary, but GoFundMe won't load any
        # more if we reach the bottom - more elements are hidden behind javascript calls
            driver.execute_script("window.scrollBy(0,5000)")
            time.sleep(1) # sleep to let the browser catch up
        for x in range(0,20):
        # we try clicking the 'show comments' button 20 times.
        # the choice of 20 is also arbitrary, but this would load 100 comments
            try:
                # this click is not working right now
                morecomments = driver.find_element_by_x_path("//a[@data-element-id='btn_donate_morecomments']")
                morecomments.click()
                time.sleep(1)
            except:
                break
        for x in range(0,20):
            # attempt to click the "show more" to see more donations
            try:
                # this click is not working right now
                moredonations = driver.find_element_by_x_path("//a[@data-element-id='btn_donate_moredonations']")
                moredonations.click()
            except:
                break
        # load the page's source as a soup object *after* we're done clicking and loading
        # dynamic javascript elements
        soup = BeautifulSoup(driver.page_source, "html5lib")
        # just to make sure that the page exists and we're not wasting our time
        if soup.title.get_text() != "Page Not Found":
            find_campaign_info(soup, url)
            find_donations(soup, url)
            find_comments(soup, url)
            print(soup.title.get_text()+" loaded and scraped.")
            return
        else:
            print("The campaign at "+url+" could not be found. It's either been deleted, or the url is incorrect.\n")
            return

if sys.argv[1].endswith('.csv'):
    load_and_parse(sys.argv[1])

elif type(sys.argv[1]) == str:
    for i in range(0,100):
        grab_results(sys.argv[1])
        load_and_parse('./campaign_urls.csv')
