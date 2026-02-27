# AGENTS.md — dynamic-sessions-mcp

## Overview

- This project demonstrates using Azure Container Apps Dynamic Sessions as a platform-managed MCP (Model Context Protocol) server.
- Unlike `/code-interpreter` and `/gpt-code-interpreter`, this project uses JSON-RPC protocol and API key authentication.

## Key Notes

- Always run commands from the project root directory (not from `/dynamic-sessions-mcp`).
- The ARM template `deploy.json` is used to create a session pool with MCP enabled (`mcpServerSettings.isMCPServerEnabled: true`).
- MCP communication uses JSON-RPC via `curl`. No Python code or `uv` required for this hands-on.
- API keys should never be committed to source control. Ensure `.vscode/mcp.json` is in `.gitignore`.
