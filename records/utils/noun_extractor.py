# records/utils/noun_extractor.py
import os, re
from bareunpy import Tagger

def _normalize(s: str) -> str:
    return re.sub(r"[^A-Za-z가-힣0-9]", "", s).lower()

_BAREUN = Tagger(
    os.environ["BAREUN_API_KEY"],                 # 반드시 백엔드 환경변수로 주입
    os.getenv("BAREUN_API_HOST", "api.bareun.ai"),
    int(os.getenv("BAREUN_API_PORT", "443")),
)

_ALLOWED_KO_POS = {"NNG", "NNP", "NP"}

def _ko_nouns(text: str) -> list[str]:
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

def extract_nouns(text: str) -> list[str]:
    ko = _ko_nouns(text)
    return [*ko]