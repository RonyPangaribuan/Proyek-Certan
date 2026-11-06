"""Offline validation and model-cache tests; real model tests are separate."""

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from proyek_certan.knowledge import embeddings
from proyek_certan.knowledge.embeddings import EmbeddingModel


@pytest.mark.parametrize("texts", ["", " \n ", [], ["valid", ""], [" "]])
def test_empty_input_fails_before_loading_model(texts, monkeypatch):
    def unexpected_load(*args):
        pytest.fail("invalid input must not load/download a model")

    monkeypatch.setattr(embeddings, "_load_model", unexpected_load)
    with pytest.raises(ValueError):
        EmbeddingModel().encode(texts)


@pytest.mark.parametrize("texts", [None, 17, b"wifi", ["wifi", None]])
def test_non_text_input_fails(texts):
    with pytest.raises(TypeError):
        EmbeddingModel().encode(texts)


def test_matrix_shape_normalization_options_and_cached_model(monkeypatch, tmp_path):
    loads = []
    calls = []

    class FakeModel:
        def get_embedding_dimension(self):
            return 3

        def encode(self, texts, **kwargs):
            calls.append((texts, kwargs))
            return np.tile([1.0, 0.0, 0.0], (len(texts), 1))

    def factory(name, **kwargs):
        loads.append((name, kwargs))
        return FakeModel()

    embeddings._load_model.cache_clear()
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=factory))
    try:
        model = EmbeddingModel(cache_folder=tmp_path)
        matrix = model.encode(["WiFi terputus", "Router mati", "Kabel LAN rusak"])
        single = EmbeddingModel(cache_folder=tmp_path).encode(" WiFi ")
        assert matrix.shape == (3, 3)
        assert single.shape == (1, 3)
        assert matrix.dtype == np.float32
        assert np.linalg.norm(matrix, axis=1) == pytest.approx([1, 1, 1])
        assert len(loads) == 1
        assert calls[-1][0] == ["WiFi"]
        assert all(call[1]["normalize_embeddings"] is True for call in calls)
    finally:
        embeddings._load_model.cache_clear()
