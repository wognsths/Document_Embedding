import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification
from Model.Language.financial_nlp import FinancialNLP
from kiwipiepy import Kiwi  # Kiwi 라이브러리 임포트

def extract_nouns(text):
    kiwi = Kiwi()
    # 전체 텍스트에 대해 문장별로 분석 결과를 가져옴 (각 문장은 여러 후보 분석을 포함)
    results = kiwi.analyze(text, top_n=1)
    nouns = []
    for sentence in results:
        # 각 문장에 대해 최적의 후보(첫 번째 후보)를 선택
        best_candidate = sentence[0]
        for token in best_candidate:
            if token.tag in ['NNG', 'NNP']:
                nouns.append(token.form)
    return " ".join(nouns)

if __name__ == '__main__':
    # 테스트용 샘플 텍스트
    sample_text = "하락"
    extracted_text = extract_nouns(sample_text)
    print("명사 추출 결과:", extracted_text)

    # 모델 인스턴스 생성
    financial_nlp = FinancialNLP(model_name="upskyy/kf-deberta-multitask")

    # NER 분석 테스트 (추출된 명사 텍스트 사용)
    ner_result = financial_nlp.analyze_ner(extracted_text)
    print("NER 결과:", ner_result)

    # AD 뉴스 분류 테스트 (추출된 명사 텍스트 사용)
    ad_result = financial_nlp.classify_ad(extracted_text)
    print("AD 뉴스 분류 결과:", ad_result)

    # 감성 분석 테스트 (추출된 명사 텍스트 사용)
    sentiment_result = financial_nlp.analyze_sentiment(extracted_text)
    print("감성 분석 결과:", sentiment_result)
