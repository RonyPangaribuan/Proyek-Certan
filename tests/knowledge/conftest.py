"""Synthetic chunk fixtures and an offline encoder for storage logic tests."""

import json
from pathlib import Path

import numpy as np
import pytest

from proyek_certan.knowledge.embeddings import DEFAULT_MODEL_NAME


SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_knowledge_chunks.json"


@pytest.fixture
def chunks():
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


class StubEmbedder:
    """Known vectors test cosine arithmetic, not real model relevance."""

    model_name = DEFAULT_MODEL_NAME

    def __init__(self):
        self.calls = 0

    def encode(self, texts):
        self.calls += 1
        batch = [texts] if isinstance(texts, str) else list(texts)
        vectors = []
        for text in batch:
            if "router" in text.lower():
                vectors.append([0.0, 1.0, 0.0])
            elif "lan" in text.lower():
                vectors.append([-1.0, 0.0, 0.0])
            else:
                vectors.append([1.0, 0.0, 0.0])
        return np.asarray(vectors, dtype=np.float32)


@pytest.fixture
def embedder():
    return StubEmbedder()
