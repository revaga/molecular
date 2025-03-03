import math
import os
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

class NlpService:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models')
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.ner_pipeline = pipeline("ner", model=self.model, tokenizer=self.tokenizer)

    def calculate_pfs(self, score):
        """
        Calculate the Membership (MY), Non-membership (MN) and Hesitancy (H)
        based on the confidence score.
        """
        # MY (Membership degree) is the confidence score
        MY = score
        # MN (Non-membership degree) is 1 - MY (assuming binary fuzzy logic)
        MN = math.sqrt(1 - MY**2) if MY**2 <= 1 else 0

        # Hesitancy degree
        H = math.sqrt(1 - MY**2 - MN**2) if MY**2 + MN**2 <= 1 else 0

        return MY, MN, H

    def extract_entities(self, text):
        entities = self.ner_pipeline(text)
        result = []
        
        for entity in entities:
            score = entity['score']
            MY, MN, H = self.calculate_pfs(score)
            
            result.append({
                "text": entity['word'],
                "label": entity['entity'],
                "score": score,
                "MY": MY,
                "MN": MN,
                "H": H
            })
            
        return result
