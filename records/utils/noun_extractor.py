# records/utils/noun_extractor.py
import os, re
from bareunpy import Tagger
import nlpcloud
#from django.conf import settings

#NLP_KEY = getattr(settings, "NLP_API_KEY", None)
NLP_KEY=os.environ["NLP_API_KEY"]
client = nlpcloud.Client("en_core_web_lg", NLP_KEY)

_BAREUN = Tagger(
    os.environ["BAREUN_API_KEY"],                 
    os.getenv("BAREUN_API_HOST", "api.bareun.ai"),
    int(os.getenv("BAREUN_API_PORT", "443")),
)

_ALLOWED_KO_POS = {"NNG", "NNP", "NP"}
_ALLOWED_EN_POS = {"NN", "NNS", "NNP", "NNPS"} 

def _normalize(s: str) -> str:
    return re.sub(r"[^A-Za-z가-힣0-9]", "", s).lower()

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

def _en_nouns(text: str) -> list[str]:
    english_text = " ".join(re.findall(r"[A-Za-z]+", text))
    if not english_text.strip():
        return []

    try:
        result = client.dependencies(english_text)
    except Exception as e:
        print(f"[NLPCloud Error] {e}")
        return []

    words = []
    tokens = result.get("tokens") or result.get("words", [])

    for token in tokens:
        pos = token.get("tag") or token.get("pos")
        word = token.get("lemma") or token.get("text")

        if pos in _ALLOWED_EN_POS and word:
            words.append(_normalize(word))

    return words

def extract_nouns(text: str) -> list[str]:
    ko = _ko_nouns(text)
    en = _en_nouns(text)
    return [*ko, *en]