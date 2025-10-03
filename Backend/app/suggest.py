# app/suggest.py
from functools import lru_cache
import language_tool_python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_tool = language_tool_python.LanguageTool("en-US")

@lru_cache(maxsize=1)
def load_t5():
    tokenizer = AutoTokenizer.from_pretrained("t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")
    return tokenizer, model

def correct_grammar(text: str) -> str:
    matches = _tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)
    return corrected

def paraphrase_t5(text: str, n=2):
    tokenizer, model = load_t5()
    input_text = "paraphrase: " + text
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True)
    outs = model.generate(**inputs, num_return_sequences=n, num_beams=4, max_length=256)
    return [tokenizer.decode(o, skip_special_tokens=True) for o in outs]

def generate_suggestions(clause_text: str, error_type: str):
    suggestions = []
    if error_type.lower() == "grammatical":
        corrected = correct_grammar(clause_text)
        if corrected and corrected != clause_text:
            suggestions.append({"suggestion": corrected, "source": "grammar", "confidence": None})
    else:
        paraphrases = paraphrase_t5(clause_text, n=2)
        for p in paraphrases:
            if p and p != clause_text:
                suggestions.append({"suggestion": p, "source": "t5", "confidence": None})
    # simple rule fallback example
    if " day." in clause_text and " days" not in clause_text:
        suggestions.append({"suggestion": clause_text.replace(" day", " days"), "source": "rule", "confidence": None})
    return suggestions
