"""
GitHub Intelligence Agent
=========================
Research anything on GitHub through natural language.
Powered by Gemini 3 Flash + GitHub MCP Server via Haystack.
"""

import os
from textwrap import dedent

from haystack.components.agents import Agent
from haystack.tools import SearchableToolset
from haystack.utils import Secret
from haystack_integrations.components.generators.google_genai import GoogleGenAIChatGenerator
from haystack_integrations.tools.mcp import MCPToolset, StreamableHttpServerInfo


# Compatibility fix: remove MCP-specific schema annotations before Gemini validation.
from haystack_integrations.components.generators.google_genai.chat import utils as google_genai_utils

_original_sanitize_tool_schema = google_genai_utils._sanitize_tool_schema


def _remove_mcp_schema_annotations(value):
    if isinstance(value, dict):
        return {
            key: _remove_mcp_schema_annotations(item)
            for key, item in value.items()
            if key != "x-mcp-header"
        }
    if isinstance(value, list):
        return [_remove_mcp_schema_annotations(item) for item in value]
    return value


def _sanitize_tool_schema_compat(schema, *args, **kwargs):
    cleaned_schema = _remove_mcp_schema_annotations(schema)
    return _original_sanitize_tool_schema(cleaned_schema, *args, **kwargs)


google_genai_utils._sanitize_tool_schema = _sanitize_tool_schema_compat


GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"
MODEL_ID = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = dedent("""
    You are a GitHub Intelligence Agent with access to GitHub's full API through MCP tools.

    You can help with:
    - Searching and discovering repositories, users, code, issues, and pull requests
    - Profiling GitHub users and their most notable projects
    - Summarising open issues, pull requests, and releases for any repository
    - Analysing trends across GitHub (top repos, active projects, popular topics)
    - Exploring codebases and understanding project structure and activity

    When given a task:
    1. Use search_tools to dynamically find the right tools for the job
    2. Call the appropriate tools with precise, well-formed parameters
    3. Synthesise the results into a clear, well-structured response

    If a tool call fails, analyse the cause, adapt your approach, and retry with
    a different strategy. Persist until the task is complete.

    Do not narrate your process. Output only the final answer.


    SOURCE ACCURACY RULES:
    1. Use GitHub MCP tool results as the primary source for repository facts.
    2. Include a direct GitHub URL for every repository discussed.
    3. For repository metadata, report only fields returned by GitHub tools.
    4. If a field is unavailable, explicitly say "Not retrieved".
    5. Distinguish formal API metadata from statements in the README.
       For example, archived=true is different from a README describing
       a project as archived, deprecated, or transitioning.
    6. If sources conflict, explain the conflict and identify each source.
    7. Never invent star counts, dates, branches, languages, or project status.
    8. Keep answers concise, structured, and useful to developers.
    9. For every repository, retrieve metadata and README separately.
       Base metadata fields only on repository metadata returned by a tool.
       Base project status and feature claims only on README content returned
       by a tool. Never use search-result snippets as proof that a tool call
       retrieved a field.
    10. If exact star counts are returned, report them as retrieved values,
        not guaranteed live counts. If not retrieved, write "Not retrieved".
    11. For each repository, include a short evidence note identifying
        which tool supplied the metadata and which supplied the README.
    12. - For a repository URL, use the exact canonical HTML URL returned by GitHub repository metadata (html_url.
       Never output only the owner/repository slug as a URL.
       If the tool does not return html_url, write "Not retrieved" rather than inventing or reconstructing the field.
    13. If a repository search returns total_count: 0, say "No matching repository was found by the search tool."
      Do not claim this proves the repository definitively does not exist.
    14. Never invent missing metadata. Use "Not retrieved" whenever a requested field is unavailable in the tool results.
    15. For canonical GitHub HTML URLs, use the exact html_url returned by GitHub metadata. If unavailable, write "Not retrieved".
""")


def build_agent(github_pat: str, gemini_api_key: str, streaming_callback=None) -> Agent:
    """Build and return a GitHub Intelligence Agent.

    Args:
        github_pat: GitHub Personal Access Token (read-only permissions are enough)
        gemini_api_key: Google AI Gemini API key
        streaming_callback: Optional callable for streaming chunks to the UI
    """
    os.environ["GITHUB_PAT"] = github_pat
    os.environ["GOOGLE_API_KEY"] = gemini_api_key

    mcp_server_info = StreamableHttpServerInfo(
        url=GITHUB_MCP_URL,
        token=Secret.from_env_var("GITHUB_PAT"),
    )

    toolset = MCPToolset(server_info=mcp_server_info)
    searchable_toolset = SearchableToolset(catalog=toolset)

    generator = GoogleGenAIChatGenerator(model=MODEL_ID)

    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        chat_generator=generator,
        tools=searchable_toolset,
        streaming_callback=streaming_callback,
    )

    return agent
