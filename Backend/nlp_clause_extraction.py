import spacy

nlp = spacy.load("en_core_web_sm")

def extract_clauses(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

def save_clauses(clauses, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for clause in clauses:
            f.write(clause + "\n")
