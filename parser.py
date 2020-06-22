#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import re
import csv
import time
import os
from selenium import webdriver
import sys
import sqlite3
import datetime
from multiprocessing import Process

# basic usage: call the script with "search term" as an argument
# next steps: move it all to a sqlite db in order to daemonize it

# this is set up to be changed; empty items 1 and 3 are changed per requests call
api_string = [
    'https://www.gofundme.com/mvc.php?route=homepage_norma/load_more&page=',
    '', '&term=', '']


def generate_api_call(search_term, page_number):
    api_string[1] = str(page_number)
    api_string[3] = search_term
    api_call = ''.join(api_string)
    return api_call


def initialize_db(database_name):
    database_connection = sqlite3.connect(database_name + ".db")
    cursor = database_connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS urls(
    url text PRIMARY KEY,
    image text,
    title text,
    location text,
    description text,
    raised text,
    goal text,
    deleted text
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns(
    name text PRIMARY KEY,
    url text,
    organizer text,
    location text,
    category text,
    description text,
    created text,
    money_raised text,
    goal text,
    donors text,
    shares text,
    followers text
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments(
    name text PRIMARY KEY,
    url text,
    campaign text,
    donation text,
    comment text
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donations(
    donation_id text PRIMARY KEY,
    url text,
    campaign text,
    amount text,
    made_offline integer,
    is_anonymous integer,
    name text,
    donation_date text,
    profile text,
    verified_user integer,
    comments text
    )""")


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meta(
    date text PRIMARY KEY,
    query text,
    num_results text
    )""")
    database_connection.commit()
    return cursor, database_connection


def grab_urls_php(search_term, database_cursor, database_connection):
    url_list = []
    main_page = requests.get(
        'https://www.gofundme.com/mvc.php?route=homepage_norma/search&term=' +
        search_term).text
    main_soup = BeautifulSoup(main_page, "html5lib")
    number_of_results = main_soup.find("div", {
        'class': 'heading-3'
    }).get_text().replace(' results found', '')
    database_cursor.execute(
        """INSERT INTO meta(date, query, num_results) VALUES (?, ?, ?)""",
        [datetime.datetime.now(), search_term, number_of_results])
    # we can get our page number by dividing by 9 - the amount of posts on a page
    number_of_pages = int(number_of_results) // 9
    # need to call at range one because our api_call asks for a page number,
    # which is invalid for 0
    for i in range(1, number_of_pages):
        time.sleep(1)
        api_call = generate_api_call(search_term, i)
        # call the php api and parse it
        r = requests.get(api_call)
        soup = BeautifulSoup(r.text, "html5lib")
        campaigntiles = soup.find_all("div",
                                      {'class': 'react-campaign-tile'})
        if len(campaigntiles) == 0:
            print("Search stopped at page " + str(i))
            break
        for c in campaigntiles:
            url = (c.find("a")['href'])
            info = parse_tile(c)
            info.insert(0,url)
            database_cursor.execute(
                """INSERT OR IGNORE INTO urls(
                url, image, title, location, description, raised, goal, deleted)
                VALUES (?,?,?,?,?,?,?,?)""", info)
            database_connection.commit()
    print('Done a search pass for ' + search_term)


# second set of functionaities: scraping the pages themselves

def parse_tile(campaign_tile):
    image = campaign_tile.find("a", {"class":"campaign-tile-img--contain"})['data-original']
    infotile = campaign_tile.find("div",{"class":"react-campaign-tile-details"})
    title = infotile.find("div", {"class":"fund-title"}).get_text()
    location = infotile.find("div",{"class":"fund-location"}).get_text().strip()
    description = infotile.find("div",{"class":"fund-description"}).get_text().strip()
    fundblock = infotile.find("div",{"class":"fund-item truncate-single-line"}
                                 ).get_text().strip().split("of")[0:2]
    raised = fundblock[0].rstrip(" raised")
    goal = fundblock[1].split(" ")[1]
    deleted = check_deleted(campaign_tile.find("a", {"class":"campaign-tile-img--contain"})['href'])
    return [image,title,location,description,raised,goal,deleted]

def check_deleted(url):
    if BeautifulSoup(requests.get(url).text,"html5lib").title.get_text() == "Page Not Found":
        return datetime.datetime.now()
    else:
        return "No"

def find_campaign_info(soup, url):
    name = soup.title.get_text()
    if name == "Page Not Found":
        deletion_date = datetime.datetime.now()
        return
    else:
        deletion_date = "exists"
        created_date = soup.find('span', {
            'class': 'm-campaign-byline-created'
        }).get_text().replace('Created ', '')
        category = soup.find('a', {
            'class': 'm-campaign-byline-type'
        }).get_text()
        # name and location are in same block, so we parse that
        organizer_block = soup.find('div',
                                    {'class': 'm-campaign-members-main'})
        organizer = organizer_block.find('div', {
            'class': 'm-person-info-name'
        }).get_text()
        location = organizer_block.find('div', {
            'class': 'm-person-info-content'
        }).get_text().replace('Organizer', '')
        # not all campaigns have donors, so we place this in a try block
        fundraiser_elements = soup.find('div', {
            'class': 'p-campaign-content'
        }).find_all('span', {'class': 'text-stat-value'})
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
            fundraiser_elements = soup.find('div', {
                'class': 'p-campaign-content'
            }).find_all('span', {'class': 'text-stat-value'})
            donors = fundraiser_elements[0].get_text()
            shares = fundraiser_elements[1].get_text()
            followers = fundraiser_elements[2].get_text()
        except:
            donors = "No donors"
            followers = "No followers"
            shares = "No shares"
        try:
            description = soup.find('div', {
                'class': 'o-campaign-story'
            }).get_text()
        except:
            description = "No description"
        try:
            # campaigns that have a goal but no money display the goal differently
            # so we need a separate assignment for a 'money raised' of 0
            sofar, goal = soup.find('h2', {
                'class': 'm-progress-meter-heading'
            }).get_text().replace('goal', '').split(' raised of ')
        except:
            goal = soup.find('h2', {
                'class': 'm-progress-meter-heading'
            }).get_text()
            sofar = '0'
        # write all of these values to a row to be written to the csv
    pagerow = [
            url, name, organizer, location, category, description,
            created_date, sofar, goal, donors, shares, followers, deletion_date
        ]
    return pagerow


def find_donations(soup, url):
    """find all donation-related information and scrapes it into donations.csv"""
    campaign_title = soup.title.get_text()
    donation_array = []
    # json.loads and ast.literal_eval don't work here, so we need to split manually
    # this is really, really messy code becaue of the peculiarities of parsing 
    # json as a string. If this section throws errors, then the code is
    # out-of-date -- probably due to a redesign of the website.
    try:
        jsonstring = str(soup.find_all('script')[0])
        donation_row_constructor = []
        campaign_id_index = jsonstring.find("campaign_id") + 14
        campaign_id_end = jsonstring.find(',"auto_fb_post_mode":')
        campaign_id = jsonstring[campaign_id_index:campaign_id_end]
        # next we find the substring that contains the list of donations
        donation_list_index = jsonstring.find("donation_id") - 1
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
            donation_array.append(donation_row_constructor)
            donation_row_constructor = []
        return donation_array
    except:
        return []
        print("The campaign at " + url + " has no donations.\n")


def find_comments(soup, url):
    # this finds all comments available and scrapes them into comments.csv
    comment_array = []
    title = soup.title.get_text()
    try:
        comment_info = []
        comment_scrip = []
        row = [title]
        comment_head = soup.find_all('div', {'class': 'm-comment-description'})
        comment_description = soup.find_all('div',
                                            {'class': 'm-comment-content'})
        for i in comment_head:
            body = i.get_text()
            name, amount = body.split(' donated ')
            comment_info.append(name, amount)
        for k in comment_description:
            comment_scrip.append(k.get_text())
        for i in range(len(comment_info)):
            row.append(comment_info[i])
            row.append(comment_scrip[i])
            row.append(url)
            comment_array.append(row)
            row = []
            row.append(title)
        print("comments grabbed for" + title)
        print(comment_array)
        return comment_array
    except:
        print("no comments for" + title)
        return []


def load_and_parse(database_cursor, database_connection, key):
    # main wrapper function for the scraper functions - loads the page and calls
    # the scrapers
    if key == "update":
        urls = database_cursor.execute("""
        SELECT * FROM urls WHERE NOT EXISTS (
        SELECT NULL
        FROM campaigns
        WHERE urls.url = campaigns.url
        )""").fetchall()
    else:
        urls = database_cursor.execute("""
        SELECT * FROM urls""").fetchall()
    for url_tuple in urls:
        url = url_tuple[0]
        driver.get(url)
        for x in range(0, 3):
            # the choice of 3 window scrolls is arbitrary, but GoFundMe won't load any
            # more if we reach the bottom - more elements are hidden behind javascript calls
            driver.execute_script("window.scrollBy(0,5000)")
            time.sleep(0.2)  # sleep to let the browser catch up
        soup = BeautifulSoup(driver.page_source, "html5lib")
        try:
            campaign_info = find_campaign_info(soup, url)
            database_cursor.execute(
                """INSERT OR REPLACE INTO campaigns(
            url, name, organizer, location, category, description, created, money_raised, goal, donors, shares, followers, does_exist
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?, ?)""",
                campaign_info)
        except:
            print(
                "The campaign at " + url +
                " could not be found. It's either been deleted, or the url is incorrect.\n"
            )
            continue
        try:
            for donation in find_donations(soup, url):
                database_cursor.execute(
                    """
                INSERT OR IGNORE INTO donations(
                    donation_id, url, campaign, amount, made_offline, is_anonymous, name, donation_date, profile, verified_user, comments)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", find_donations(soup, url))
            database_connection.commit()
        except:
            print(
                "Couldn't find donations for the campaign at " + url
            )
            continue
        try:
            for comment in find_comments(soup, url):
                database_cursor.execute(
                    """INSERT OR IGNORE INTO comments(campaign, url, name, donation, comment)
                    VALUES (?,?,?,?,?,?,?,?)""", comment)
        except:
            print(
                "Couldn't find comments for the campaign at " + url
            )
            continue


if __name__ == '__main__':
    if sys.argv[2]:
        passes = int(sys.argv[2])
    else:
        passes = 1
    cursor, connection = initialize_db(sys.argv[1])
    for x in range(0, passes):
        grab_urls_php(sys.argv[1], cursor, connection)
        print('success')
    driver = webdriver.Firefox()
    key = sys.argv[3]
    load_and_parse(cursor, connection, key)
    connection.commit()
    connection.close()
