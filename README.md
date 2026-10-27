# RepoLens AI

### GitHub Intelligence Agent + Repository RAG

RepoLens AI is a Python application that lets users investigate GitHub
repositories through natural-language questions. It combines a
**Haystack agent connected to GitHub's Model Context Protocol (MCP)
server** with a **local Retrieval-Augmented Generation (RAG) pipeline**
for asking questions about the project's own source code and
documentation.

The Streamlit interface offers two modes:

-   **GitHub Agent** --- uses Gemini, Haystack, and GitHub MCP tools to
    research GitHub repositories. Provide a repository name or URL when
    the question requires a specific remote repository.
-   **Repository RAG** --- searches indexed files in the local RepoLens
    AI project and generates answers from retrieved evidence, with
    source filenames shown in the interface.

> **Scope note:** GitHub Agent researches information available through
> the configured GitHub MCP tools. Repository RAG searches the local
> files indexed by this project; it is not automatically a
> general-purpose index of every remote GitHub repository.

------------------------------------------------------------------------

## Features

### GitHub Agent

-   Ask natural-language questions about GitHub repositories.
-   Discover relevant tools through Haystack's `SearchableToolset`.
-   Retrieve available repository metadata and documentation through
    GitHub MCP.
-   Compare repositories using information returned by the available
    tools.
-   Apply response instructions for unavailable fields and zero-result
    searches.
-   Display responses in an interactive Streamlit chat interface.

### Repository RAG

-   Read supported local source-code and documentation files.
-   Split documents into overlapping text chunks.
-   Generate vector embeddings using Google's Gemini embedding model.
-   Store embeddings and source metadata in persistent ChromaDB storage.
-   Retrieve semantically relevant chunks for a question.
-   Generate an answer using Gemini and retrieved repository evidence.
-   Show the filenames associated with the retrieved chunks.
-   Re-index the local repository from the Streamlit interface or
    command line.

### Engineering and testing

-   Automated tests for the existing GitHub agent and RAG pipeline.
-   A small retrieval-evaluation script that checks whether expected
    files appear in the top retrieved results.
-   Environment-variable configuration for API credentials.
-   A compatibility fix for MCP schema annotations that are not accepted
    by Gemini's schema validation.

Feature availability depends on the configured model, credentials,
network access, and tools exposed by the GitHub MCP server. Generated
answers can still be incorrect and should be checked against their
evidence.

------------------------------------------------------------------------

## Architecture

### 1. GitHub Agent mode

``` text
User question
     |
     v
Streamlit interface (app.py)
     |
     v
Haystack Agent (agent.py) <------> Gemini
     |
     v
SearchableToolset / MCPToolset
     |
     v
GitHub MCP server
     |
     v
Available GitHub tools and repository information
     |
     v
Answer displayed in Streamlit
```

### 2. Repository RAG mode

``` text
Local project files
       |
       v
Document loading and filtering
       |
       v
Text chunking with overlap
       |
       v
Gemini embeddings
       |
       v
Persistent ChromaDB collection
       |
User question --> Query embedding
                       |
                       v
                Similarity retrieval
                       |
                       v
             Retrieved text + sources
                       |
                       v
                  Gemini answer
                       |
                       v
              Streamlit answer + sources
```

The two modes serve different purposes: GitHub Agent calls remote GitHub
MCP tools, while Repository RAG answers questions using the locally
indexed project files.

------------------------------------------------------------------------

## Technology Stack

  -----------------------------------------------------------------------
  Technology                          Purpose
  ----------------------------------- -----------------------------------
  Python                              Application and pipeline logic

  Streamlit                           Interactive web interface

  Haystack                            Agent orchestration and tool
                                      discovery

  GitHub MCP server                   Access to the GitHub tools
                                      available to the agent

  Google Gemini                       Answer generation and tool-calling
                                      support

  `gemini-embedding-001`              Text and query embeddings for RAG

  ChromaDB                            Persistent vector storage and
                                      similarity retrieval

  pytest                              Automated tests

  uv                                  Python dependency and environment
                                      management
  -----------------------------------------------------------------------

The RAG pipeline currently configures `gemini-2.5-flash` for answer
generation. The GitHub Agent may use a separately configured model in
`agent.py`. Check the code before changing model names.

------------------------------------------------------------------------

## Project Structure

``` text
RepoLensAI/
├── agent.py
├── app.py
├── rag_pipeline.py
├── evaluate_rag.py
├── test_rag.py
├── tests/
│   └── test_agent.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

Local runtime files, such as `.env` and `.chroma_db/`, may also exist
but should not be committed.

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `agent.py`                          Configures the Haystack agent,
                                      Gemini, GitHub MCP connection, tool
                                      discovery, and agent instructions

  `app.py`                            Streamlit UI, mode selection,
                                      credential inputs, and chat flow

  `rag_pipeline.py`                   Loads files, chunks text, embeds
                                      content, indexes and retrieves
                                      chunks, and generates RAG answers

  `test_rag.py`                       Tests RAG indexing, retrieval, and
                                      answer generation

  `evaluate_rag.py`                   Checks retrieval against a small
                                      set of expected source files

  `tests/test_agent.py`               Tests the GitHub Agent's
                                      configuration and behavior

  `.env.example`                      Template for environment variables

  `.gitignore`                        Excludes credentials and generated
                                      files from version control

  `pyproject.toml`                    Project metadata and dependency
                                      declarations

  `uv.lock`                           Locked dependency versions
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Setup

### Prerequisites

-   Python 3.11 or a compatible version allowed by `pyproject.toml`
-   Git
-   A Google Gemini API key
-   A GitHub Personal Access Token for GitHub Agent mode
-   Internet access for Gemini and GitHub MCP requests

Repository RAG requires a Gemini API key. GitHub Agent mode also
requires a GitHub token according to the current application
configuration. Use the minimum GitHub permissions needed; do not grant
write access unless it is genuinely required.

### 1. Open the project directory

Open PowerShell in the directory containing `pyproject.toml`.

### 2. Install uv and project dependencies

If `uv` is not installed:

``` powershell
python -m pip install uv
```

Install the project dependencies from the project configuration and
lockfile:

``` powershell
python -m uv sync
```

### 3. Configure credentials

Create a local `.env` file from the example:

``` powershell
Copy-Item .env.example .env
```

Edit `.env` and provide the variable names used by the application:

``` dotenv
GEMINI_API_KEY=your_gemini_api_key
GITHUB_PAT=your_github_personal_access_token
```

Use real credentials only in your local `.env` file. Keep placeholder
values in `.env.example`. Never commit or share `.env`, API keys, or
access tokens. The Streamlit sidebar may also allow credentials to be
entered at runtime.

### 4. Launch the application

``` powershell
python -m uv run streamlit run app.py
```

Open the local address printed by Streamlit, usually
`http://localhost:8501`.

