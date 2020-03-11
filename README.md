# Loading URLs
The scripts expect a `.csv` file named `GFMURL.csv` in the directory.

# Grabbing campaign info
Run the `parser.py` script. It will grab campaign information and donation
information from static pages.

# Grabbing comments
Since the comments are loaded dynamically, this script has been separated into
the `selenium-downloader.py` script. Run this and make sure that you have
Firefox installed, as well as have followed the instructions at [Pythonspot's
Selenium setup page](https://pythonspot.com/selenium/). Then run the script and
don't worry if a Firefox window pops up and starts doing some stuff. 

This script outputs the comments into `comments.csv`. It is currently only
capable of grabbing ten comments per campaign.
