# AGENTS.md — code-interpreter

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

- Always run commands from the `/code-interpreter` directory.
- Environment variables are loaded from `.env` file. Copy `.env.example` to `.env` and set required values before running.
