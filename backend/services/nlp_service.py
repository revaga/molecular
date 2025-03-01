from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

class NlpService:
    def __init__(self):
        model_name = "d4data/BioMedNLP-PubMedBERT"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.nlp_ner = pipeline("ner", model=self.model, tokenizer=self.tokenizer)

    def extract_entities(self, text):
        entities = self.nlp_ner(text)
        extracted_entities = []

        for entity in entities:
            entity_data = {
                "text": entity['word'],
                "label": entity['entity'],
                "score": entity['score'],
            }
            if entity['entity'] in ["GENE", "PROTEIN", "DRUG", "ANTIBODY", "INHIBITOR"]:
                extracted_entities.append(entity_data)
        return extracted_entities
