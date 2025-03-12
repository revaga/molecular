import os
from transformers import AutoTokenizer, AutoModelForTokenClassification, T5ForConditionalGeneration, T5Tokenizer
from transformers import pipeline
from typing import List, Dict, Tuple
import math

# Linguistic term mappings
LINGUISTIC_TERMS = {
    'very_high': (0.9, 0.1),
    'high': (0.7, 0.3),
    'medium': (0.5, 0.5),
    'low': (0.3, 0.7),
    'very_low': (0.1, 0.9)
}

class NlpService:
    def __init__(self):
        # Initialize BioMERT model
        model_path = 'BioMedNLP-PubMedBERT'
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.ner_pipeline = pipeline('ner', model=self.model, tokenizer=self.tokenizer)
        
        # Initialize T5 model for guideline generation
        self.t5_model_name = 'mrm8488/t5-base-finetuned-bio-medical'
        self.t5_tokenizer = T5Tokenizer.from_pretrained(self.t5_model_name)
        self.t5_model = T5ForConditionalGeneration.from_pretrained(self.t5_model_name)

    def calculate_pfs(self, confidence: float) -> Tuple[float, float, float]:
        """
        Calculate Pythagorean Fuzzy Sets from NLP confidence score
        
        Args:
            confidence: NLP model confidence score (0-1)
        
        Returns:
            Tuple of (MY, MN, H) values
        """
        MY = confidence
        MN = 1 - confidence
        H = math.sqrt(1 - MY**2 - MN**2)
        
        # Normalize to ensure MY^2 + MN^2 + H^2 = 1
        norm = math.sqrt(MY**2 + MN**2 + H**2)
        return MY/norm, MN/norm, H/norm

    def get_linguistic_term(self, MY: float, MN: float) -> str:
        """
        Map PFS values to linguistic term
        """
        for term, (my_val, mn_val) in LINGUISTIC_TERMS.items():
            if MY >= my_val and MN <= mn_val:
                return term
        return 'unknown'

    def extract_entities_with_pfs(self, text: str) -> List[Dict]:
        """
        Extract entities with PFS calculations
        """
        predictions = self.ner_pipeline(text)
        entities = []
        
        target_types = {'GENE', 'PROTEIN', 'PATHWAY'}
        therapy_types = {'DRUG', 'INHIBITOR', 'ANTIBODY'}
        
        for pred in predictions:
            entity_type = pred['entity_group']
            if entity_type in target_types.union(therapy_types):
                MY, MN, H = self.calculate_pfs(pred['score'])
                entities.append({
                    'text': pred['word'],
                    'type': entity_type,
                    'confidence': pred['score'],
                    'MY': MY,
                    'MN': MN,
                    'hesitancy': H,
                    'linguistic_term': self.get_linguistic_term(MY, MN)
                })
        
        return entities

    def generate_guidelines(self, target: str, context: str) -> str:
        """
        Generate handling guidelines for a molecular target
        
        Args:
            target: The molecular target name
            context: Contextual information about the target
        
        Returns:
            Generated handling guidelines
        """
        input_text = f"Generate handling guidelines for {target}: {context}"
        input_ids = self.t5_tokenizer.encode(input_text, return_tensors='pt')
        
        # Generate guidelines
        outputs = self.t5_model.generate(
            input_ids,
            max_length=200,
            num_beams=4,
            early_stopping=True
        )
        
        return self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)