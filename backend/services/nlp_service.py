import os
import logging
import math
from typing import List, Dict, Tuple
import requests
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
)
from sklearn.metrics import precision_recall_fscore_support
from difflib import get_close_matches
import re

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LINGUISTIC_TERMS = {
    'very_high': (0.9, 0.1),
    'high': (0.7, 0.3),
    'medium': (0.5, 0.5),
    'low': (0.3, 0.7),
    'very_low': (0.1, 0.9)
}

# Instead of mapping from Hugging Face tags, we'll define static known targets/drugs:
# (Populate/expand these as you wish)
KNOWN_TARGETS = {
    "BCL-2", "PTHRPP", "CD44", "IHH", "PDGFRB", 
    "COX-2", "PPARC", "XIAP", "HDAC", "VEGF"
}
KNOWN_DRUGS = {
    "siRNA", "2ME", "Anti-PTHrP", "Pioglitazone", "Anti-CD44",
    "EGCG", "Imatinib", "Sunitinib", "Celecoxib", 
    "15d-PGJ2", "HDAC inhibitors", "VEGF inhibitors"
}
# Possible synonyms or variations (optional)
SYNONYMS = {
    "BCL2": "BCL-2", 
    "COX2": "COX-2",
    "PDGFR-BETA": "PDGFRB",
    "PTHRPP": "PTHRPP",  # Example if you see 'PTHrP' or 'PTHRPP'
    # etc.
}

# Mapping from known targets to known related drugs (as in your original code)
KNOWN_TARGET_DRUGS = {
    "BCL-2": ["siRNA", "2ME"],
    "PTHRPP": ["Anti-PTHrP", "Pioglitazone"],
    "CD44": ["Anti-CD44"],
    "IHH": ["EGCG"],
    "PDGFRB": ["Imatinib", "Sunitinib"],
    "COX-2": ["Celecoxib"],
    "PPARC": ["15d-PGJ2", "Pioglitazone"],
    "XIAP": ["siRNA"],
    "HDAC": ["HDAC inhibitors"],
    "VEGF": ["VEGF inhibitors"]
}

