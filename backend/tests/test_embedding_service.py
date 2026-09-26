from types import SimpleNamespace

import pytest
from openai import APIConnectionError, BadRequestError

from app.services.embeddings import (
    EMPTY_RESPONSE_ATTEMPTS,
    EmbeddingUnavailableError,
    OpenAICompatibleEmbeddingService,
)


def _service(create, dimensions=3, batch_size=2, concurrency=1):
    service = OpenAICompatibleEmbeddingService.__new__(OpenAICompatibleEmbeddingService)
    service.model = "test-model"
    service.dimensions = dimensions
    service.batch_size = batch_size
    service.concurrency = concurrency
    service.client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
    return service


def _response(vectors, reverse=False):
    data = [SimpleNamespace(index=i, embedding=v) for i, v in enumerate(vectors)]
    return SimpleNamespace(data=data[::-1] if reverse else data, model_extra={})


def test_batches_and_preserves_input_order():
    calls = []

    def create(model, input, encoding_format):
        calls.append(list(input))
        # Provider returns items out of order; the service must sort by index.
        return _response([[float(len(t)), 0.0, 0.0] for t in input], reverse=True)

    vectors = _service(create).embed_texts(["a", "bb", "ccc", "dddd", "eeeee"])

    assert calls == [["a", "bb"], ["ccc", "dddd"], ["eeeee"]]
    assert [v[0] for v in vectors] == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_retries_once_on_incomplete_response():
    responses = iter([_response([]), _response([[1.0, 2.0, 3.0]])])
    service = _service(lambda **_kw: next(responses))
    assert service.embed_text("q") == [1.0, 2.0, 3.0]


def test_raises_when_always_incomplete():
    service = _service(lambda **_kw: _response([]))
    with pytest.raises(EmbeddingUnavailableError):
        service.embed_text("q")
    assert EMPTY_RESPONSE_ATTEMPTS == 2


def test_dimension_mismatch_is_a_clear_error():
    service = _service(lambda **_kw: _response([[1.0, 2.0]]), dimensions=3)
    with pytest.raises(EmbeddingUnavailableError, match="EMBEDDING_DIMENSIONS=3"):
        service.embed_text("q")


def test_api_errors_become_unavailable():
    def create(**_kw):
        raise APIConnectionError(request=SimpleNamespace(method="POST", url="x"))

    with pytest.raises(EmbeddingUnavailableError):
        _service(create).embed_text("q")


def _too_long(tokens, limit=512):
    err = BadRequestError.__new__(BadRequestError)
    Exception.__init__(
        err,
        f"Error code: 400 - Embedding input has {tokens} tokens, "
        f"exceeding the model maximum of {limit}.",
    )
    return err


def test_overlong_input_is_shortened_and_batch_still_succeeds():
    # Pretend 1 char = 1 token and the model max is 512.
    calls = []

    def create(model, input, encoding_format):
        calls.append([len(t) for t in input])
        longest = max(len(t) for t in input)
        if longest > 512:
            raise _too_long(longest)
        return _response([[float(len(t)), 0.0, 0.0] for t in input])

    texts = ["short", "x" * 1000, "also short"]
    vectors = _service(create, batch_size=32).embed_texts(texts)

    # Batch rejected -> per-item; the long one shortened to fit (1000*512/1000*0.9).
    assert calls[0] == [5, 1000, 10]
    assert [v[0] for v in vectors] == [5.0, 460.0, 10.0]


def test_other_bad_requests_are_not_retried_as_length_errors():
    def create(**_kw):
        err = BadRequestError.__new__(BadRequestError)
        Exception.__init__(err, "Error code: 400 - invalid model")
        raise err

    with pytest.raises(EmbeddingUnavailableError, match="invalid model"):
        _service(create).embed_text("q")


def test_concurrent_batches_keep_input_order():
    import random
    import time

    def create(model, input, encoding_format):
        time.sleep(random.uniform(0, 0.02))  # finish out of order
        return _response([[float(t), 0.0, 0.0] for t in map(len, input)])

    texts = ["x" * n for n in range(1, 41)]
    vectors = _service(create, batch_size=3, concurrency=4).embed_texts(texts)

    assert [v[0] for v in vectors] == [float(n) for n in range(1, 41)]
