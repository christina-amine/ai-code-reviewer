"""
FastAPI Backend for AI Code Reviewer Agent
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from code_review_agent import CodeReviewAgent
from config import settings
from github_oauth import oauth, create_session, get_session, delete_session
import asyncio
import os
from typing import Optional

# Initialize FastAPI app
app = FastAPI(
    title="AI Code Reviewer",
    description="AI-powered code review agent for GitHub PRs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signed cookie session, used by authlib to hold OAuth state/nonce during the
# GitHub redirect round-trip. Not to be confused with the opaque session id
# issued to the frontend after login (see github_oauth.py).
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

# Initialize agent
agent = CodeReviewAgent()

# In-memory storage for reviews (in production, use database)
reviews_cache = {}


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request to analyze a GitHub PR"""
    pr_url: str
    session_token: Optional[str] = None
    access_token: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response from PR analysis"""
    review_id: str
    pr_url: str
    pr_title: str
    pr_author: str
    files_changed: int
    analysis: str
    status: str


class FollowUpRequest(BaseModel):
    """Follow-up question about a review"""
    review_id: str
    question: str


class FollowUpResponse(BaseModel):
    """Response to follow-up question"""
    answer: str


# Routes

@app.get("/auth/github/login")
async def github_login(request: Request):
    """Redirect the browser to GitHub's OAuth consent screen."""
    return await oauth.github.authorize_redirect(request, settings.github_redirect_uri)


@app.get("/auth/github/callback")
async def github_callback(request: Request):
    """Handle GitHub's redirect back, exchange the code for a token, and start a session."""
    try:
        token = await oauth.github.authorize_access_token(request)
        user_resp = await oauth.github.get("user", token=token)
        user_resp.raise_for_status()
        user = user_resp.json()
    except Exception as e:
        return RedirectResponse(f"{settings.frontend_url}/?auth_error={str(e)}")

    session_id = create_session(
        access_token=token["access_token"],
        user={
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
        },
    )

    return RedirectResponse(f"{settings.frontend_url}/?session_token={session_id}")


@app.get("/auth/logout")
async def github_logout(session_token: Optional[str] = None):
    """Clear a server-side session."""
    if session_token:
        delete_session(session_token)
    return {"status": "logged_out"}


@app.get("/auth/me")
async def auth_me(session_token: Optional[str] = None):
    """Return the authenticated GitHub user for a session, if any."""
    session = get_session(session_token) if session_token else None
    if not session:
        return {"authenticated": False}
    return {"authenticated": True, "user": session["user"]}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_pr(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze a GitHub PR for code quality issues.

    Args:
        request: PR URL and optional access token

    Returns:
        Code review analysis
    """
    try:
        # Validate PR URL
        if not request.pr_url.startswith("https://github.com/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub PR URL"
            )

        # Resolve access token: prefer the OAuth session, fall back to a
        # directly supplied token (e.g. for programmatic API use).
        access_token = request.access_token
        if request.session_token:
            session = get_session(request.session_token)
            if session:
                access_token = session["access_token"]

        # Run review
        result = agent.review_pr(request.pr_url, access_token)

        # Cache result
        review_id = f"{request.pr_url}_{len(reviews_cache)}"
        reviews_cache[review_id] = result

        return AnalyzeResponse(review_id=review_id, **result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/follow-up", response_model=FollowUpResponse)
async def follow_up(request: FollowUpRequest):
    """
    Ask a follow-up question about a previous review.

    Args:
        request: Review ID and question

    Returns:
        Answer to the question
    """
    try:
        if request.review_id not in reviews_cache:
            raise HTTPException(
                status_code=404,
                detail="Review not found. Please analyze a PR first."
            )

        context = reviews_cache[request.review_id]
        answer = agent.follow_up_question(request.question, context)

        return FollowUpResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reviews/{review_id}")
async def get_review(review_id: str):
    """Get a previously stored review"""
    if review_id not in reviews_cache:
        raise HTTPException(status_code=404, detail="Review not found")

    return reviews_cache[review_id]


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "AI Code Reviewer",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "POST /analyze",
            "follow_up": "POST /follow-up",
            "github_login": "/auth/github/login",
            "github_callback": "/auth/github/callback",
            "logout": "/auth/logout",
            "me": "/auth/me",
            "docs": "/docs",
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
