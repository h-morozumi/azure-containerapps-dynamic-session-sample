# AGENTS.md — gpt-code-interpreter

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

- Always run commands from the `/gpt-code-interpreter` directory.
- This project uses Azure Container Apps Dynamic Sessions as a code execution tool via Azure OpenAI Function Calling.
- Environment variables are loaded from `.env` file. Copy `.env.example` to `.env` and set required values before running.
- Required environment variables:
  - `POOL_ENDPOINT` — Session pool management endpoint
  - `AZURE_OPENAI_ENDPOINT` — Azure OpenAI endpoint URL
  - `AZURE_OPENAI_API_KEY` — Azure OpenAI API key
  - `AZURE_OPENAI_MODEL` — Model deployment name (default: `gpt-4o`)
