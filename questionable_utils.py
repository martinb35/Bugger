import re
import requests

def is_real_person_name(created_by):
    """Check if the bug creator appears to be a real person"""
    if not created_by:
        return False

    name = created_by.lower().strip()
    bot_indicators = [
        'bot', 'system', 'auto', 'service', 'script', 'automation',
        'test', 'dummy', 'fake', 'admin', 'api', 'webhook', 'deploy'
    ]
    if any(indicator in name for indicator in bot_indicators):
        return False
    # Heuristic: real names usually have a space and are not all lowercase
    if " " in original_name and not original_name.islower():
        return True
    # Accept emails that look like real people
    if re.match(r"^[a-z]+\.[a-z]+@", name):
        return True
    # Otherwise, likely not a real person
    return False

def extract_links_from_text(text):
    """Extract all URLs from a given text"""
    if not text:
        return []
    url_pattern = re.compile(r'https?://[^\s\]\)]+')
    return url_pattern.findall(text)

def check_link_actionability(url, timeout=5):
    """Check if a link is reachable (basic HEAD request)"""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False

def has_clear_remediation_steps(description):
    """Heuristic: does the description contain clear remediation steps?"""
    if not description:
        return False
    desc = description.lower()
    action_words = [
        "fix", "resolve", "update", "remove", "replace", "implement",
        "add", "change", "correct", "address", "patch", "refactor"
    ]
    return any(word in desc for word in action_words)

def is_title_unique(title, all_titles):
    """Check if the title is unique among all bug titles"""
    if not title or not all_titles:
        return True
    return all_titles.count(title) == 1

def has_repro_steps(text):
    """Check if text contains indications of repro steps"""
    if not text:
        return False
    desc_lower = text.lower()
    step_indicators = [
        'step 1', 'step 2', 'step 3', 'steps to reproduce', 'repro steps',
        'reproduce:', 'steps:', 'to reproduce', 'how to reproduce',
        'first', 'then', 'next', 'finally', 'expected', 'actual'
    ]
    if any(ind in desc_lower for ind in step_indicators):
        return True
    if any(f"{n}." in desc_lower for n in range(1, 5)):
        return True
    return False

def evaluate_bot_bug_actionability(bug_id, title, description, all_titles, progress_callback=None):
    """Evaluate if a bot-created bug is actionable (stub for extensibility)"""
    # Example: must have a unique title and clear remediation steps
    reasons = []
    if not is_title_unique(title, all_titles):
        reasons.append("Non-unique title")
    if not has_clear_remediation_steps(description):
        reasons.append("No clear remediation steps")
    if not description or len(description) < 10:
        reasons.append("Description too short")
    return len(reasons) == 0, reasons