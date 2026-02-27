# AGENTS.md

Think in English, output in Japanese.

## Project Overview

This repository contains hands-on samples for Azure Container Apps Dynamic Sessions. It demonstrates how to execute Python code in the cloud using session pools.

## Repository Structure

- `/code-interpreter` — Python sample that calls Dynamic Sessions REST API to execute code in a session pool.
- `/gpt-code-interpreter` — Sample that uses Dynamic Sessions as a code execution tool via Azure OpenAI Function Calling.

## Language and Style

- All documentation (README.md, comments, commit messages) MUST be written in **Japanese**.
- Code (variable names, function names, etc.) should be written in English.

## Prerequisites

- Azure subscription
- Azure CLI installed and logged in (`az login`)
- A session pool created and role assigned (see root README.md for setup steps)

## Development Environment

- This project is designed to run in a **DevContainer** (GitHub Codespaces or VS Code Dev Containers).
- Each sub-project (`/code-interpreter`, `/gpt-code-interpreter`) is an independent Python project managed by `uv`.
- Refer to each sub-directory's `AGENTS.md` for project-specific instructions.
