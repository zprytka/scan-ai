# middleware/planner.py
# Connects to Claude API and requests scan plan

import anthropic
import os
import json


client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


def plan_with_claude(subnet):
    prompt = f"""
You are a pentesting expert. Generate STEALTHY nmap commands to scan the network {subnet}.

IMPORTANT: You must return EXACTLY this JSON format:

{{
  "steps": [
    "Active host discovery",
    "Complete port scan (stealthy)"
  ],
  "commands": [
    "nmap -sn {subnet}",
    "nmap -p- --min-rate 500 {subnet}"
  ]
}}

Generate nmap commands for:
1. Discover active hosts with ping sweep (-sn)
2. Scan ALL ports in a controlled manner (--min-rate 500 to avoid detection)

IMPORTANT NOTES:
- Use --min-rate 500 instead of -T4 to control traffic
- The third scan (services) will be done dynamically later with found ports
- DO NOT include -sV -sC in these initial commands

DO NOT include additional text, ONLY valid JSON.
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response text safely
        text = response.content[0].text

        # Search for JSON in the response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            result = json.loads(json_str)
            return result
        else:
            print("[!] No valid JSON found in response")
            return {"commands": []}
    except Exception as e:
        print(f"[!] Error in planner: {e}")
        return {"commands": []}
