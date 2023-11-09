#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Setup
import os
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from time import sleep
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
import argparse

# Command call for directory and files
def parse_args():
    parser = argparse.ArgumentParser(description='PDF Downloader')
    parser.add_argument('-a', '--articledb', type=str, default='./all_articles.dta',
                        help='Path to articles database')
    parser.add_argument('-f', '--folder', type=str, default='./all_pdfs',
                        help='Directory where PDFs will be downloaded')
    return parser.parse_args()

# Given DOIs list, downloads PDFs to folder_path
def download_pdfs(df, folder_path):
    os.makedirs(folder_path, exist_ok=True)
    os.chmod(folder_path, mode = 0o777)
    
    # Browser options
    browser_options = ChromeOptions()
    browser_options.add_experimental_option('prefs', {
        "download.default_directory": folder_path, # Change default directory for downloads
        "download.prompt_for_download": False, # To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True # It will not show PDF directly in chrome
    })
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=browser_options)

    aea_df = df[df['Publisher'] == 'American Economic *']
    
    # Loop over DOIs and get files
    for doi in aea_df['DOI_link']:
        if doi != "NA":
            if 'https://' not in doi:
                print("Downloading file from link: {}".format("https://pubs.aeaweb.org/doi/pdfplus/" + doi))
                driver.get("https://pubs.aeaweb.org/doi/pdfplus/" + doi)
                sleep(2)
            else:
                print("Downloading file from link: {}".format(doi))
                driver.get(doi)
                sleep(2)
        
    driver.quit()

# Usage
def main():
    args = parse_args()
    
    df = pd.read_stata(args.articledb)
    download_pdfs(df, args.folder)

if __name__ == "__main__":
    main()
