import spacy

# Load the spaCy model once
nlp = spacy.load("en_core_web_sm")

def extract_clauses(text: str) -> list:
    """
    Extracts clauses/sentences from the given text using spaCy.
    Returns a list of non-empty clauses.
    """
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def save_clauses(clauses, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for clause in clauses:
            f.write(clause + "\n")

# Example usage
if __name__ == "__main__":
    sample_text = """
    The company reported a profit of $1 million this quarter.
    This agreement is binding under the law.
    He definately made a mistake in the report.
    """
    clauses = extract_clauses(sample_text)
    print("Extracted Clauses:")
    for c in clauses:
        print("-", c)

