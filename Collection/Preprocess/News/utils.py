import re
import numpy as np

def categorize_document(text):
    patterns = {
        "공시": r"^\[.*공시.*\]",
        "인사": r"^\[인사\]",
        "표": r"^\[표\]",
        "메모": r"^\[오늘의 메모\]",
        "추천": r"^\[주간추천주\]",
        "부고": r"^\[부고\]",
        "속보": r"^\[속보\]",
        "단독": r"^\[단독\]",
        "인터뷰": r"\[인터뷰\]",
        "영상": r"\[영상\]"
    }
    if not isinstance(text, str):
        return "NotText"
    for key, value in patterns.items():
        if re.match(value, text):
            return key
    for cat in [r"순매수 상위 종목\s*\n\n", r"순매도 상위 종목\s*\n\n"]:
        if re.match(cat, text):
            return "순매수/매도"
    return np.nan

def convert_hanja(text):
    hanja_dict = {
        "美": "미국", "軍": "군대", "日": "일본", "中": "중국", "英": "영국", "亞": "아시아",
        "獨": "독일", "佛": "프랑스", "加": "캐나다", "露": "러시아", "印": "인도",
        "西": "스페인", "濠": "호주", "韓": "한국", "北": "북한", "南": "남한",
        "港": "홍콩", "台": "대만", "新": "싱가포르", "越": "베트남", "泰": "태국"
    }
    if not isinstance(text, str):
        return text
    for hanja, korean in hanja_dict.items():
        text = text.replace(hanja, korean)
    return text

def remove_special_characters(text):
    if not isinstance(text, str):
        return text
    return re.sub(r"[^\w\sㄱ-ㅎ가-힣\.\(\)%]", "", text)

def process_body(text):
    if not isinstance(text, str):
        return text

    lines = text.split("\n")
    lines = [line for line in lines if "ⓒ" not in line]
    lines = [line for line in lines if "@" not in line]
    text = "\n".join(lines)

    text = re.sub(r"\[.*?\]", "", text)

    text = re.sub(r'\d{4}[.-]?\d{1,2}[.-]?\d{1,2}', '', text)
    
    text = re.sub(r'\b[가-힣]{2,4}\s*기자\b', '', text)
    
    remove_patterns = [
        r"▶.*",
        r"☞.*",
        r"【.*?】",
        r".*? 기자입니다\.",
        r".*? 기자가 취재했습니다\.",
        r".*? 추천$",
        r".*? 이 기사는 .*",
        r".*? 사진제공=.*",
        r".*? 그래픽.*",
        r"사진\s*=",
        r"\(이하 .*?\)",
        r"!\[image.*\]\(attachment:.*?\)",
        r"\([^)]*?=[^)]*?뉴스\)"
    ]

    for pattern in remove_patterns:
        text = re.sub(pattern, "", text)
    
    paragraphs = re.split(r'\n{1,}', text)
    paragraphs = [p for p in paragraphs if p.strip().endswith('.')]
    text = "\n\n".join(paragraphs)

    return text