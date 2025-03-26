from services.nlp_service import NlpService

# Test text
text = """Chondrosarcoma is histologically classified as grade 1–3 according
to the degree of malignancy, in addition, there are dedifferentiated
and mesenchymal subtypes. Grade 3 chondrosarcoma is highly cellular with a mucomyxoid matrix and mitoses. Grade 3 chondrosarcoma tumors are mainly observed in adults, and most involve the
pelvis, followed by the femur and humerus, and have a poor prognosis.1
 Grade 3 chondrosarcoma accounts for 3%–25% of central
chondrosarcomas.1–7
Dedifferentiated chondrosarcoma is a highly malignant variant of
chondrosarcoma characterized by high-grade nonchondrosarcoma,
such as fibrosarcoma, OS, or undifferentiated pleomorphic sarcoma,
immediately adjacent to a low-grade chondroid neoplasm.8 The incidence of DDCS in all chondrosarcomas is low (1.4%)9
 and represents
10%–15% of patients with central chondrosarcoma.10,11 The prognosis of DDCS is poor, with early distant metastasis and 5-year OAS
rates of 6%–24%."""

# Initialize service and run test
nlp = NlpService()
results = nlp.test_clinical_text(text)

# Print results
print("\nExtracted Entities by Type:")
print("==========================")
for entity_type, entities in results.items():
    print(f"\n{entity_type}:")
    for e in entities:
        print(f"- {e['text']} (confidence: {e['score']:.3f}, hesitancy: {e['hesitancy']:.3f})")
