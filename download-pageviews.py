#!/bin/python

import argparse
import datetime
import requests
import signal
import random
import gzip
import os

from tqdm import tqdm
from urllib.parse import urljoin

BASE_URL = "https://dumps.wikimedia.org/other/pageviews/"

def generate_urls(start_date, end_date):
    url_list = []
    current_date = start_date
    while current_date <= end_date:
        year_month = current_date.strftime("%Y/%Y-%m/")
        for hour in range(24):
            file_name = f"pageviews-{current_date.strftime('%Y%m%d')}-{hour:02d}0000.gz"
            url = urljoin(BASE_URL, year_month + file_name)
            url_list.append(url)
        current_date += datetime.timedelta(days=1)
    return url_list

def get_random_hour(urls, count):
    random_urls = []
    interval = len(urls) // count
    for i in range(0, len(urls), interval):
        random_hour = random.choice(urls[i:i+interval])
        random_urls.append(random_hour)
    return random_urls[:count]


def download_and_extract(url, dest_folder):
    response = requests.get(url, stream=True)
    file_name = os.path.basename(url)
    file_path = os.path.join(dest_folder, file_name[:-3])

    if os.path.exists(file_path):
        return

    print(f"Downloading and decompressing {file_name}")

    try:
        with open(file_path, "wb") as f_out, gzip.open(response.raw, "rb") as f_in:
            for chunk in iter(lambda: f_in.read(8192), b""):
                f_out.write(chunk)
    except KeyboardInterrupt:
        os.remove(file_path)
        print(f"\nDownload interrupted. {file_name} removed.")
        exit(0)

def main():
    parser = argparse.ArgumentParser(description="Download and extract Wikipedia pageviews")
    parser.add_argument("-c", "--count", type=int, default=10, help="The number of pageview files to download (default is 10)")
    parser.add_argument("-s", "--start", type=str, default=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m%d"), help="The start date (default is 1 year ago)")
    parser.add_argument("-e", "--end", type=str, default=datetime.datetime.now().strftime("%Y%m%d"), help="The end date (default is the latest available pageview file)")
    parser.add_argument("-n", "--no-download", action="store_true", help="Export the URLs to a file and stop the script")
    args = parser.parse_args()

    start_date = datetime.datetime.strptime(args.start, "%Y%m%d")
    end_date = datetime.datetime.strptime(args.end, "%Y%m%d")

    urls = generate_urls(start_date, end_date)
    random_urls = get_random_hour(urls, args.count)

    if args.no_download:
        with open("pageview_urls.txt", "w") as f:
            for url in random_urls:
                f.write(url + "\n")
    else:
        os.makedirs("pageviews", exist_ok=True)
        for url in random_urls:
            download_and_extract(url, "pageviews")

if __name__ == "__main__":
    main()
