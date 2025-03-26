import os
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from transformers import T5ForConditionalGeneration, T5Tokenizer
from typing import List, Dict, Tuple
import math
import torch
import logging
from sklearn.metrics import precision_recall_fscore_support

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Linguistic term mappings
LINGUISTIC_TERMS = {
    'very_high': (0.9, 0.1),
    'high': (0.7, 0.3),
    'medium': (0.5, 0.5),
    'low': (0.3, 0.7),
    'very_low': (0.1, 0.9)
}

# Entity type mappings for PubMedBERT
ENTITY_MAPPINGS = {
    'B-DISEASE': 'DISEASE',
    'I-DISEASE': 'DISEASE',
    'B-CHEMICAL': 'DRUG',
    'I-CHEMICAL': 'DRUG',
    'B-ANATOMICAL': 'ANATOMICAL',
    'I-ANATOMICAL': 'ANATOMICAL'
}

class NlpService:
    def __init__(self):
        logger.info("Initializing NLP service...")
        
        # Initialize PubMedBERT model for NER
        model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
        logger.info(f"Loading PubMedBERT model: {model_name}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple"
            )
            logger.info("PubMedBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading PubMedBERT model: {str(e)}")
            raise
        
        # Initialize T5 model for guidelines generation
        t5_model = "t5-base"
        logger.info(f"Loading T5 model: {t5_model}")
        try:
            self.t5_tokenizer = T5Tokenizer.from_pretrained(
                t5_model,
                model_max_length=512,
                legacy=True  # Use legacy tokenizer to avoid protobuf dependency
            )
            self.t5_model = T5ForConditionalGeneration.from_pretrained(t5_model)
            logger.info("T5 model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading T5 model: {str(e)}")
            raise

    def compute_pfs(self, confidence: float) -> Tuple[float, float, float]:
        """
        Compute Pythagorean Fuzzy Sets metrics based on confidence score.
        Returns (membership degree, non-membership degree, hesitancy degree)
        """
        # Map confidence to linguistic term
        if confidence >= 0.9:
            my, mn = LINGUISTIC_TERMS['very_high']
        elif confidence >= 0.7:
            my, mn = LINGUISTIC_TERMS['high']
        elif confidence >= 0.5:
            my, mn = LINGUISTIC_TERMS['medium']
        elif confidence >= 0.3:
            my, mn = LINGUISTIC_TERMS['low']
        else:
            my, mn = LINGUISTIC_TERMS['very_low']
            
        # Calculate hesitancy degree
        h = math.sqrt(abs(1 - my**2 - mn**2))
        return my, mn, h

    def extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text using PubMedBERT."""
        try:
            logger.info("Extracting entities from text...")
            entities = self.ner_pipeline(text)
            processed_entities = []
            
            for ent in entities:
                if ent['entity_group'] in ENTITY_MAPPINGS:
                    # Handle NaN/infinite values
                    score = ent['score']
                    if not math.isfinite(score):
                        score = 0.0
                    
                    my, mn, h = self.compute_pfs(score)
                    processed_entities.append({
                        'text': ent['word'],
                        'entity_type': ENTITY_MAPPINGS[ent['entity_group']],
                        'confidence': score,
                        'my': my if math.isfinite(my) else 0.0,
                        'mn': mn if math.isfinite(mn) else 0.0,
                        'hesitancy': h if math.isfinite(h) else 0.0
                    })
            
            logger.info(f"Found {len(processed_entities)} entities")
            return processed_entities
        except Exception as e:
            logger.error(f"Error in entity extraction: {str(e)}")
            raise

    def generate_guidelines(self, target_name: str, entity_type: str) -> str:
        """Generate handling guidelines using T5."""
        prompt = f"Generate clinical guidelines for {entity_type} {target_name}:"
        inputs = self.t5_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        outputs = self.t5_model.generate(
            inputs.input_ids,
            max_length=150,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True
        )
        
        guidelines = self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return guidelines

    def calculate_metrics(self, true_labels: List[str], pred_labels: List[str]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 score."""
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels,
            pred_labels,
            average='weighted'
        )
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
