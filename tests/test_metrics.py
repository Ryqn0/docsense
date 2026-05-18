import pytest

from ml.evaluation.metrics import cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        vec = [1.0, 0.0, 0.0]
        # TODO: assert cosine_similarity(vec, vec) == 1.0

        assert cosine_similarity(vec, vec) == 1.0

    def test_opposite_vectors_return_minus_one(self):
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        # TODO: assert cosine_similarity(a, b) == -1.0

        assert cosine_similarity(a, b) == -1.0

    def test_orthogonal_vectors_return_zero(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        result = cosine_similarity(a, b)
        # TODO: assert result == pytest.approx(0.0)
        # why pytest.approx? floating point math isn't always exactly 0.0

        assert result == pytest.approx(0.0)

    def test_zero_vector_returns_zero(self):
        zero = [0.0, 0.0, 0.0]
        other = [1.0, 2.0, 3.0]
        # TODO: assert cosine_similarity(zero, other) == 0.0
        # This tests the edge case guard (division by zero)

        assert cosine_similarity(zero, other) == 0.0

    def test_returns_float(self):
        result = cosine_similarity([1.0, 0.0], [0.0, 1.0])
        # TODO: assert isinstance(result, float)

        assert isinstance(result, float)
