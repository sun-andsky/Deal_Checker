import re
from transformers import pipeline

# Rule-Based
GRAMMAR_RULES = [r"\bteh\b", r"\brecieve\b", r"\bdefinately\b", r"\btheir\b\s+\bthere\b", r"\bwas\b\s+\bwere\b"]
FINANCIAL_KEYWORDS = ["profit", "revenue", "loss", "expense", "tax", "%", "$", "income", "budget"]
LEGAL_KEYWORDS = ["agreement", "contract", "liability", "clause", "penalty", "terms", "conditions"]

def classify_clause_rule_based(clause):
    for pattern in GRAMMAR_RULES:
        if re.search(pattern, clause, re.IGNORECASE):
            return "grammatical"
    for word in FINANCIAL_KEYWORDS:
        if word.lower() in clause.lower():
            return "financial"
    for word in LEGAL_KEYWORDS:
        if word.lower() in clause.lower():
            return "legal"
    return "unknown"

# Pretrained Zero-Shot
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
ZERO_SHOT_LABELS = ["financial", "legal", "grammatical", "unknown"]

def classify_clause_pretrained(clause):
    result = classifier(clause, candidate_labels=ZERO_SHOT_LABELS)
    return result['labels'][0]

# Hybrid
def classify_clause_hybrid(clause):
    label = classify_clause_rule_based(clause)
    if label == "unknown":
        label = classify_clause_pretrained(clause)
    return label

