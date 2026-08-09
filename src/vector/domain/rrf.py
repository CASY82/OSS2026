from collections import defaultdict

RRF_K = 60

def fuse(vector_ranked: list[str], keyword_ranked: list[str], top_k: int) -> list[tuple[str, float]]:
    score: dict[str, float] = defaultdict(float)
    for rank, chunk_id in enumerate(vector_ranked, 1):
        score[chunk_id] += 1.0 / (RRF_K + rank)
    for rank, chunk_id in enumerate(keyword_ranked, 1):
        score[chunk_id] += 1.0 / (RRF_K + rank)
    return sorted(score.items(), key=lambda item: (-item[1], item[0]))[:max(0, top_k)]
