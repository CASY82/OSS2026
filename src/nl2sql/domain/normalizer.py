import re
MAPPINGS = {"보안솔루션":"security", "보안":"security", "클라우드":"cloud", "데이터 분석":"data", "데이터":"data", "컨설팅":"consulting", "크리티컬":"critical"}
def normalize_korean_enums(text: str) -> str:
    result = text
    for korean, value in MAPPINGS.items(): result = result.replace(korean, value)
    return re.sub(r"\b(Critical|High|Medium|Low)\b", lambda m: m.group(1).lower(), result)
