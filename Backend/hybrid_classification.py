import re
from transformers import pipeline

# Rule-based keywords
GRAMMAR_RULES = [
    r"\bteh\b", r"\brecieve\b", r"\bdefinately\b",
    r"\btheir\b\s+\bthere\b", r"\bwas\b\s+\bwere\b"
]
FINANCIAL_KEYWORDS = ["profit", "revenue", "loss", "expense", "tax", "%", "$", "income", "budget"]
LEGAL_KEYWORDS = ["agreement", "contract", "liability", "clause", "penalty", "terms", "conditions"]

# Rule-based classifier
def classify_clause_rule_based(clause: str) -> str:
    for pattern in GRAMMAR_RULES:
        if re.search(pattern, clause, re.IGNORECASE):
            return "grammatical"
    if any(word.lower() in clause.lower() for word in FINANCIAL_KEYWORDS):
        return "financial"
    if any(word.lower() in clause.lower() for word in LEGAL_KEYWORDS):
        return "legal"
    return "unknown"

# Zero-shot classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
ZERO_SHOT_LABELS = ["financial", "legal", "grammatical", "unknown"]

def classify_clause_zero_shot(clause: str) -> str:
    result = classifier(clause, candidate_labels=ZERO_SHOT_LABELS)
    return result['labels'][0]

# Hybrid classification
def classify_clause_hybrid(clause: str) -> str:
    label = classify_clause_rule_based(clause)
    if label == "unknown":
        label = classify_clause_zero_shot(clause)
    return label

# Batch processing helper
def classify_clauses_batch(clauses: list) -> list:
    return [(clause, classify_clause_hybrid(clause)) for clause in clauses]

# Example usage
if __name__ == "__main__":
    sample_clauses = [
        "The company reported a profit of $1 million this quarter.",
        "This agreement is binding under the law.",
        "He definately made a mistake in the report."
    ]
    results = classify_clauses_batch(sample_clauses)
    for clause, label in results:
        print(f"[{label.upper()}] {clause}")
gi
