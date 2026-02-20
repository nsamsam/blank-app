# CLAUDE.md

## Project Overview

This is a **Streamlit** web application built from the official Streamlit blank app template. It is licensed under Apache 2.0 and designed for deployment on [Streamlit Community Cloud](https://streamlit.io/cloud).

## Repository Structure

```
.
├── streamlit_app.py       # Main application entry point
├── requirements.txt       # Python dependencies
├── .devcontainer/         # Dev container configuration (Codespaces / VS Code)
│   └── devcontainer.json
├── .github/
│   └── CODEOWNERS         # Owned by @streamlit/community-cloud
├── .gitignore             # Standard Python gitignore
├── LICENSE                # Apache License 2.0
└── README.md              # Project readme
```

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** Streamlit
- **Deployment:** Streamlit Community Cloud

## Development Setup

### Install dependencies

```
pip install -r requirements.txt
```

### Run the app locally

```
streamlit run streamlit_app.py
```

The app will be available at `http://localhost:8501`.

### Dev Container (Codespaces)

The `.devcontainer/devcontainer.json` is configured to:
- Use Python 3.11 (Debian Bullseye)
- Auto-install requirements on container creation
- Auto-start the Streamlit server on port 8501 with CORS and XSRF protection disabled (for the dev container proxy)

## Key Files

| File | Purpose |
|---|---|
| `streamlit_app.py` | Single entry point for the Streamlit app. All UI code goes here (or in modules imported from here). |
| `requirements.txt` | Pin all Python dependencies here. Currently only `streamlit`. |
| `.streamlit/secrets.toml` | Streamlit secrets file (gitignored, never commit). Use for API keys and sensitive config. |

## Conventions

- **Entry point:** `streamlit_app.py` is the main file Streamlit Community Cloud looks for. Do not rename it without updating the deployment configuration.
- **Dependencies:** Add new Python packages to `requirements.txt`, one per line.
- **Secrets:** Use Streamlit's built-in secrets management (`st.secrets`) rather than environment variables or `.env` files. The `.streamlit/secrets.toml` file is gitignored.
- **No build step:** Streamlit apps have no compile/build step. Changes to `.py` files take effect on reload.

## Testing

No test framework is currently configured. If adding tests:
- Use `pytest` as the test runner
- Place tests in a `tests/` directory
- Add `pytest` to `requirements.txt` (or a separate `requirements-dev.txt`)

## Deployment

The app is deployed via Streamlit Community Cloud. Pushing to the default branch triggers automatic redeployment. No CI/CD pipeline or manual build step is required.
