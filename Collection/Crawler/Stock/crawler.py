from Collection.Crawler.Stock.config import *

import os
import sys
import csv
import time
import datetime
import schedule
import pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class StockNewsCrawler:
    def __init__(
            self,
            output_dir: str,            # Data output directory
            driver_path: str = None,    # Driver path
            year: str = '2019',         # Base year
            ticker_code: str = None     # Key: TickerDict > Ticker Code
        ):
        self.output_dir = output_dir
        self.year = year
        self.ticker_code = ticker_code
        self.query = TickerDict[ticker_code][0]
        self.driver_path = driver_path
        self.output_file = os.path.join(self.output_dir, f'{ticker_code}_{self.year}.csv')
        self.detailed_articles = []
    
    def start_browser(self):
        print('Initialize browser...')
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--headless')
        try:
            if self.driver_path and os.path.exists(self.driver_path):
                self.driver = webdriver.Chrome(
                    service=Service(self.driver_path),
                    options=chrome_options
                )
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            print('Browser initialized successfully!')
        except Exception as e:
            print(f'Something went wrong... Message below:\n\n{e}')
            sys.exit(1)
    
    def scrape_articles(self, date):
        print('Starting crawling process...')
        self.start_browser()

        naver_url_query = f'https://search.naver.com/search.naver?where=news&query={self.query}'
        sort_argument = (
            f'sm=tab_opt&sort=0&photo=0&field=0&pd=3'
            f'&ds={date[:4]}.{date[4:6]}.{date[6:]}'
            f'&de={date[:4]}.{date[4:6]}.{date[6:]}'
            f'&docid=&related=0&mynews=1&office_type=1&office_section_code=2'
            f'&news_office_checked=1001&nso=so%3Ar%2Cp%3Afrom{date}to{date}'
            f'&is_sug_officeid=0&office_category=0&service_area=0'
        )

        self.driver.get(f'{naver_url_query}&{sort_argument}')
        print(f'Query: {self.query}, Ticker: {self.ticker_code}, Date: {date}')
        time.sleep(1)

        last_height = self.driver.execute_script('return document.body.scrollHeight')
        while True:
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(1)
            new_height = self.driver.execute_script('return document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

        time.sleep(1)
        article_list = []
        self.detailed_articles = []
        news_items = self.driver.find_elements(By.CSS_SELECTOR, ".list_news._infinite_list > li.bx[id^='sp_nws']")

        for item in tqdm(news_items, desc='Scraping Meta'):
            try:
                title_element = item.find_element(By.CSS_SELECTOR, "div.news_contents a.news_tit")
                title = title_element.text.strip()
                
                link_element = item.find_element(By.CSS_SELECTOR, "div.info_group a.info:not(.press)")
                link = link_element.get_attribute("href")

                article_list.append([title, link])
            except Exception as e:
                pass

        for (title, link) in tqdm(article_list, desc='Scraping Details'):
            try:
                self.driver.get(link)
                time.sleep(0.5)

                try:
                    body_elem = self.driver.find_element(By.CSS_SELECTOR, 'article#dic_area')
                    body = body_elem.text.strip()
                except Exception as e:
                    print(f'[ERROR] Failed to fetch article content. Link: {link}')
                    continue

                b, d, r, ur = "", "", "", ""
                try:
                    comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.u_cbox_comment_box.u_cbox_type_profile")
                    for comment_item in comment_elements:
                        try:
                            b_elem = comment_item.find_element(By.CSS_SELECTOR, "span.u_cbox_contents")
                            b += f"{b_elem.text.strip()}\n"

                            d_elem = comment_item.find_element(By.CSS_SELECTOR, "div.u_cbox_info_base span.u_cbox_date")
                            d += f"{d_elem.get_attribute('data-value')}\n"

                            r_elem = comment_item.find_element(By.CSS_SELECTOR, "a.u_cbox_btn_recomm em.u_cbox_cnt_recomm")
                            r += f"{r_elem.text.strip()}\n"

                            ur_elem = comment_item.find_element(By.CSS_SELECTOR, "a.u_cbox_btn_unrecomm em.u_cbox_cnt_unrecomm")
                            ur += f"{ur_elem.text.strip()}\n"
                        except Exception as e:
                            pass
                except Exception as e:
                    pass

                try:
                    e_elems = self.driver.find_elements(By.CSS_SELECTOR, "span.u_likeit_list_count._count")
                    emo = [e.text.strip() for e in e_elems]
                    if len(emo) >= 10:
                        emotion = f"Good:{emo[5]} Warm:{emo[6]} Sad:{emo[7]} Angry:{emo[8]} Want:{emo[9]}"
                    else:
                        emotion = ""
                except Exception as e:
                    emotion = ""
                
                try:
                    n_elem = self.driver.find_element(By.CSS_SELECTOR, "span.u_cbox_count")
                    num_comment = n_elem.text.strip()
                except Exception as e:
                    num_comment = ""

                self.detailed_articles.append({
                    'Title': title,
                    'Date': date,
                    'Link': link,
                    'Body': body,
                    'Emotion': emotion,
                    'Comment_body': b,
                    'Comment_date': d,
                    'Comment_recomm': r,
                    'Comment_unrecomm': ur,
                    'Num_comment': num_comment
                })
            except Exception as e:
                print(f"[ERROR] Failed to extract detail article({link}): {e}")
        
        self.driver.quit()

    def save_to_database(self):
        if not self.detailed_articles:
            print('No articles to save')
            if hasattr(self, 'driver'):
                self.driver.quit()
            return
        
        file_exists = os.path.exists(self.output_file)
        with open(self.output_file, 'a', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Title', 'Date', 'Link', 'Press', 'Body', 'Emotion', 
                          'Comment_body', 'Comment_date', 'Comment_recomm', 
                          'Comment_unrecomm', 'Num_comment']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists or os.path.getsize(self.output_file) == 0:
                writer.writeheader()

            for article in self.detailed_articles:
                writer.writerow(article)

        print(f'[INFO] Finished scraping | PATH -> {self.output_file}')

    def set_start_date(self) -> str:
        if os.path.exists(self.output_file):
            df = pd.read_csv(self.output_file)
            if 'Date' in df.columns and not df.empty:
                latest_date = df['Date'].max()
                start_date = datetime.datetime.strptime(str(latest_date), "%Y%m%d") + datetime.timedelta(days=1)
                return start_date.strftime("%Y%m%d")
        return f"{self.year}0101"
    
    def run(self):
        """지정한 연도의 1월 1일부터 12월 31일까지 매일 크롤링"""
        start_date_str = self.set_start_date()
        end_date_str = f"{self.year}1231"
        current_date = datetime.datetime.strptime(start_date_str, "%Y%m%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y%m%d")
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            print(f"Processing date: {date_str}")
            self.scrape_articles(date_str)
            self.save_to_database()
            
            time.sleep(2)
            current_date += datetime.timedelta(days=1)