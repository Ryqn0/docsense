import os
import tempfile

from ml.retrieval.chunker import chunk_text, count_tokens, extract_text_from_txt


class TestCountTokens:
    def test_empty_string_returns_zero(self):
        assert count_tokens("") == 0

    def test_known_text_returns_positive_count(self):
        count = count_tokens("hello world")
        assert count > 0
        assert isinstance(count, int)

    def test_longer_text_has_more_tokens(self):
        short = count_tokens("hi")
        long = count_tokens("This is a much longer sentence with many words")
        assert long > short


class TestChunkText:
    def test_short_text_produces_one_chunk(self):
        # Text with fewer tokens than chunk_size -> single chunk
        result = chunk_text("short text", chunk_size=512, chunk_overlap=64)
        assert len(result) == 1

    def test_chunk_has_correct_fields(self):
        result = chunk_text("some text here", chunk_size=512, chunk_overlap=64)
        chunk = result[0]
        # TODO: assert chunk.content is a str
        # TODO: assert chunk.chunk_index == 0
        # TODO: assert chunk.token_count > 0
        # TODO: assert "char_offset" in chunk.metadata

        assert isinstance(chunk.content, str)
        assert chunk.chunk_index == 0
        assert chunk.token_count > 0
        assert "char_offset" in chunk.metadata.keys()

    def test_long_text_produces_multiple_chunks(self):
        # Create text that is definitely longer than chunk_size=10 tokens
        long_text = " ".join(["word"] * 100)  # 100 words = 100 tokens
        result = chunk_text(long_text, chunk_size=10, chunk_overlap=2)
        # TODO: assert len(result) > 1

        assert len(result) > 1

    def test_chunks_are_ordered(self):
        long_text = " ".join(["word"] * 100)
        result = chunk_text(long_text, chunk_size=10, chunk_overlap=2)
        indexes = [c.chunk_index for c in result]
        # TODO: assert indexes == list(range(len(result))

        assert indexes == list(range(len(result)))

    def test_content_is_not_empty(self):
        result = chunk_text("hello world this is a test", chunk_size=512, chunk_overlap=64)
        for chunk in result:
            assert chunk.content.strip() != ""


class TestExtractTextFromTxt:
    def test_reads_content_correctly(self):
        expected = "Hello, this is test content.\nSecond line."
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(expected)
            tmp_path = f.name

        try:
            result = extract_text_from_txt(tmp_path)
            # TODO: asseert result == expected

            assert result == expected

        finally:
            os.unlink(tmp_path)  # always clean up temp files

    def test_returns_string(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("test")
            tmp_path = f.name
        try:
            result = extract_text_from_txt(tmp_path)
            # TODO: assert isinstance(result, str)

            assert isinstance(result, str)

        finally:
            os.unlink(tmp_path)
