# GitHub Intelligence Agent

A natural-language AI agent for researching GitHub repositories using Google Gemini, Haystack, and GitHub's MCP server.

## Overview

GitHub Intelligence Agent lets users explore GitHub repositories through conversational queries instead of manually navigating repository pages and API documentation.

The agent discovers relevant GitHub tools, retrieves available repository information, and uses an LLM to generate structured responses. It is designed to distinguish repository metadata from README documentation and handle missing information without presenting unsupported details as facts.

## Features

- **Natural-language GitHub research:** Ask questions about repositories using plain English.
- **Dynamic tool discovery:** Uses Haystack's `SearchableToolset` to discover relevant tools from the GitHub MCP tool catalog.
- **Repository metadata retrieval:** Query available repository details such as stars, description, programming language, and last-updated timestamp.
- **Repository comparison:** Compare repositories using retrieved metadata and documentation.
- **Evidence-aware responses:** Separates GitHub metadata from information described in README files.
- **Missing-data handling:** Uses `Not retrieved` when requested information is unavailable from the retrieved results.
- **Careful search-result handling:** Distinguishes zero search matches from definitive proof that a repository does not exist.
- **Interactive chat interface:** Uses Streamlit for a conversational interface.
- **Automated tests:** Includes tests for configuration, agent construction, schema sanitization, and response-quality instructions.

> Feature availability depends on the tools exposed by the GitHub MCP server and the behavior of the configured model. Not every possible GitHub operation has necessarily been tested.

## Architecture

The application follows this workflow:

1. **User query:** The user submits a natural-language question through Streamlit.
2. **Agent initialization:** The application configures the Gemini model and GitHub MCP connection.
3. **Tool discovery:** Haystack's `SearchableToolset` helps identify relevant tools dynamically.
4. **Information retrieval:** The agent invokes the available GitHub tools to retrieve relevant information.
5. **Response generation:** Gemini generates a response based on the retrieved results and the system instructions.
6. **Response display:** Streamlit displays the answer in the chat interface.

### Architecture diagram

```text
User
 |
 v
Streamlit Chat Interface
 |
 v
Haystack Agent
 |
 +--------------------------+
 |                          |
 v                          v
SearchableToolset       Gemini Model
 |
 v
GitHub MCP Server
 |
 v
GitHub Repository Data
 |
 +----------> Agent Response
                  |
                  v
           Streamlit UI
```

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Haystack | Agent orchestration and tool discovery |
| Google Gemini | Language generation and tool-calling capabilities |
| GitHub MCP Server | Access to available GitHub tools |
| Streamlit | Interactive chat interface |
| pytest | Automated testing |

**Configured model:** `gemini-3.5-flash-lite`

The configured model and dependencies are defined in the project code and configuration files.

## Project Structure

```text
github_intelligence_agent/
├── agent.py
├── app.py
├── tests/
│   └── test_agent.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

Additional files or assets may exist in the local repository.

| File | Responsibility |
|---|---|
| `agent.py` | Configures the model, GitHub MCP connection, tool discovery, and agent instructions |
| `app.py` | Provides the Streamlit user interface |
| `tests/test_agent.py` | Contains automated tests |
| `.env.example` | Template for environment configuration |
| `.gitignore` | Excludes credentials and generated files from Git |
| `pyproject.toml` | Defines project metadata and dependencies |
| `uv.lock` | Records locked dependency versions |

## Getting Started

### Prerequisites

- Python compatible with the versions supported by the project dependencies
- Git
- A Google Gemini API key
- A GitHub Personal Access Token with the minimum permissions required by the configured GitHub MCP connection

### 1. Obtain API credentials

**Google Gemini API key**

Create an API key through [Google AI Studio](https://aistudio.google.com/).

**GitHub Personal Access Token**

Create a token through [GitHub Developer Settings](https://github.com/settings/personal-access-tokens).

Use the minimum permissions required for your intended repository access. Public-repository research should not require granting unnecessary write permissions.

Never share your keys or commit them to the repository.

### 2. Open the project directory

Open a terminal in the directory containing `pyproject.toml`.

### 3. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

Install the project and its declared dependencies:

```powershell
python -m pip install -e .
```

Install pytest if it is not already available:

```powershell
python -m pip install pytest
```

### 5. Configure environment variables

Create a local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Add your credentials using the variable names expected by the application:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GITHUB_PAT=your_github_personal_access_token
```