class NlpService:
    def __init__(self):
        logger.info("Initializing static rule-based pipeline...")

        # (No huggingface model loading here)
        logger.info("Rule-based NER pipeline initialized.")

        # Still load T5 if you need it for guidelines generation
        t5_model = "t5-base"
        logger.info("Loading T5 model...")
        self.t5_tokenizer = T5Tokenizer.from_pretrained(t5_model)
        self.t5_model = T5ForConditionalGeneration.from_pretrained(t5_model)
        logger.info("T5 model loaded successfully.")

    def compute_pfs(self, confidence: float) -> Tuple[float, float, float]:
        """
        Convert a confidence (0..1) into fuzzy membership (my, mn)
        and compute hesitancy h. This is carried over from your original logic.
        """
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
        h = math.sqrt(abs(1 - my ** 2 - mn ** 2))
        return my, mn, h

    def fetch_drugs_from_dgidb(self, target: str) -> List[str]:
        """
        Optionally fetch known drug interactions from DGIdb
        if we don't already have them in KNOWN_TARGET_DRUGS.
        """
        try:
            url = f"https://dgidb.org/api/v2/interactions.json?genes={target}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            matched = data.get("matchedTerms", [])
            for item in matched:
                if item.get("geneName", "").upper() == target.upper():
                    return [i["drugName"] for i in item.get("interactions", [])]
        except Exception as e:
            logger.warning(f"[DGIdb] Failed to fetch drugs for {target}: {e}")
        return []

    def fuzzy_match_target(self, word: str) -> str:
        """
        Fuzzy match the extracted token to known target keys (e.g., 'BCL-2', 'COX-2', etc.).
        If no match found, just return the original word.
        """
        all_known_targets = list(KNOWN_TARGET_DRUGS.keys())
        match = get_close_matches(word.upper(), all_known_targets, n=1, cutoff=0.85)
        return match[0] if match else word

    def tokenize_text(self, text: str) -> List[str]:
        """
        Basic tokenizer that preserves letters, digits, and dashes.
        Adjust if needed.
        """
        return re.findall(r"[a-zA-Z0-9\-\']+", text)

    def extract_entities(self, text: str) -> List[Dict]:
        """
        Main method for entity extraction, but now purely static/dictionary-based.
        1) Tokenize the text.
        2) Check if each token is a known target or drug (directly or via synonyms/fuzzy).
        3) Assign a synthetic confidence score (e.g., 0.99).
        4) Convert confidence to (my, mn, h).
        5) Return the resulting list of entities.
        """
        logger.info("Extracting entities (static pipeline) from text...")

        tokens = self.tokenize_text(text)
        merged = []
        seen = set()

        for tok in tokens:
            original_tok = tok  # store
            upper_tok = tok.upper()

            # Check synonyms
            if upper_tok in SYNONYMS:
                upper_tok = SYNONYMS[upper_tok].upper()

            # Decide entity_type
            if upper_tok in (t.upper() for t in KNOWN_TARGETS):
                entity_type = "TARGET"
            elif upper_tok in (d.upper() for d in KNOWN_DRUGS):
                entity_type = "DRUG"
            else:
                # Optionally do fuzzy target matching 
                # (Only if you want to treat near matches as targets)
                # For drugs, you could do something similar if you wish.
                possible_match = self.fuzzy_match_target(upper_tok)
                if possible_match.upper() in (t.upper() for t in KNOWN_TARGETS):
                    entity_type = "TARGET"
                    upper_tok = possible_match.upper()
                else:
                    continue  # Not recognized as target or drug

            # Avoid duplicates
            if upper_tok in seen:
                continue

            # Synthetic confidence
            confidence = 0.99  # or 1.0, or anything
            my, mn, h = self.compute_pfs(confidence)

            entity = {
                'text': original_tok,
                'entity_type': entity_type,
                'confidence': confidence,
                'my': my,
                'mn': mn,
                'hesitancy': h
            }

            # If it's a TARGET, see if we have related drugs
            if entity_type == "TARGET":
                # upper_tok might be e.g. 'BCL-2'
                related = KNOWN_TARGET_DRUGS.get(upper_tok, [])
                if not related:
                    # Optionally fetch from DGIdb
                    related = self.fetch_drugs_from_dgidb(upper_tok)
                if related:
                    entity["related_drugs"] = related

            merged.append(entity)
            seen.add(upper_tok)

        logger.info(f"Returning {len(merged)} processed entities (static pipeline)")
        return merged

    def organize_entities_by_type(self, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group entities into 'targets', 'drugs', 'diseases', 'anatomical' lists.
        In this static version, we only have 'targets' and 'drugs' (unless you define more).
        """
        organized = {"targets": [], "drugs": [], "diseases": [], "anatomical": []}
        for ent in entities:
            etype = ent["entity_type"].lower()
            if etype == "target":
                organized["targets"].append(ent)
            elif etype == "drug":
                organized["drugs"].append(ent)
            elif etype == "disease":
                organized["diseases"].append(ent)
            elif etype == "anatomical":
                organized["anatomical"].append(ent)
        return organized

    def aggregate_pfs_values(self, entities: List[Dict]) -> Tuple[float, float, float]:
        """
        Average my, mn, and hesitancy across all entities.
        """
        total_my = sum(e['my'] for e in entities)
        total_mn = sum(e['mn'] for e in entities)
        total_h = sum(e['hesitancy'] for e in entities)
        n = len(entities)
        return (
            total_my / n if n else 0,
            total_mn / n if n else 0,
            total_h / n if n else 0
        )

    def generate_guidelines(self, target_name: str, entity_type: str) -> str:
        """
        Generate guidelines using a T5 model (unchanged from your original code).
        """
        prompt = f"Generate clinical guidelines for {entity_type} {target_name}:"
        inputs = self.t5_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = self.t5_model.generate(
            inputs.input_ids,
            max_length=150,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True
        )
        return self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)

    def calculate_metrics(self, true_labels: List[str], pred_labels: List[str]) -> Dict[str, float]:
        """
        Calculate precision, recall, and F1 score for a set of labels.
        (Kept from your original code for completeness.)
        """
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, pred_labels, average='weighted', zero_division=0
        )
        return {'precision': precision, 'recall': recall, 'f1': f1}


# -------------------------
# Example usage (if you want to try locally):
# -------------------------
if __name__ == "__main__":
    service = NlpService()
    sample_text = """
        Bcl-2 is known to be anti-apoptotic. 
        Pioglitazone is a PPARc ligand. 
        Another drug is 2ME. 
        Also note that PDGFRB can be inhibited by Imatinib.
    """
    # 1) Extract
    entities = service.extract_entities(sample_text)
    print("Entities (static extraction):")
    for e in entities:
        print(e)

    # 2) Organize
    organized = service.organize_entities_by_type(entities)
    print("\nOrganized by type:")
    print(organized)

    # 3) Optional: generate guidelines for the first target
    if organized["targets"]:
        first_target = organized["targets"][0]["text"]
        guidelines = service.generate_guidelines(first_target, "target")
        print(f"\nGuidelines for target '{first_target}':\n{guidelines}")
