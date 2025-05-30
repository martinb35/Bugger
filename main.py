import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict, Counter
from datetime import datetime, timezone
import gradio as gr
import re
from urllib.parse import quote
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure DevOps configuration from environment variables
ORG = os.getenv("AZURE_DEVOPS_ORG")
PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
USER_EMAIL = os.getenv("AZURE_DEVOPS_USER_EMAIL")
PERSONAL_ACCESS_TOKEN = os.getenv("AZURE_DEVOPS_PAT")

# Validate that all required environment variables are set
required_vars = {
    "AZURE_DEVOPS_ORG": ORG,
    "AZURE_DEVOPS_PROJECT": PROJECT,
    "AZURE_DEVOPS_USER_EMAIL": USER_EMAIL,
    "AZURE_DEVOPS_PAT": PERSONAL_ACCESS_TOKEN
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def extract_meaningful_buckets(bugs_data):
    """Group bugs by meaningful patterns and create queries for each bucket"""
    buckets = {}
    
    # Analyze titles and descriptions for patterns
    all_text = []
    for bug_id, title, description, url, created, activated in bugs_data:
        all_text.append(f"{title} {description}".lower())
    
    # Common Windows/OS patterns
    patterns = {
        "BSoD/Crashes": {
            "keywords": ["bsod", "blue screen", "crash", "exception", "fault", "bugcheck", "stop error"],
            "explanation": "System crashes and blue screen errors that require immediate investigation",
            "action": "Analyze crash dumps, check driver compatibility, and review recent system changes"
        },
        "Boot/Startup": {
            "keywords": ["boot", "startup", "start", "initialization", "init", "loading"],
            "explanation": "Issues preventing system or application startup",
            "action": "Check boot configuration, startup dependencies, and initialization sequences"
        },
        "Performance/Hangs": {
            "keywords": ["slow", "hang", "freeze", "performance", "timeout", "unresponsive"],
            "explanation": "Performance degradation and system responsiveness issues",
            "action": "Profile performance bottlenecks, check resource usage, and optimize critical paths"
        },
        "Driver Issues": {
            "keywords": ["driver", "device", "hardware", "pnp", "plug and play"],
            "explanation": "Hardware driver compatibility and device management problems",
            "action": "Update drivers, check hardware compatibility, and review device manager errors"
        },
        "Memory Issues": {
            "keywords": ["memory", "leak", "heap", "allocation", "out of memory", "oom"],
            "explanation": "Memory management problems including leaks and allocation failures",
            "action": "Run memory analysis tools, check for leaks, and optimize memory usage"
        },
        "Security/Access": {
            "keywords": ["security", "permission", "access", "privilege", "auth", "token"],
            "explanation": "Security vulnerabilities and access control issues",
            "action": "Review security policies, check permissions, and audit access controls"
        },
        "File System": {
            "keywords": ["file", "disk", "storage", "ntfs", "fat32", "corruption"],
            "explanation": "File system corruption and storage-related problems",
            "action": "Run disk checks, verify file system integrity, and check storage health"
        }
    }
    
    # Group bugs by patterns
    for pattern_name, pattern_info in patterns.items():
        matching_bugs = []
        for bug_id, title, description, url, created, activated in bugs_data:
            text = f"{title} {description}".lower()
            if any(keyword in text for keyword in pattern_info["keywords"]):
                matching_bugs.append((bug_id, title, description, url, created, activated))
        
        if matching_bugs:  # Only include buckets with bugs
            # Create a proper WIQL query with correct syntax
            keyword_conditions = []
            for kw in pattern_info["keywords"][:3]:  # Use top 3 keywords
                keyword_conditions.append(f"[System.Title] Contains '{kw}'")
                keyword_conditions.append(f"[System.Description] Contains '{kw}'")
            
            wiql = f"""SELECT [System.Id], [System.Title], [System.State] 
                      FROM WorkItems 
                      WHERE [System.WorkItemType] = 'Bug' 
                      AND [System.AssignedTo] = '{USER_EMAIL}' 
                      AND [System.State] = 'Active' 
                      AND ({' OR '.join(keyword_conditions)})"""
            
            # Properly encode the WIQL query for URL
            encoded_wiql = quote(wiql)
            query_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems?_a=query&wiql={encoded_wiql}"
            
            buckets[pattern_name] = {
                "bugs": matching_bugs,
                "explanation": pattern_info["explanation"],
                "action": pattern_info["action"],
                "query_url": query_url,
                "count": len(matching_bugs)
            }
    
    return buckets

def fetch_and_summarize_bugs():
    wiql_query = {
        "query": f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.WorkItemType] = 'Bug'
            AND [System.AssignedTo] = '{USER_EMAIL}'
            AND [System.State] = 'Active'
        """
    }

    url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/wiql?api-version=7.0"
    response = requests.post(
        url,
        json=wiql_query,
        auth=HTTPBasicAuth('', PERSONAL_ACCESS_TOKEN)
    )
    response.raise_for_status()
    work_items = response.json().get("workItems", [])

    if not work_items:
        return "No active bugs assigned to you."

    def chunked(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    bugs_data = []
    created_dates = []
    activated_dates = []
    now = datetime.now(timezone.utc)

    for chunk in chunked(work_items, 200):
        ids = [str(item["id"]) for item in chunk]
        ids_str = ",".join(ids)
        details_url = (
            f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/workitems"
            f"?ids={ids_str}"
            f"&fields=System.Id,System.Title,System.State,System.CreatedDate,Microsoft.VSTS.Common.ActivatedDate,System.Description"
            f"&api-version=7.0"
        )
        details_response = requests.get(
            details_url,
            auth=HTTPBasicAuth('', PERSONAL_ACCESS_TOKEN)
        )
        details_response.raise_for_status()
        details = details_response.json().get("value", [])
        
        for bug in details:
            fields = bug["fields"]
            bug_id = bug["id"]
            title = fields.get("System.Title", "No Title")
            description = fields.get("System.Description", "")
            url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/{bug_id}"
            
            created = fields.get("System.CreatedDate")
            activated = fields.get("Microsoft.VSTS.Common.ActivatedDate")
            
            bugs_data.append((bug_id, title, description, url, created, activated))
            
            if created:
                created_dates.append((bug_id, datetime.fromisoformat(created.rstrip("Z")).replace(tzinfo=timezone.utc)))
            if activated:
                activated_dates.append((bug_id, datetime.fromisoformat(activated.rstrip("Z")).replace(tzinfo=timezone.utc)))

    total_bugs = len(work_items)
    if created_dates:
        avg_age_days = sum((now - dt).days for _, dt in created_dates) / len(created_dates)
    else:
        avg_age_days = 0
    if activated_dates:
        avg_active_days = sum((now - dt).days for _, dt in activated_dates) / len(activated_dates)
    else:
        avg_active_days = 0

    # Group bugs into meaningful buckets
    buckets = extract_meaningful_buckets(bugs_data)
    
    # Sort buckets by count (largest first)
    sorted_buckets = sorted(buckets.items(), key=lambda x: x[1]["count"], reverse=True)

    md = []
    md.append("## 🐞 Bug Stats")
    md.append(f"- **Total active bugs:** {total_bugs}")
    md.append(f"- **Average bug age:** {avg_age_days:.1f} days")
    md.append(f"- **Average length of being active:** {avg_active_days:.1f} days\n")

    if sorted_buckets:
        md.append("## 📊 Bug Analysis by Issue Type")
        
        for bucket_name, bucket_info in sorted_buckets:
            md.append(f"### {bucket_info['count']} bugs likely related to: {bucket_name}")
            md.append(f"**What these bugs are about:** {bucket_info['explanation']}")
            md.append(f"**Recommended next steps:** {bucket_info['action']}")
            md.append(f"**[→ View all {bucket_name} bugs in Azure DevOps]({bucket_info['query_url']})**")
            
            # Show sample bugs
            md.append("\n**Sample bugs:**")
            for bug_id, title, description, url, created, activated in bucket_info['bugs'][:3]:
                md.append(f"- [{title}]({url})")
            
            if bucket_info['count'] > 3:
                md.append(f"...and {bucket_info['count'] - 3} more")
            md.append("")

        # Overall recommendations
        md.append("## 💡 Priority Recommendations")
        if sorted_buckets:
            top_bucket = sorted_buckets[0]
            md.append(f"1. **Focus on {top_bucket[0]}** - This is your largest category with {top_bucket[1]['count']} bugs")
            md.append(f"2. **{top_bucket[1]['action']}**")
            
        if avg_age_days > 60:
            md.append("3. **Triage old bugs** - Some bugs are quite old and may need to be closed or deprioritized")
        
        if len(sorted_buckets) > 3:
            md.append("4. **Consider batch processing** - You have multiple issue types that could benefit from focused sprints")
    else:
        md.append("## 📊 No clear patterns found")
        md.append("Your bugs don't fit common categories. Consider manual review or different grouping criteria.")

    return "\n".join(md)

with gr.Blocks() as demo:
    gr.Markdown("# 🐞 My Active Bugs Dashboard")
    output = gr.Markdown()
    btn = gr.Button("🔄 Refresh Analysis")
    btn.click(fn=fetch_and_summarize_bugs, outputs=output)
    demo.load(fn=fetch_and_summarize_bugs, outputs=output)

if __name__ == "__main__":
    demo.launch()