from rag_pipeline import index_repository, retrieve


TEST_CASES = [
    {
        "question": "How does the project connect to the GitHub MCP server?",
        "expected_source": "agent.py",
    },
    {
        "question": "How are RAG documents indexed and stored?",
        "expected_source": "rag_pipeline.py",
    },
    {
        "question": "What tests verify the GitHub agent?",
        "expected_source": "tests/test_agent.py",
    },
    {
        "question": "How do I install and run this project?",
        "expected_source": "README.md",
    },
]


def evaluate_retrieval():
    index_repository()

    passed = 0

    for case in TEST_CASES:
        results = retrieve(case["question"], top_k=4)
        sources = [item["source"] for item in results]

        success = any(
            case["expected_source"] in source
            for source in sources
        )

        if success:
            passed += 1

        print(f"\nQuestion: {case['question']}")
        print(f"Expected file: {case['expected_source']}")
        print(f"Retrieved files: {sources}")
        print(f"Result: {'PASS' if success else 'FAIL'}")

    total = len(TEST_CASES)
    print(f"\nRetrieval Hit Rate: {passed}/{total} ({passed / total:.0%})")


if __name__ == "__main__":
    evaluate_retrieval()