------------------------------------------------------------------------

## Using the Application

### GitHub Agent

1.  Select **GitHub Agent** in the sidebar.
2.  Provide the required Gemini API key and GitHub token.
3.  Ask a question that names the target repository when needed. For
    example:
    -   `Summarize the main features of https://github.com/microsoft/autogen`
    -   `Compare microsoft/autogen and langchain-ai/langgraph`
    -   `What repository metadata is available for microsoft/autogen?`

Answers depend on the GitHub MCP tools available to the agent and the
information those tools return.

### Repository RAG

1.  Select **Repository RAG** in the sidebar.
2.  Ensure the Gemini API key is available.
3.  Use **Re-index repository** after making relevant changes to local
    source files.
4.  Ask a question about the local project's implementation. For
    example:
    -   `How does this project connect to the GitHub MCP server?`
    -   `How are RAG documents indexed and stored?`
    -   `Which file implements the GitHub agent?`

The RAG pipeline searches the local repository files it indexes. If a
file is changed or added, re-index so the vector store reflects the
current contents.

------------------------------------------------------------------------

## RAG Implementation Details

The RAG pipeline is implemented in `rag_pipeline.py`.

1.  **Loading:** Reads supported local file types, including `.md`,
    `.txt`, `.py`, `.toml`, `.yaml`, `.yml`, and `.json`, while
    excluding configured directories and sensitive environment files.
2.  **Chunking:** Splits documents into overlapping chunks to preserve
    context across boundaries.
3.  **Embedding:** Uses `gemini-embedding-001` to convert chunks and
    questions into vectors.
4.  **Indexing:** Stores vectors, text, and source metadata in the
    persistent `repolens_docs` ChromaDB collection.
5.  **Retrieval:** Finds chunks similar to the question using vector
    similarity.
6.  **Generation:** Sends retrieved evidence and the question to Gemini
    to generate a response.
7.  **Sources:** Returns source filenames associated with retrieved
    chunks for display in Streamlit.

The vector database is local runtime data and can be rebuilt by
re-indexing. Do not commit the `.chroma_db/` directory.

------------------------------------------------------------------------

## Tests and Retrieval Evaluation

### Run RAG tests

``` powershell
python -m uv run python -m pytest test_rag.py -v
```

### Run the full test suite

``` powershell
python -m uv run python -m pytest -q
```

### Run retrieval evaluation

``` powershell
python -m uv run python evaluate_rag.py
```

`evaluate_rag.py` uses four predefined questions and checks whether each
expected source file appears among the top four retrieved results.

**Initial observed result: 4/4 queries passed (100% hit rate) on this
four-query evaluation set.** This is a small diagnostic benchmark, not a
claim of 100% overall accuracy, answer correctness, or production
reliability. The tests and evaluator may call Gemini and consume API
quota.

For a stronger evaluation, expand the dataset with varied questions,
expected relevant files, unanswerable questions, and difficult cases.
Measure retrieval separately from generated-answer factuality, and keep
live API tests distinct from mocked unit tests.

------------------------------------------------------------------------

## Security and Limitations

-   Keep `.env`, API keys, and personal access tokens out of Git.
-   Keep `.env.example` restricted to placeholders.
-   Use minimum necessary GitHub token permissions.
-   Do not commit `.chroma_db/`, virtual environments, caches, or
    generated build artifacts.
-   Treat retrieved repository content as untrusted input.
-   Retrieval can return irrelevant or incomplete chunks; displaying a
    source filename does not guarantee every answer claim is supported
    by that file.
-   Gemini may generate incorrect or unsupported statements even when
    relevant evidence is retrieved.
-   GitHub MCP tool availability, authentication, rate limits, network
    connectivity, and model behavior can affect results.
-   The current four-question retrieval evaluation is too small to
    establish broad reliability.

------------------------------------------------------------------------

## Future Improvements

-   Expand the retrieval evaluation dataset and report more informative
    metrics such as Recall@k and MRR.
-   Evaluate answer faithfulness and whether citations support
    individual claims.
-   Display source snippets and line-level references where available.
-   Add tests for empty retrieval results, malformed responses, and
    external-service failures.
-   Improve error handling for authentication, rate limits, and API
    outages.
-   Add a clear index-refresh strategy for larger repositories.
-   Add support for selecting a local repository directory or indexing a
    remote repository intentionally.
-   Improve observability for retrieval latency, model latency, and
    token/API usage.

------------------------------------------------------------------------

## License

Add a license before distributing the project if you intend to publish
it for reuse. Until a license is selected and included, do not imply
that the project has a particular open-source license.
