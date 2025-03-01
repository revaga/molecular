# Load the tokenizer and model
model_name = "d4data/BioMedNLP-PubMedBERT"  # Replace with the exact model name if it's different
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)

# Set up the NER pipeline
nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer)


#replace with pdf input later
text = """This is a sample text mentioning gene BRCA1 and protein p53, along with drugs such as Tamoxifen 
and inhibitors like Trastuzumab, which target molecular pathways related to breast cancer."""

# Run the NER pipeline on the input text
entities = nlp_ner(text)


# Store the entities and their confidence scores
extracted_entities = []

for entity in entities:
    entity_data = {
        "text": entity['word'],
        "label": entity['entity'],
        "score": entity['score'],
    }
    
    # You can add filtering logic for relevant entities like genes, proteins, drugs, etc.
    if entity['entity'] in ["GENE", "PROTEIN", "DRUG", "ANTIBODY", "INHIBITOR"]:
        extracted_entities.append(entity_data)

# Output the extracted entities
for entity in extracted_entities:
    print(f"Entity: {entity['text']}, Label: {entity['label']}, Confidence Score: {entity['score']:.4f}")


"""
Extracted Entities goal format
Entity: BRCA1, Label: GENE, Confidence Score: 0.9987
Entity: p53, Label: PROTEIN, Confidence Score: 0.9978
Entity: Tamoxifen, Label: DRUG, Confidence Score: 0.9876
Entity: Trastuzumab, Label: ANTIBODY, Confidence Score: 0.9923
"""