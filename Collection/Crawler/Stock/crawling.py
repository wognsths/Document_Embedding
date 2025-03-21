from argparse import ArgumentParser
from typing import Dict, Type
from Collection.Crawler.Stock.config import *
from Collection.Crawler.Stock.crawler import StockNewsCrawler

import os
import datetime
import time

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=False)
    parser.add_argument('-t', '--ticker_code', type=str, required=True, choices=TickerDict.keys())
    parser.add_argument('-y', '--year', type=str, required=True)
    return parser

def run_crawler():
    args = create_parser().parse_args()

    ticker_code = args.ticker_code
    if ticker_code not in TickerDict.keys():
        print(f"Choose argument in {list(TickerDict.keys())}")
        return None

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = f'./Data/News/Raw'
    os.makedirs(output_dir, exist_ok=True)

    driver_path = "./chromedriver"

    crawler = StockNewsCrawler(
        output_dir=output_dir,
        driver_path=driver_path,
        year=args.year,
        ticker_code=ticker_code
    )

    start_date_str = crawler.set_start_date()
    start_date = datetime.datetime.strptime(start_date_str, "%Y%m%d")

    year_int = int(args.year)
    today = datetime.datetime.today()
    if year_int < today.year:
        final_end_date = datetime.datetime(year_int, 12, 31)
    else:
        final_end_date = today

    if start_date > final_end_date:
        print(f"No new dates to crawl. Start date {start_date.strftime('%Y-%m-%d')} is after final end date {final_end_date.strftime('%Y-%m-%d')}.")
        return None

    print(f"Crawling from {start_date.strftime('%Y-%m-%d')} to {final_end_date.strftime('%Y-%m-%d')}")

    current_date = start_date
    while current_date <= final_end_date:
        date_str = current_date.strftime("%Y%m%d")
        print(f"Processing date: {date_str}")

        crawler.scrape_articles(date_str)

        crawler.save_to_database()

        current_date += datetime.timedelta(days=1)
        print(f"Next date: {current_date.strftime('%Y-%m-%d')}")

    print(f"✅ Finished crawling from {start_date.strftime('%Y-%m-%d')} to {final_end_date.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    run_crawler()