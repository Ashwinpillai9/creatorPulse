import re
from statistics import mean

def build_style_profile(texts: list[str]) -> dict:
    if not texts:
        return {"avg_sentence_len": 18, "tone": "concise, neutral", "avoid": ["jargon"], "traits": []}
    sent_lens = []
    for t in texts:
        sents = re.split(r"[.!?]+\s+", t.strip())
        words = [len(s.split()) for s in sents if s]
        if words:
            sent_lens.append(mean(words))
    avg_len = round(mean(sent_lens), 2) if sent_lens else 18
    return {"avg_sentence_len": avg_len, "tone": "insightful, conversational", "avoid": ["clickbait"], "traits": ["active voice"]}
