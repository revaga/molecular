import os
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from transformers import T5ForConditionalGeneration
from typing import List, Dict, Tuple
import math
import torch
import logging

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

# Entity type mappings for BioMedNLP-PubMedBERT
ENTITY_MAPPINGS = {
    'B-GENE': 'GENE',
    'I-GENE': 'GENE',
    'B-PROTEIN': 'PROTEIN',
    'I-PROTEIN': 'PROTEIN',
    'B-CHEMICAL': 'DRUG',
    'I-CHEMICAL': 'DRUG',
    'B-DISEASE': 'PATHWAY',
    'I-DISEASE': 'PATHWAY'
}

class NlpService:
    def __init__(self):
        logger.info("Initializing NLP service...")
        
        # Initialize BioBERT model for NER
        model_name = "dmis-lab/biobert-v1.1-pubmed"
        logger.info(f"Loading BioBERT model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=9,
            id2label={
                0: "O",
                1: "B-GENE",
                2: "I-GENE",
                3: "B-PROTEIN",
                4: "I-PROTEIN",
                5: "B-CHEMICAL",
                6: "I-CHEMICAL",
                7: "B-DISEASE",
                8: "I-DISEASE"
            },
            label2id={
                "O": 0,
                "B-GENE": 1,
                "I-GENE": 2,
                "B-PROTEIN": 3,
                "I-PROTEIN": 4,
                "B-CHEMICAL": 5,
                "I-CHEMICAL": 6,
                "B-DISEASE": 7,
                "I-DISEASE": 8
            }
        )
        
        # Configure NER pipeline with custom settings
        logger.info("Configuring NER pipeline...")
        self.ner_pipeline = pipeline(
            'ner',
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple",
            device=-1  # Use CPU
        )

        # Initialize T5 model for guidelines generation
        t5_model = "razent/SciFive-base-Pubmed_PMC"
        logger.info(f"Loading T5 model: {t5_model}")
        self.t5_tokenizer = AutoTokenizer.from_pretrained(t5_model)
        self.t5_model = T5ForConditionalGeneration.from_pretrained(t5_model)
        self.t5_pipeline = pipeline('text2text-generation', model=self.t5_model, tokenizer=self.t5_tokenizer)
        
        logger.info("NLP service initialization complete")

    def calculate_pfs(self, confidence: float) -> Tuple[float, float, float]:
        """
        Calculate Pythagorean Fuzzy Sets from NLP confidence score
        
        PFS Membership and Non-Membership Constraint:
        MY^2 + MN^2 ≤ 1
        where MY (Membership Degree) quantifies the certainty an entity belongs to a set
        and MN (Non-Membership Degree) quantifies the certainty it does not belong.
        
        Hesitancy Calculation in PFS:
        H = sqrt(1 - MY^2 - MN^2)
        where H (Hesitancy Degree) represents uncertainty level
        
        Args:
            confidence: NLP model confidence score (0-1)
        
        Returns:
            Tuple of (MY, MN, H) values ensuring MY^2 + MN^2 + H^2 = 1
        """
        # Initial MY based on model confidence
        MY = confidence
        max_mn = math.sqrt(1 - MY**2)
        MN = max_mn * (1 - confidence)
        H = math.sqrt(1 - MY**2 - MN**2)
        
        # Normalize to ensure MY^2 + MN^2 + H^2 = 1
        norm = math.sqrt(MY**2 + MN**2 + H**2)
        return MY/norm, MN/norm, H/norm

    def get_linguistic_term(self, MY: float, MN: float) -> str:
        """Map PFS values to linguistic term"""
        for term, (my_val, mn_val) in LINGUISTIC_TERMS.items():
            if MY >= my_val and MN <= mn_val:
                return term
        return 'medium'  # default to medium if no clear match

    def extract_entities_with_pfs(self, text: str) -> List[Dict]:
        """Extract entities and calculate PFS metrics"""
        # Clean and preprocess text
        text = text.replace('\n', ' ').strip()
        logger.info(f"Processing text of length: {len(text)}")
        
        try:
            # Get predictions from NER pipeline
            logger.info("Running NER pipeline...")
            predictions = self.ner_pipeline(text)
            logger.info(f"Got {len(predictions)} raw predictions")
            
            entities = []
            current_entity = None
            
            for pred in predictions:
                # Skip non-entity tokens
                if pred['entity'] == 'O':
                    if current_entity:
                        entities.append(current_entity)
                        current_entity = None
                    continue
                
                # Extract entity type from prediction
                entity_type = pred['entity'].split('-')[1]  # Remove B- or I- prefix
                logger.debug(f"Found token: {pred['word']} of type {entity_type}")
                
                # Handle beginning of new entity
                if pred['entity'].startswith('B-'):
                    if current_entity:
                        entities.append(current_entity)
                    
                    MY, MN, H = self.calculate_pfs(pred['score'])
                    current_entity = {
                        'text': pred['word'],
                        'type': entity_type,
                        'confidence': pred['score'],
                        'MY': MY,
                        'MN': MN,
                        'hesitancy': H,
                        'linguistic_term': self.get_linguistic_term(MY, MN),
                        'start': pred['start'],
                        'end': pred['end']
                    }
                    logger.debug(f"Started new entity: {current_entity['text']} ({current_entity['type']})")
                
                # Handle continuation of current entity
                elif pred['entity'].startswith('I-') and current_entity:
                    if current_entity['type'] == entity_type:
                        current_entity['text'] += ' ' + pred['word']
                        current_entity['end'] = pred['end']
                        # Update confidence with average
                        current_entity['confidence'] = (current_entity['confidence'] + pred['score']) / 2
                        MY, MN, H = self.calculate_pfs(current_entity['confidence'])
                        current_entity.update({
                            'MY': MY,
                            'MN': MN,
                            'hesitancy': H,
                            'linguistic_term': self.get_linguistic_term(MY, MN)
                        })
                        logger.debug(f"Updated entity: {current_entity['text']}")
            
            # Add the last entity if it exists
            if current_entity:
                entities.append(current_entity)
            
            logger.info(f"Found {len(entities)} entities")
            for entity in entities:
                logger.info(f"Entity: {entity['text']} ({entity['type']}) - Confidence: {entity['confidence']:.2f}")
            
            return entities
        except Exception as e:
            logger.error(f"Error in extract_entities_with_pfs: {str(e)}")
            return []

    def generate_guidelines(self, target_name: str, context: str = "") -> str:
        """Generate handling guidelines for a molecular target using T5"""
        prompt = f"Generate safety guidelines for handling {target_name}."
        if context:
            prompt += f" Context: {context}"
        
        result = self.t5_pipeline(prompt, max_length=200, num_return_sequences=1)[0]
        return result['generated_text']

    def calculate_metrics(self, true_positives: int, false_positives: int, false_negatives: int) -> Dict[str, float]:
        """Calculate precision, recall, and F1-score"""
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
