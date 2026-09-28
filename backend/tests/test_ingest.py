from pathlib import Path

import pytest

from app.ingest import chunk_pages, chunk_text, embed_texts, extract_pages
from tests.fakes import FakeOpenAI

SAMPLE_PDF = Path(__file__).resolve().parents[2] / "eval" / "sample_docs" / "doi_absence_and_leave_handbook.pdf"


def test_chunk_text_short_text_is_one_chunk():
    assert chunk_text("one two three", size_words=10, overlap_words=2) == ["one two three"]


def test_chunk_text_windows_overlap():
    words = [f"w{i}" for i in range(25)]
    chunks = chunk_text(" ".join(words), size_words=10, overlap_words=2)
    assert [len(c.split()) for c in chunks] == [10, 10, 9]
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


def test_chunk_text_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("a b c", size_words=5, overlap_words=5)


def test_chunk_text_empty():
    assert chunk_text("   ", size_words=5, overlap_words=1) == []


def test_chunk_pages_never_crosses_pages():
    pages = [(1, "page one " * 700), (3, "page three")]
    chunks = chunk_pages(pages)
    page_one = [c for c in chunks if c.page_number == 1]
    page_three = [c for c in chunks if c.page_number == 3]
    assert len(page_one) >= 2
    assert len(page_three) == 1
    assert all("three" not in c.text for c in page_one)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_extract_pages_from_sample_pdf():
    pages = extract_pages(SAMPLE_PDF.read_bytes())
    numbers = [n for n, _ in pages]
    assert numbers[0] == 1
    assert numbers == sorted(numbers)
    assert "Absence and Leave Handbook" in pages[0][1]


async def test_embed_texts_batches_and_keeps_order():
    client = FakeOpenAI()
    texts = [f"text {i}" for i in range(250)]
    vectors = await embed_texts(client, texts)
    assert len(vectors) == 250
    assert [len(call) for call in client.embeddings.calls] == [100, 100, 50]
