from rag_pipeline import index_repository, retrieve, answer_question, collection


def test_rag_index_contains_documents():
    index_repository()
    assert collection.count() > 0


def test_retrieval_finds_mcp_implementation():
    results = retrieve(
        "How does the project connect to the GitHub MCP server?"
    )

    assert results, "Retrieval returned no results."

    sources = [item["source"] for item in results]
    assert any("agent.py" in source for source in sources), (
        f"Expected agent.py in retrieved sources, got: {sources}"
    )


def test_answer_includes_primary_implementation():
    result = answer_question(
        "How does this project connect to the GitHub MCP server?"
    )

    assert result["answer"]
    assert result["sources"]
    assert any("agent.py" in source for source in result["sources"])


def test_answer_mentions_mcp_connection():
    result = answer_question(
        "How does this project connect to the GitHub MCP server?"
    )

    answer = result["answer"].lower()
    assert "mcp" in answer
    assert "agent.py" in answer