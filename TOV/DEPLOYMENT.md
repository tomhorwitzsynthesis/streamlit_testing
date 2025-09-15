# Deployment Guide for Streamlit Cloud

## Setting up Secrets in Streamlit Cloud

### 1. Deploy to Streamlit Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the main file path to `app.py`

### 2. Configure Secrets
In your Streamlit Cloud app settings, go to "Secrets" and add these key-value pairs:

```
OPENAI_API_KEY = your_actual_openai_api_key_here
OPENAI_BASE_URL = https://api.openai.com/v1
LLM_MODEL = gpt-4o
LLM_TIMEOUT = 20
```

### 3. Alternative: Use .streamlit/secrets.toml (for local testing)
Create a `.streamlit/secrets.toml` file in your project root:

```toml
OPENAI_API_KEY = "your_actual_openai_api_key_here"
OPENAI_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o"
LLM_TIMEOUT = "20"
```

**Important:** Never commit this file to GitHub! Add it to `.gitignore`.

## Local Development

### Option 1: Use .env file (current setup)
Create a `.env` file in your project root:
```
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_TIMEOUT=20
```

### Option 2: Use Streamlit secrets
Create `.streamlit/secrets.toml` as shown above.

## How the Code Works

The `_get_secret()` function in `llm.py` automatically:
1. **First tries Streamlit secrets** (for cloud deployment)
2. **Falls back to environment variables** (for local development with .env)
3. **Uses default values** if neither is available

This means your app will work in both environments without any code changes!

## Required Files for GitHub

Make sure these files are in your GitHub repository root:
- `app.py` (main Streamlit app)
- `llm.py` (LLM wrapper)
- `prompting.py` (prompt building)
- `storage.py` (data persistence)
- `requirements.txt` (dependencies)
- `README.md` (optional but recommended)

## Security Notes

- ✅ **DO**: Use Streamlit Cloud secrets for production
- ✅ **DO**: Use .env files for local development
- ❌ **DON'T**: Commit API keys to GitHub
- ❌ **DON'T**: Hardcode secrets in your code
- ❌ **DON'T**: Share your secrets.toml file
