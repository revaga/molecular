import math
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

class NlpService:
    def __init__(self):
        model_name = "d4data/BioMedNLP-PubMedBERT"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.nlp_ner = pipeline("ner", model=self.model, tokenizer=self.tokenizer)

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
        entities = self.nlp_ner(text)
        extracted_entities = []

        for entity in entities:
            # Extract the word and its confidence score
            entity_data = {
                "text": entity['word'],
                "label": entity['entity'],
                "score": entity['score'],
            }

            # Filter entities related to molecular targets (genes, proteins, drugs, etc.)
            if entity['entity'] in ["GENE", "PROTEIN", "DRUG", "ANTIBODY", "INHIBITOR"]:
                MY, MN, H = self.calculate_pfs(entity_data['score'])

                entity_data['MY'] = MY
                entity_data['MN'] = MN
                entity_data['H'] = H

                extracted_entities.append(entity_data)

        return extracted_entities
