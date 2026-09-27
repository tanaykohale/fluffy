import pytest

from src.services.rag import RagIndex, chunk_text, cosine, read_file


def test_chunk_text_overlaps_and_covers_everything():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, size=200, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    assert "word0" in chunks[0] and "word499" in chunks[-1]
    # overlap: end of chunk n reappears at start of chunk n+1
    assert chunks[0].split()[-1] in chunks[1]


def test_chunk_text_edge_cases():
    assert chunk_text("   ") == []
    assert chunk_text("short") == ["short"]
    with pytest.raises(ValueError):
        chunk_text("x", size=10, overlap=10)


def test_cosine():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine([0, 0], [1, 1]) == 0.0


def test_search_ranks_relevant_file_first(tmp_path, embed):
    (tmp_path / "pets.txt").write_text("My cat and my dog sleep all day. The cat is grey.")
    (tmp_path / "bills.md").write_text("Invoice 42 is due. Pay the invoice by Friday.")
    idx = RagIndex(embed)
    idx.add_file(str(tmp_path / "pets.txt"))
    idx.add_file(str(tmp_path / "bills.md"))
    assert idx.sources() == ["bills.md", "pets.txt"]
    hits = idx.search("when is the invoice due?", k=1)
    assert hits[0]["source"] == "bills.md"
    assert idx.search("tell me about the cat", k=1)[0]["source"] == "pets.txt"


def test_readding_file_replaces_old_chunks(tmp_path, embed):
    f = tmp_path / "a.txt"
    f.write_text("cat")
    idx = RagIndex(embed)
    idx.add_file(str(f))
    idx.add_file(str(f))
    assert len(idx.chunks) == 1


def test_persistence_roundtrip(tmp_path, embed):
    path = str(tmp_path / "idx" / "rag.json")
    idx = RagIndex(embed, path=path)
    idx.add_text("python is a language", source="notes")
    idx.save()
    again = RagIndex(embed, path=path)
    assert again.sources() == ["notes"]
    assert again.search("python")[0]["text"] == "python is a language"


def test_build_prompt_includes_sources():
    assert RagIndex.build_prompt("q", []) is None
    p = RagIndex.build_prompt("q", [{"source": "a.md", "text": "hello", "score": 1}])
    assert "[a.md]" in p and "hello" in p


def test_empty_index_search():
    assert RagIndex(lambda t: [[1]] * len(t)).search("x") == []


def test_unsupported_file(tmp_path):
    f = tmp_path / "img.png"
    f.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError):
        read_file(str(f))
