import torch
from transformers import (
    AutoModel,
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification
)
import random
import numpy as np

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

set_seed(42)

class FinancialNLP:
    def __init__(self, model_name="kakaobank/kf-deberta-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.base_model = AutoModel.from_pretrained(model_name).to(self.device)
        self._init_ner_model()
        self._init_ad_classifier()
        self._init_sentiment_analyzer()

    def _init_ner_model(self):
        """Initalize financial-NER model"""
        self.ner_model = AutoModelForTokenClassification.from_pretrained(
            "kakaobank/kf-deberta-base",
            num_labels=11,
            id2label={
                0: "O", 1: "B-FC", 2: "I-FC", 3: "B-FT",
                4: "I-FT", 5: "B-FI", 6: "I-FI", 7: "B-FE",
                8: "I-FE", 9: "B-FX", 10: "I-FX"
            }
        ).to(self.device)

    def _init_ad_classifier(self):
        """Initalize AD-news classifier"""
        self.ad_model = AutoModelForSequenceClassification.from_pretrained(
            "kakaobank/kf-deberta-base",
            num_labels=2
        ).to(self.device)

    def _init_sentiment_analyzer(self):
        """Initalize sentiment analyzer"""
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            "kakaobank/kf-deberta-base",
            num_labels=3
        ).to(self.device)

    def check_and_truncate(self, text, max_tokens=510):
        """
        Check text token length and adjust length
        Args:
            text (str): Input text
            max_tokens (int): Maximum token
        """
        tokens = self.tokenizer.tokenize(text)
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[:max_tokens]
            return self.tokenizer.convert_tokens_to_string(truncated_tokens)
        return text

    def analyze_ner(self, text):
        """
        Analyze financial entities
        Returns:
            List[Dict]: {entity: entity name, type: type of entity, start: start position, end: end position}
        """
        processed_text = self.check_and_truncate(text)
        inputs = self.tokenizer(
            processed_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.ner_model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().numpy()

        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        entities = []
        current_entity = None

        for i, (token, pred_idx) in enumerate(zip(tokens, predictions)):
            label = self.ner_model.config.id2label[pred_idx]
            if label == "O":
                if current_entity:
                    entities.append(current_entity)
                current_entity = None
                continue

            _, entity_type = label.split("-")
            if label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    "entity": self.tokenizer.convert_tokens_to_string([token]),
                    "type": entity_type,
                    "start": i,
                    "end": i+1
                }
            elif label.startswith("I-") and current_entity:
                current_entity["entity"] += self.tokenizer.convert_tokens_to_string([token])
                current_entity["end"] = i+1

        if current_entity:
            entities.append(current_entity)

        char_pos = 0
        for entity in entities:
            start_token = tokens[entity["start"]]
            end_token = tokens[entity["end"]-1]
            char_start = processed_text.find(start_token.lstrip('##'), char_pos)
            char_end = processed_text.find(end_token.lstrip('##'), char_start) + len(end_token.lstrip('##'))
            entity["start"] = char_start
            entity["end"] = char_end
            char_pos = char_end

        return entities

    def classify_ad(self, text):
        """
        Classify advertisement news
        Returns:
            Dict: {label: 0(General)/1(Ad), confidence}
        """
        processed_text = self.check_and_truncate(text)
        inputs = self.tokenizer(
            processed_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.ad_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, pred = torch.max(probs, dim=1)

        return {
            "label": pred.item(),
            "confidence": confidence.item()
        }

    def analyze_sentiment(self, text):
        """
        Analyze financial-sentiment
        Returns:
            Dict: {label: 0(Positive)/1(Neutral)/2(Negative), confidence}
        """
        processed_text = self.check_and_truncate(text)
        inputs = self.tokenizer(
            processed_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.sentiment_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, pred = torch.max(probs, dim=1)

        print(probs)
        return {
            "label": pred.item(),
            "confidence": confidence.item()
        }

    def batch_predict(self, texts, task='all'):
        """
        Predict batch
        Args:
            task: 'ner', 'ad', 'sentiment', 'all'
        """
        processed_texts = [self.check_and_truncate(t) for t in texts]
        inputs = self.tokenizer(
            processed_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        results = []
        with torch.no_grad():
            if task == 'ner':
                outputs = self.ner_model(**inputs)
            elif task == 'ad':
                outputs = self.ad_model(**inputs)
            elif task == 'sentiment':
                outputs = self.sentiment_model(**inputs)
            else:
                raise ValueError("Not supported task")

        return results
