# 🤖 AI Code Reviewer Agent

AI-powered code review agent that analyzes GitHub pull requests for bugs, security issues, and improvements using LangChain and Claude.

## Features

- 🔍 Analyze GitHub PRs for bugs, security vulnerabilities, and code quality issues
- 🤖 AI-powered code review using Claude, Gemini, or OpenAI
- 💬 Interactive follow-up questions about findings
- 🔐 Support for both public and private repositories
- 🎨 Clean Streamlit UI for easy interaction
- ⚡ Fast, asynchronous analysis

## Tech Stack

- **Backend**: FastAPI + LangChain + Python
- **Frontend**: Streamlit
- **LLM**: Claude (Anthropic), configurable to Gemini or OpenAI
- **GitHub API**: PyGithub
- **Database**: In-memory cache (upgradeable to PostgreSQL)

## Setup

### 1. Clone/Download Project
```bash
cd ai-code-reviewer
```

### 2. Create .env File
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_claude_key_here
```

Get API keys:
- **Claude**: https://console.anthropic.com/account/keys
- **Gemini**: https://ai.google.dev/
- **OpenAI**: https://platform.openai.com/account/api-keys

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Backend
```bash
python backend_main.py
```
Backend will start at `http://localhost:8000`

### 5. Run Frontend (New Terminal)
```bash
streamlit run frontend_app.py
```
Frontend will start at `http://localhost:8501`

## Usage

1. Paste a GitHub PR URL: `https://github.com/owner/repo/pull/123`
2. Click "Analyze PR"
3. Wait for analysis (may take 1-2 minutes)
4. View findings with severity levels
5. Ask follow-up questions in the "Ask Questions" tab

## API Endpoints

- `GET /health` - Health check
- `POST /analyze` - Analyze a PR
- `POST /follow-up` - Ask follow-up question
- `GET /docs` - Interactive API docs

## Project Structure

```
ai-code-reviewer/
├── config.py              # Configuration
├── llm_provider.py        # LLM abstraction (Claude/Gemini/OpenAI)
├── github_client.py       # GitHub API wrapper
├── code_review_agent.py   # Core review agent
├── backend_main.py        # FastAPI backend
├── frontend_app.py        # Streamlit frontend
├── requirements.txt       # Dependencies
└── .env.example          # Config template
```

## Switching LLM Providers

Just change `LLM_PROVIDER` in `.env`:

```env
LLM_PROVIDER=claude      # Use Claude
LLM_PROVIDER=gemini      # Use Gemini
LLM_PROVIDER=openai      # Use OpenAI
```

## Deployment

### Deploy Backend to Railway

1. Push to GitHub
2. Connect to Railway
3. Set environment variables
4. Deploy

### Deploy Frontend to Streamlit Cloud

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Set `.streamlit/secrets.toml` with env vars
4. Deploy

## Future Enhancements

- [ ] OAuth for GitHub (currently uses personal tokens)
- [ ] Database storage (PostgreSQL)
- [ ] Batch PR analysis
- [ ] GitHub bot integration
- [ ] Custom rulesets
- [ ] Team collaboration features

## License

MIT

## Author

Built by Christina Amine for portfolio demonstration.
