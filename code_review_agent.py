"""
AI Code Reviewer Agent
Analyzes GitHub PRs for bugs, security issues, and improvements
"""

from llm_provider import get_llm
from github_client import fetch_pr_for_review
from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from typing import Any, Dict, List
import json


@tool
def analyze_code_for_issues(code_content: str) -> str:
    """
    Analyze code content for potential bugs, security issues, and improvements.

    Args:
        code_content: The code to analyze

    Returns:
        Analysis report with issues and recommendations
    """
    llm = get_llm()

    prompt = f"""Analyze this code for issues. Look for:
1. BUGS: Logic errors, off-by-one errors, null pointer issues
2. SECURITY: SQL injection, XSS, authentication/authorization issues
3. PERFORMANCE: Inefficient algorithms, N+1 queries, memory leaks
4. STYLE: PEP8 violations, naming conventions, code organization
5. BEST PRACTICES: Error handling, logging, testing

Code to review:
```
{code_content}
```

Provide a structured analysis with specific line numbers and fixes."""

    response = llm.invoke(prompt)
    return response.content


@tool
def get_file_context(filename: str, file_patch: str = "") -> str:
    """
    Get context about a file being changed in the PR.

    Args:
        filename: Name of the file
        file_patch: The diff/patch of changes

    Returns:
        Analysis of the changes in context
    """
    llm = get_llm()

    prompt = f"""Analyze this file change in context. What is the purpose of this change?

File: {filename}
Changes (patch format):
{file_patch}

Provide a brief summary of what's being changed and why."""

    response = llm.invoke(prompt)
    return response.content


@tool
def generate_security_report(pr_code_content: str) -> str:
    """
    Generate a focused security analysis of the PR changes.

    Args:
        pr_code_content: The PR code changes

    Returns:
        Security-focused report
    """
    llm = get_llm()

    prompt = f"""Perform a security code review. Look for:
- Authentication/Authorization flaws
- Input validation issues
- SQL injection vulnerabilities
- XSS vulnerabilities
- Sensitive data exposure
- Cryptographic weaknesses
- Dependency vulnerabilities

Code:
{pr_code_content}

Report severity levels (Critical, High, Medium, Low) and provide fixes."""

    response = llm.invoke(prompt)
    return response.content


class CodeReviewAgent:
    """AI-powered code review agent"""

    def __init__(self):
        self.llm = get_llm()
        self.tools = [
            analyze_code_for_issues,
            get_file_context,
            generate_security_report,
        ]
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Create LangChain agent executor"""
        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )
        return executor

    def review_pr(self, pr_url: str, access_token: str = None) -> Dict[str, Any]:
        """
        Conduct a comprehensive code review on a GitHub PR.

        Args:
            pr_url: GitHub PR URL
            access_token: Optional GitHub OAuth token for private repos

        Returns:
            Review report with findings and recommendations
        """
        pr_data = fetch_pr_for_review(pr_url, access_token)

        pr_info = pr_data["pr"]
        files = pr_data["files"]
        languages = pr_data["languages"]

        code_content = self._format_pr_code(files)

        analysis_prompt = f"""Review this GitHub PR:

Title: {pr_info['title']}
Description: {pr_info['description']}
Author: {pr_info['author']}
Files Changed: {pr_info['changed_files']}
Additions: {pr_info['additions']}
Deletions: {pr_info['deletions']}
Languages Used: {', '.join(languages.keys()) if languages else 'Unknown'}

Analyze the code changes for:
1. Critical bugs or errors
2. Security vulnerabilities
3. Performance issues
4. Code style and best practices
5. Testing coverage gaps

Provide actionable recommendations for each issue found.

Changed code:
{code_content}"""

        result = self.agent_executor.invoke({"input": analysis_prompt})

        return {
            "pr_url": pr_url,
            "pr_title": pr_info["title"],
            "pr_author": pr_info["author"],
            "files_changed": pr_info["changed_files"],
            "analysis": result.get("output", ""),
            "status": "completed",
        }

    def follow_up_question(self, question: str, review_context: Dict[str, Any]) -> str:
        """
        Answer follow-up questions about the code review.

        Args:
            question: User's follow-up question
            review_context: Context from the initial review

        Returns:
            Answer to the question
        """
        prompt = f"""Based on the previous code review:

PR: {review_context['pr_title']}
Previous Analysis: {review_context['analysis']}

User Question: {question}

Provide a detailed answer referencing the code review context."""

        result = self.agent_executor.invoke({"input": prompt})
        return result.get("output", "")

    @staticmethod
    def _format_pr_code(files: List[Dict[str, Any]]) -> str:
        """Format PR file changes into readable code blocks"""
        formatted = []

        for file in files:
            formatted.append(f"\n{'='*60}")
            formatted.append(f"File: {file['filename']}")
            formatted.append(f"Status: {file['status']} (+{file['additions']}/-{file['deletions']})")
            formatted.append(f"{'='*60}")
            formatted.append(file.get('patch', ''))

        return "\n".join(formatted)
