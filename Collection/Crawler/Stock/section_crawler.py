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
    chrome_options.add_argument('--headless')
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
        if "Section" not in df.columns:
            df["Section"] = None

        driver = start_browser(driver_path)

        # enumerate(df.iterrows()) -> (순번, (인덱스, Series))
        for idx, (row_idx, row) in tqdm(enumerate(df.iterrows()), total=len(df)):

            # 이미 Section에 값이 있다면(=이미 처리됨) 스킵
            # pd.notna(row["Section"])로도 체크 가능
            if not pd.isna(row["Section"]):
                continue

            # Link가 NaN이면 스킵
            if pd.isna(row["Link"]):
                continue

            driver.get(row["Link"])

            try:
                categories = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".media_end_categorize_item"))
                )
                cat_texts = [cat.text.strip() for cat in categories if cat.text.strip()]

                if cat_texts:
                    df.loc[row_idx, "Section"] = "/".join(cat_texts)
                else:
                    df.loc[row_idx, "Section"] = None

            except Exception:
                df.loc[row_idx, "Section"] = None

            # 100개 단위로 중간 저장
            if (idx + 1) % 100 == 0:
                df.to_csv(file, index=False, encoding="utf-8")
                print(f"Saved partial results for first {idx + 1} rows.")

        # 모든 처리 완료 후 최종 저장
        df.to_csv(file, index=False, encoding="utf-8")
        driver.quit()

if __name__ == "__main__":
    main()
