import os
import sys
import pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def start_browser(driver_path):
    print('Initialize browser...')
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--start-maximized')
    # chrome_options.add_argument('--headless')
    try:
        if driver_path and os.path.exists(driver_path):
            driver = webdriver.Chrome(
                service=Service(driver_path),
                options=chrome_options
            )
        else:
            driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(2)
        print('Browser initialized successfully!')
        return driver
    except Exception as e:
        print(f'Something went wrong... Message below:\n\n{e}')
        sys.exit(1)


def main():
    base_dir = "./Data/News/Raw"
    files = [os.path.join(base_dir, file) for file in os.listdir(base_dir) 
             if file.endswith(".csv")]
    driver_path = "./chromedriver"

    for file in files:
        print(f"\nProcessing file: {file}")
        df = pd.read_csv(file, encoding="utf-8")

        # Section 컬럼이 없으면 미리 추가
        if "Summarization" not in df.columns:
            df["Summarization"] = None

        driver = start_browser(driver_path)

        # enumerate(df.iterrows()) -> (순번, (인덱스, Series))
        for idx, (row_idx, row) in tqdm(enumerate(df.iterrows()), total=len(df)):

            # 이미 Section에 값이 있다면(=이미 처리됨) 스킵
            # pd.notna(row["Section"])로도 체크 가능
            if not pd.isna(row["Summarization"]):
                continue

            # Link가 NaN이면 스킵
            if pd.isna(row["Link"]):
                continue

            driver.get(row["Link"])

            try:
                button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.media_end_head_autosummary_button._toggle_btn._SUMMARY_BTN"))
                )
                button.click()

                summary_div = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "div._contents_body._SUMMARY_CONTENT_BODY")
                    )
                )
                summary_text = summary_div.text.strip()
                print(summary_text)

                df.loc[row_idx, "Summarization"] = summary_text
            
            except Exception as e:
                pass

            # 100개 단위로 중간 저장
            if (idx + 1) % 100 == 0:
                df.to_csv(file, index=False, encoding="utf-8")
                print(f"Saved partial results for first {idx + 1} rows.")

        # 모든 처리 완료 후 최종 저장
        df.to_csv(file, index=False, encoding="utf-8")
        driver.quit()

if __name__ == "__main__":
    main()