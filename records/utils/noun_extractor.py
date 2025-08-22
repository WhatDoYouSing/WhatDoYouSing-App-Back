# records/utils/noun_extractor.py
'''
from konlpy.tag import Okt
import spacy, re

_model = Okt()                      
_en   = spacy.load("en_core_web_sm")

def _normalize(word: str) -> str:
    return re.sub(r"[^A-Za-z가-힣0-9]", "", word).lower()

def extract_nouns(text: str) -> list[str]:
    ko = _model.nouns(text)          
    en = [tok.lemma_ for tok in _en(text) if tok.pos_ == "NOUN"]
    words = [_normalize(w) for w in (*ko, *en)]
    return [w for w in words if w]
'''