# records/utils/noun_extractor.py
import os, re
import spacy

# ─ 영어 (원하면 제거 가능) ─
try:
    _en = spacy.load("en_core_web_sm")
except Exception:
    _en = None
SEASON_WORDS = {"spring", "summer", "autumn", "fall", "winter"}

def _normalize(s: str) -> str:
    return re.sub(r"[^A-Za-z가-힣0-9]", "", s).lower()

# ─ 바른(클라우드) ─
from bareunpy import Tagger
_BAREUN = Tagger(
    os.environ["BAREUN_API_KEY"],                 # 반드시 백엔드 환경변수로 주입
    os.getenv("BAREUN_API_HOST", "api.bareun.ai"),
    int(os.getenv("BAREUN_API_PORT", "443")),
)

_ALLOWED_KO_POS = {"NNG", "NNP", "NP"}

def _ko_nouns(text: str) -> list[str]:
    """
    바른의 POS 결과에서 품사 태그를 읽어
    NNG/NNP/NP만 남기고 정규화하여 반환.
    """
    tuples = []
    pos = _BAREUN.pos(text)

    for tok in pos:
        if isinstance(tok, (list, tuple)) and len(tok) >= 2:
            word, tag = tok[0], str(tok[1])
        elif isinstance(tok, dict):
            word = tok.get("lemma") or tok.get("text") or tok.get("morph") or tok.get("word")
            tag  = str(tok.get("pos") or tok.get("tag") or "")
        else:
            continue

        if not word or not tag:
            continue

        main_tag = tag.split("+", 1)[0].split("-", 1)[0]
        if main_tag in _ALLOWED_KO_POS:
            tuples.append(word)

    return [_normalize(w) for w in tuples if w]

def _en_nouns(text: str) -> list[str]:
    if not _en:
        return []
    en = [
        tok.lemma_.lower()
        for tok in _en(text)
        if tok.pos_ in {"NOUN", "PROPN"} or tok.text.lower() in SEASON_WORDS
    ]
    return [_normalize(w) for w in en if w]

def extract_nouns(text: str) -> list[str]:
    ko = _ko_nouns(text)
    en = _en_nouns(text)
    return [*ko, *en]

# 이전 오픈소스 사용 버전
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