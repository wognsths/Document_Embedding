import json
import os
from argparse import ArgumentParser
from datetime import datetime, timedelta

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-w', '--window_size', type=int, required=True)
    parser.add_argument('-m', '--minimum_sample', type=int, required=True)
    return parser

def main():
    args = create_parser().parse_args()
    window_size = args.window_size      # 예: 30일
    minimum_sample = args.minimum_sample  # 예: 200개

    embedding_path = "./Data/News/Embeddings"
    # "_Q" 문자열이 들어간 파일들만 리스트업
    file_dirs = [
        os.path.join(embedding_path, file)
        for file in os.listdir(embedding_path)
        if "_Q" in file
    ]

    # 모든 JSON 파일을 한 번에 메모리로 로드하되, "ID" 컬럼만 저장
    file_data = {}
    for file in file_dirs:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            file_data[file] = [item["ID"] for item in data]

    start_date = datetime.strptime("20190101", "%Y%m%d")
    end_date = datetime.strptime("20250321", "%Y%m%d")

    results = []

    # 하루씩 이동하는 슬라이딩 윈도우
    current_date = start_date
    while current_date + timedelta(days=window_size - 1) <= end_date:
        print(f"Current date: {current_date}")
        # 윈도우에 포함되는 날짜들
        date_range = [current_date + timedelta(days=i) for i in range(window_size)]
        
        # 윈도우 시작 및 종료 날짜를 문자열로 (YYYYMMDD)
        window_start_str = current_date.strftime("%Y%m%d")
        window_end = current_date + timedelta(days=window_size - 1)
        window_end_str = window_end.strftime("%Y%m%d")
        
        # 각 날짜에 대해 필요한 연/반기(Q1/Q2) 리스트 생성
        quarter_list = []
        for d in date_range:
            if d.month > 6:
                quarter_list.append(f"{d.year}_Q2")
            else:
                quarter_list.append(f"{d.year}_Q1")
        quarter_list = list(set(quarter_list))  # 중복 제거

        # quarter_list에 해당하는 파일들 매칭
        matched_files = []
        for q in quarter_list:
            for f in file_dirs:
                if q in f:
                    matched_files.append(f)
        matched_files = list(set(matched_files))  # 중복 제거

        # 매칭된 파일들에서 윈도우 기간에 해당하는 ID만 수집
        all_ids = []
        for mf in matched_files:
            valid_ids = [id for id in file_data[mf] if window_start_str <= id[:8] <= window_end_str]
            all_ids.extend(valid_ids)

        # 최소 샘플 개수 미달 시 하루씩 과거로 확장(backfill)
        back_offset = 1
        while len(all_ids) < minimum_sample:
            back_date = current_date - timedelta(days=back_offset)
            if back_date < datetime.strptime("20100101", "%Y%m%d"):
                break
            if back_date.month > 6:
                back_q = f"{back_date.year}_Q2"
            else:
                back_q = f"{back_date.year}_Q1"

            new_files = []
            for f in file_dirs:
                if back_q in f:
                    new_files.append(f)
            new_files = list(set(new_files))

            # 기존에 매칭되지 않은 파일들만 추가
            for nf in new_files:
                if nf not in matched_files:
                    matched_files.append(nf)
                    valid_ids = [id for id in file_data[nf] if window_start_str <= id[:8] <= window_end_str]
                    all_ids.extend(valid_ids)

            back_offset += 1
            # 무한 루프 방지를 위한 한계 설정 (예: 5년치까지)
            if back_offset > 365 * 5:
                break

        result_dict = {
            window_end_str: [os.path.basename(x) for x in matched_files],
            "IDs": all_ids
        }
        results.append(result_dict)

        # 하루씩 이동 (슬라이딩 윈도우)
        current_date += timedelta(days=1)

    output_file = f"./Analysis/reference_{window_size}.json"
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

    print(f"Done! Saved results to {output_file}")

if __name__ == "__main__":
    main()
