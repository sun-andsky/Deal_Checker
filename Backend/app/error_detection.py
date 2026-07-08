# app/error_detection.py

# -------- Error Detection --------
def detect_grammatical_errors(clause):
    import language_tool_python
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(clause)
    errors = [{"error": m.message, "offset": m.offset, "length": m.errorLength} for m in matches]
    return errors

def detect_financial_errors(clause):
    import re
    errors = []
    if re.search(r"\b\d+(\.\d+)?\s*(USD|INR|€|GBP)?\b", clause) is None:
        errors.append({"error": "No financial value found", "clause": clause})
    return errors

def detect_legal_errors(clause):
    errors = []
    required_phrases = ["hereinafter", "shall", "agreement", "party", "witnesseth"]
    if not any(p.lower() in clause.lower() for p in required_phrases):
        errors.append({"error": "Possible missing legal keywords", "clause": clause})
    return errors
