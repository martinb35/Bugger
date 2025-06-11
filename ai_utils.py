import re
import requests
import time
from collections import defaultdict
from config import ORG, PROJECT, AZURE_DEVOPS_PAT

def call_ai_api(prompt, max_tokens=150):
    """
    Stub for calling an AI API (e.g., OpenAI GPT-4o).
    Replace with your actual API call logic.
    """
    # Example: return a dummy response for now
    return "AI response placeholder"

def fallback_person_check(created_by):
    """Fallback heuristic to check if the creator is a real person."""
    if not created_by:
        return False
    name = created_by.lower().strip()
    bot_indicators = [
        'bot', 'system', 'auto', 'service', 'script', 'automation',
        'test', 'dummy', 'fake', 'admin', 'api', 'webhook', 'deploy'
    ]
    if any(indicator in name for indicator in bot_indicators):
        return False
    if " " in name and not name.islower():
        return True
    if re.match(r"^[a-z]+\.[a-z]+@", name):
        return True
    return False

def fallback_actionability_check(title, description):
    """Fallback heuristic to check if a bug is actionable."""
    if not description or len(description) < 10:
        return False
    desc = description.lower()
    action_words = [
        "fix", "resolve", "update", "remove", "replace", "implement",
        "add", "change", "correct", "address", "patch", "refactor"
    ]
    if any(word in desc for word in action_words):
        return True
    # If description is just repeating the title, not actionable
    if title and desc.strip() == title.lower().strip():
        return False
    return True

def check_for_dead_links(description, timeout=5):
    """Check for dead links in the description."""
    if not description:
        return []
    url_pattern = re.compile(r'https?://[^\s\]\)]+')
    urls = url_pattern.findall(description)
    dead_links = []
    for url in urls:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=timeout)
            if resp.status_code != 200:
                dead_links.append(url)
        except Exception:
            dead_links.append(url)
    return dead_links

def fallback_title_grouping(all_bugs):
    """Fallback heuristic: group bugs by normalized titles."""
    title_groups = defaultdict(list)
    for bug in all_bugs:
        title = bug[1] or ""
        normalized = re.sub(r'\d+', 'N', title.lower())
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())
        title_groups[normalized].append(bug)
    similar_bugs = []
    for group_bugs in title_groups.values():
        if len(group_bugs) >= 2:
            similar_bugs.extend(group_bugs)
    return similar_bugs