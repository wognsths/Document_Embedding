import os
import json

def main():
    input_dir = "./Data/News/Embeddings"
    # input_dir 내에서 checkpoint 파일 목록 가져오기
    files = [file for file in os.listdir(input_dir) if "checkpoint" in file]
    
    for file in files:
        file_path = os.path.join(input_dir, file)
        with open(file_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        
        total_count = len(data)
        print(f"파일 {file}의 전체 데이터 개수: {total_count}")
        
        # 상반기(Q1)와 하반기(Q2) 데이터를 담을 리스트 초기화
        q1_data = []
        q2_data = []
        
        # 각 행의 id에서 월을 추출하여 해당 분기에 추가 (id는 "YYYYMMDD_{번호}" 형식)
        for row in data:
            # "id" 또는 "ID" 필드 사용
            row_id = row.get("id") or row.get("ID")
            if not row_id or len(row_id) < 8:
                continue  # id가 없거나 형식이 잘못된 경우 건너뜁니다.
            try:
                month = int(row_id[4:6])
            except ValueError:
                continue  # 월 추출 실패 시 건너뜁니다.
            
            if 1 <= month <= 6:
                q1_data.append(row)
            elif 7 <= month <= 12:
                q2_data.append(row)
        
        # 파일 이름 형식: checkpoint_005930_{year}.json 에서 {year} 추출
        parts = file.split("_")
        if len(parts) < 3:
            print(f"파일 이름 형식 오류: {file}")
            continue
        year_with_ext = parts[-1]  # 예: "2020.json"
        year = year_with_ext.split(".")[0]
        
        # 출력 파일 이름 정의: 005930_{year}_Q1.json, 005930_{year}_Q2.json
        q1_filename = f"005930_{year}_Q1.json"
        q2_filename = f"005930_{year}_Q2.json"
        q1_path = os.path.join(input_dir, q1_filename)
        q2_path = os.path.join(input_dir, q2_filename)
        
        # JSON 파일 저장 (빈 리스트여도 저장합니다)
        with open(q1_path, "w", encoding="utf-8") as f:
            json.dump(q1_data, f, ensure_ascii=False, indent=4)
        with open(q2_path, "w", encoding="utf-8") as f:
            json.dump(q2_data, f, ensure_ascii=False, indent=4)
        
        print(f"{file} 처리 완료 -> 전체: {total_count}개, {q1_filename} ({len(q1_data)}개), {q2_filename} ({len(q2_data)}개)")

if __name__ == "__main__":
    main()
