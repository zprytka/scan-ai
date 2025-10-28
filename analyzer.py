# middleware/analyzer.py
# Sends summary to Claude and gets response

import anthropic
import os
import json


client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


def analyze_results(json_results):
    """
    Analyzes scan results using Claude AI

    Args:
        json_results: List of dictionaries with parsed results

    Returns:
        Text with security analysis
    """
    if not json_results:
        return "[!] No results to analyze"

    try:
        # Limit data size sent to Claude
        limited_data = json.dumps(json_results[:2], indent=2)[:8000]

        prompt = f"""
Analyze the following Nmap scan results:

{limited_data}

Identify:
- Dangerous or exposed services
- Known vulnerable versions
- Common attack vectors
- Suggestions for next pentesting steps
- Overall risk level (Low/Medium/High/Critical)
"""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    except Exception as e:
        return f"[!] Error in analysis: {e}"
