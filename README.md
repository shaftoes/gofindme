# Loading URLs
The scripts expect a `.csv` file named `GFMURL.csv` in the directory.

# Grabbing campaign info
Run the `parser.py` script. It will grab campaign information, comment information, and donation
information from scraped pages using selenium's webdriver, which automates
loading and scraping the content of each page. This script used to be split into
two separate scripts, but I've combined them for usability's sake.

# Using the selenium web automator
Make sure that you have Firefox installed, as well as have followed the instructions at [Pythonspot's
Selenium setup page](https://pythonspot.com/selenium/). Then run the script and
don't worry if a Firefox window pops up and starts doing some stuff. 

This script outputs the campaign information into `campaigns.csv`, the donation
information into `donations.csv`, and the comments into `comments.csv`. It is currently only
capable of grabbing ten comments per campaign.
