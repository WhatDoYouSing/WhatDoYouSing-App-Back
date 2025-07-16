from konlpy.tag import Okt
import spacy, re

_okt = Okt()
_en  = spacy.load("en_core_web_sm")

def _normalize(word: str) -> str:
    # 특수문자 제거 + 소문자
    return re.sub(r"[^A-Za-z가-힣0-9]", "", word).lower()

def extract_nouns(text: str) -> list[str]:
    ko = _okt.nouns(text)
    en = [tok.lemma_ for tok in _en(text) if tok.pos_ == "NOUN"]
    words = [_normalize(w) for w in (*ko, *en)]
    return [w for w in words if w]  # 빈 문자열 제거