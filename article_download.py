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
import time

# Command call for directory and files
def parse_args():
    parser = argparse.ArgumentParser(description='PDF Downloader')
    parser.add_argument('-a', '--articledb', type=str, default='./all_articles.dta',
                        help='Path to articles database')
    parser.add_argument('-f', '--folder', type=str, default='./all_pdfs',
                        help='Directory where PDFs will be downloaded')
    return parser.parse_args()

# Download file give df
def download_pdfs(df, folder_path):
    os.makedirs(folder_path, exist_ok=True)
    os.chmod(folder_path, mode=0o777)

    # Browser options
    browser_options = ChromeOptions()
    browser_options.add_experimental_option('prefs', {
        "download.default_directory": folder_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=browser_options)
    
    df['DOI_link'].fillna('NA')

    aea_df = df[(df['Publisher'] == 'American Economic *') & (pd.notna(df['DOI_link']))]

    for doi in aea_df['DOI_link']:
        print(doi)
        download_url = "https://pubs.aeaweb.org/doi/pdfplus/" + doi if 'https://' not in doi else doi
        print(f"Downloading file from link: {download_url}")
        driver.get(download_url)
        sleep(2)  # Wait for the download to start

        # Wait for the download to finish
        while any([filename.endswith(".crdownload") for filename in os.listdir(folder_path)]):
            time.sleep(1)  # Check every second

        # Rename the file
        downloaded_files = os.listdir(folder_path)
        if downloaded_files:
            # Assuming the latest file in the directory is the one we just downloaded
            latest_file = max([os.path.join(folder_path, f) for f in downloaded_files], key=os.path.getctime)
            new_file_name = os.path.join(folder_path, doi.replace('/', '_') + '.pdf')
            os.rename(latest_file, new_file_name)
            print(f"Renamed downloaded file to {new_file_name}")

    driver.quit()

# Usage
def main():
    args = parse_args()
    
    df = pd.read_csv(args.articledb)
    download_pdfs(df, args.folder)

if __name__ == "__main__":
    main()
