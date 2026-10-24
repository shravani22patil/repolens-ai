import agent
from unittest.mock import patch


def test_model_id_is_configured():
    assert agent.MODEL_ID == "gemini-3.5-flash-lite"


def test_github_mcp_url_is_configured():
    assert agent.GITHUB_MCP_URL == "https://api.githubcopilot.com/mcp/"


def test_system_prompt_has_source_accuracy_rules():
    assert "Not retrieved" in agent.SYSTEM_PROMPT
    assert "Never invent" in agent.SYSTEM_PROMPT
    assert "README" in agent.SYSTEM_PROMPT


def test_mcp_schema_annotations_are_removed_recursively():
    schema = {
        "type": "object",
        "x-mcp-header": "secret-header",
        "properties": {
            "query": {
                "type": "string",
                "x-mcp-header": "nested-header",
            }
        },
        "items": [{"x-mcp-header": "list-header", "type": "string"}],
    }

    cleaned = agent._remove_mcp_schema_annotations(schema)

    assert "x-mcp-header" not in cleaned
    assert "x-mcp-header" not in cleaned["properties"]["query"]
    assert "x-mcp-header" not in cleaned["items"][0]
    assert schema["x-mcp-header"] == "secret-header"


def test_build_agent_wires_components_without_network_calls():
    with patch.object(agent, "MCPToolset") as mcp, \
         patch.object(agent, "SearchableToolset") as searchable, \
         patch.object(agent, "GoogleGenAIChatGenerator") as generator, \
         patch.object(agent, "Agent") as agent_class:

        result = agent.build_agent(
            github_pat="test-github-token",
            gemini_api_key="test-gemini-key",
        )

        mcp.assert_called_once()
        searchable.assert_called_once_with(catalog=mcp.return_value)
        generator.assert_called_once_with(model=agent.MODEL_ID)
        agent_class.assert_called_once()
        assert result == agent_class.return_value


def test_build_agent_passes_system_prompt_and_streaming_callback():
    callback = lambda chunk: None

    with patch.object(agent, "MCPToolset"), \
         patch.object(agent, "SearchableToolset"), \
         patch.object(agent, "GoogleGenAIChatGenerator"), \
         patch.object(agent, "Agent") as agent_class:

        agent.build_agent(
            github_pat="test-github-token",
            gemini_api_key="test-gemini-key",
            streaming_callback=callback,
        )

        kwargs = agent_class.call_args.kwargs
        assert kwargs["system_prompt"] == agent.SYSTEM_PROMPT
        assert kwargs["streaming_callback"] is callback



def test_system_prompt_requires_canonical_html_url():
    assert "html_url" in agent.SYSTEM_PROMPT
    assert "Not retrieved" in agent.SYSTEM_PROMPT


def test_system_prompt_handles_zero_search_results_carefully():
    assert "total_count: 0" in agent.SYSTEM_PROMPT
    assert "No matching repository was found by the search tool." in agent.SYSTEM_PROMPT


def test_system_prompt_prohibits_invented_metadata():
    assert "Never invent missing metadata" in agent.SYSTEM_PROMPT


def test_system_prompt_separates_metadata_from_readme_evidence():
    prompt = agent.SYSTEM_PROMPT.lower()
    assert "metadata" in prompt
    assert "readme" in prompt
