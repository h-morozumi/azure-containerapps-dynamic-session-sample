# AGENTS.md — mcp

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

## Key Notes

- Always run commands from the `/mcp` directory.
- This project uses Azure Container Apps Dynamic Sessions as an MCP (Model Context Protocol) server.
