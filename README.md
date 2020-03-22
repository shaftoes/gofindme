# Loading URLs
When run on the command line, call the script with a `.csv` of URLs as your
argument.

> e.g., `python parser.py GFMURLS.csv`

# Grabbing campaign info
The script will grab campaign information, comment information, and donation information from scraped pages using selenium's webdriver, which automates
loading and scraping the content of each page. Campaigns that do not exist anymore, or have incorrect URLs, are written to `exceptions.txt`. Campaigns that have no donations are written to `exceptions.txt`. 

# Information on using the selenium web driver
Make sure that you have Firefox installed, as well as have followed the instructions at [Pythonspot's
Selenium setup page](https://pythonspot.com/selenium/). Then run the script and
don't worry if a Firefox window pops up and starts doing some stuff. If you want
to use a different browser, you can edit the code accordingly to create a new driver. 

This script outputs the campaign information into `campaigns.csv`, the donation
information into `donations.csv`, and the comments into `comments.csv`. It is currently only
capable of grabbing ten comments and five donations per campaign, but this can easily be remedied by adding a selenium
instruction to click the "See More" button that appears after 10 comments have been loaded. Just haven't
gotten around to adding that yet.