Keep `.env` private. Verify that the application reads these variables as expected before running it.

The Streamlit interface may also allow credentials to be entered through the sidebar, depending on the current implementation.

### 6. Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL printed in the terminal. The default Streamlit address is:

[http://localhost:8501](http://localhost:8501)

## Example Queries

Try asking questions such as:

- `Get the description, stars, and last updated date for microsoft/autogen.`
- `Compare microsoft/autogen and langchain-ai/langgraph.`
- `Summarize the main features described in the README of a repository.`
- `Retrieve the available metadata for a GitHub repository.`
- `Search for a repository and explain which requested fields could not be retrieved.`

Actual answers depend on tool availability, repository access, current GitHub data, and model behavior.

## Evidence and Response Reliability

The system instructions include safeguards intended to reduce unsupported claims:

- Retrieve repository metadata and README content as distinct evidence sources.
- Use the canonical GitHub `html_url` when it is returned by the metadata tool.
- Use `Not retrieved` when a requested field is unavailable.
- Avoid inventing missing repository details.
- When a search returns `total_count: 0`, explain that no matching repository was found by the search tool rather than claiming this definitively proves that the repository does not exist.

These are intended safeguards, not a guarantee that every generated response is factually correct. Their effectiveness should be measured through controlled evaluation.

## Testing

Run the automated test suite from the project directory:

```powershell
python -m pytest -q
```

The existing tests cover areas including:

- Model and GitHub MCP configuration.
- System-prompt requirements.
- Recursive removal of MCP schema annotations.
- Agent component construction.
- Passing system instructions and streaming callbacks.
- Rules for canonical URLs, missing metadata, and zero-result searches.

Tests that mock components validate the behavior of those components under controlled conditions. They do not, by themselves, prove that live GitHub and Gemini integrations always work correctly.

## Evaluation and Metrics

The project can be evaluated using a reproducible set of predefined repository queries and expected outcomes.

Useful metrics include:

| Metric | Calculation |
|---|---|
| Task success rate | Tasks meeting all predefined requirements divided by total tasks |
| Evidence correctness | Evaluated factual claims supported by retrieved evidence divided by all factual claims evaluated |
| Missing-data handling | Missing-data cases handled correctly divided by missing-data cases tested |
| Canonical URL correctness | Correct canonical URLs returned divided by URL cases evaluated |
| Offline test pass rate | Passed automated tests divided by total tests executed |
| Response latency | Elapsed time between query submission and completed response |

No performance or accuracy percentage is claimed in this README because reliable results must first be collected using a documented evaluation procedure.

For meaningful comparisons, use the same evaluation cases and expected outcomes across implementations, record the number of runs, and distinguish mocked tests from live API evaluations.

## Security Considerations

- Never commit `.env` or expose API credentials in source code.
- Keep `.env.example` limited to placeholder values.
- Use the minimum GitHub permissions necessary.
- Avoid logging access tokens or sensitive request information.
- Review error messages before sharing logs publicly.
- Do not assume that retrieved repository content is safe or trustworthy merely because it comes from GitHub.

## Limitations

- Results depend on the availability and correctness of GitHub MCP tools.
- Repository metadata can change over time.
- Search results may be incomplete; zero matches do not establish that a repository definitively does not exist.
- Some requested fields may be unavailable and must be reported as such.
- LLM-generated responses can still contain unsupported or incorrect claims.
- API availability, authentication, rate limits, network failures, and model errors can affect results.
- Live integration reliability and response quality require separate evaluation.

## Future Improvements

- Build a standardized evaluation dataset covering repository lookup, comparison, and missing-data scenarios.
- Measure factual correctness and task completion against predefined expected outcomes.
- Add regression tests for malformed tool responses and external-service failures.
- Improve latency and tool-call observability.
- Add structured response exports and saved research reports.
- Add clearer error handling for authentication, rate limits, and service outages.

## License

Add the appropriate license information if and when a license is selected for this repository.