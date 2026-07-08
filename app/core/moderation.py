import re

# 기본적인 욕설/비속어 키워드 목록. 완전한 목록이 아니며, 운영 단계에서는 외부 형태소
# 분석기(예: soynlp, py-hanspell) 또는 상용 콘텐츠 모더레이션 API로 교체/보강하는 것을 권장한다.
BANNED_KEYWORDS: set[str] = {
    "씨발", "시발", "씨팔", "ㅅㅂ", "ㅆㅂ",
    "개새끼", "개새기", "새끼", "개새",
    "병신", "ㅂㅅ",
    "지랄", "ㅈㄹ",
    "좆", "존나", "ㅈㄴ",
    "미친놈", "미친년",
    "걸레같은",
    "fuck", "shit", "bitch", "asshole",
}

_NON_ALNUM_RE = re.compile(r"[^0-9a-zA-Z가-힣]")


def _normalize(text: str) -> str:
    """공백/특수문자를 제거해 간단한 우회 표기를 어느 정도 방어한다 (예: '씨 발')."""
    return _NON_ALNUM_RE.sub("", text.lower())


def find_profanity(text: str) -> list[str]:
    normalized = _normalize(text)
    return [word for word in BANNED_KEYWORDS if word.lower() in normalized]


def contains_profanity(text: str) -> bool:
    return len(find_profanity(text)) > 0
