# AGENTS.md — gpt-mcp-interpreter

## Project Management

- Use `uv` for project management and dependency management.
- Do NOT use `pip` or `pip install` directly.

## Adding Dependencies

- Use `uv add <package>` to add new dependencies.
  ```bash
  uv add <package-name>
  ```

## Running the Application

- Use `uv run` to execute the main script.
  ```bash
  uv run main.py
  ```
- For interactive mode:
  ```bash
  uv run main.py --interactive
  ```

## Key Notes

- Always run commands from the `/gpt-mcp-interpreter` directory.
- This project uses Azure OpenAI Responses API with MCP (Model Context Protocol) to execute Python code via Dynamic Sessions.
- The Responses API handles MCP tool discovery and execution server-side — no manual tool calling loop is needed.
- Environment variables are loaded from `.env` file. Copy `.env.example` to `.env` and set required values before running.
- Required environment variables:
  - `MCP_ENDPOINT` — MCP session pool endpoint (from dynamic-sessions-mcp hands-on)
  - `MCP_API_KEY` — MCP session pool API key (from dynamic-sessions-mcp hands-on)
  - `AZURE_OPENAI_ENDPOINT` — Azure OpenAI endpoint URL
  - `AZURE_OPENAI_API_KEY` — Azure OpenAI API key
  - `AZURE_OPENAI_MODEL` — Model deployment name (default: `gpt-4o`)
