import re
import requests
import time
from collections import defaultdict
from urllib.parse import quote, urlparse
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE, AZURE_DEVOPS_PAT

class QuestionableAnalyzer:
    def __init__(self):
        self.questionable_categories = {
            "Empty/Minimal Description": [],
            "Broken References": [],
            "Vague Internal References": [],
            "Cryptic Technical Jargon": [],
            "Non-Descriptive Placeholders": [],
            "Copy-Paste Artifacts": [],
            "Duplicate Title/Description": [],
            "Special Characters Soup": [],
            "Single Word Description": [],
            "Similar Titles Group": [],
            "Fake/Bot Created": [],
            "Dead Links": []
        }
        
        self.category_explanations = {
            "Empty/Minimal Description": "Bugs with no description or repro steps (less than 10 characters total) - impossible to understand the issue",
            "Broken References": "Bugs pointing to attachments, links, or documents that likely don't exist in the bug report",
            "Vague Internal References": "Bugs referencing discussions, emails, or meetings without providing context",
            "Cryptic Technical Jargon": "Bugs with generic technical terms that don't explain the actual problem",
            "Non-Descriptive Placeholders": "Bugs with placeholder text like 'needs fixing' without explaining what's broken",
            "Copy-Paste Artifacts": "Bugs with test data, Lorem Ipsum, or temporary content",
            "Duplicate Title/Description": "Bugs where the description just repeats the title without adding details",
            "Special Characters Soup": "Bugs with descriptions full of special characters and no meaningful text",
            "Single Word Description": "Bugs with only 1-2 word descriptions that provide no context",
            "Similar Titles Group": "Multiple bugs with nearly identical titles - likely duplicates or related issues that should be consolidated",
            "Fake/Bot Created": "Bugs created by automated systems, bots, or users with suspicious names that fail actionability tests",
            "Dead Links": "Bugs with links that are broken, inaccessible, or lead to non-actionable content"
        }

    def _is_real_person_name(self, created_by):
        """Check if the bug creator appears to be a real person"""
        if not created_by:
            return False
            
        name = created_by.lower().strip()
        
        # Check for bot/system indicators
        bot_indicators = [
            'bot', 'system', 'auto', 'service', 'script', 'automation',
            'test', 'dummy', 'fake', 'admin', 'api', 'webhook', 'deploy'
        ]
        
        if any(indicator in name for indicator in bot_indicators):
            return False
            
        # Check for generic patterns
        generic_patterns = [
            r'^user\d+',
            r'^test\d*$',
            r'^admin\d*$',
            r'^temp\d*$',
            r'^\w{1,2}$',  # Too short
            r'^[a-z]+\d+@',  # Email-like but generic
        ]
        
        if any(re.match(pattern, name) for pattern in generic_patterns):
            return False
            
        # Should have at least one space or proper email format
        if '@' in name:
            # Email format - check for reasonable name part
            local_part = name.split('@')[0]
            return len(local_part) > 3 and not local_part.isdigit()
        else:
            # Should have first/last name or be reasonable length
            return len(name) > 3 and (' ' in name or len(name) > 6)

    def _extract_links_from_text(self, text):
        """Extract URLs from bug description"""
        if not text:
            return []
            
        # Pattern to match URLs
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, text)
        
        # Also look for Azure DevOps work item references
        workitem_pattern = r'#(\d+)'
        workitem_refs = re.findall(workitem_pattern, text)
        
        # Convert work item refs to URLs
        for ref in workitem_refs:
            urls.append(f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/{ref}")
            
        return urls

    def _check_link_actionability(self, url):
        """Check if a link contains actionable information"""
        try:
            # Set timeout and headers
            headers = {
                'User-Agent': 'Bugger-Analysis-Tool/1.0'
            }
            
            # Add Azure DevOps authentication only for Azure DevOps URLs
            if 'dev.azure.com' in url or 'visualstudio.com' in url:
                import base64
                auth_string = f":{AZURE_DEVOPS_PAT}"
                auth_bytes = auth_string.encode('ascii')
                auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                headers['Authorization'] = f'Basic {auth_b64}'
            
            response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            
            if response.status_code == 404:
                return False, "Link not found (404)"
            elif response.status_code == 403:
                return False, "Access denied (403)"
            elif response.status_code >= 400:
                return False, f"Link error ({response.status_code})"
                
            content = response.text.lower()
            
            # Check for actionable indicators
            actionable_indicators = [
                'urgent', 'critical', 'immediate', 'asap', 'priority',
                'deadline', 'blocker', 'production', 'customer',
                'escalation', 'sev 1', 'severity 1', 'p1', 'high priority'
            ]
            
            if any(indicator in content for indicator in actionable_indicators):
                return True, "Contains priority/urgency indicators"
                
            # Check for substantial content
            if len(content.strip()) < 100:
                return False, "Minimal content"
                
            return True, "Contains substantial content"
            
        except requests.RequestException as e:
            return False, f"Link inaccessible: {str(e)[:50]}"
        except Exception as e:
            return False, f"Error checking link: {str(e)[:50]}"

    def _has_clear_remediation_steps(self, description):
        """Check if description contains clear remediation steps"""
        if not description or len(description.strip()) < 50:
            return False
            
        desc_lower = description.lower()
        
        # Look for step-by-step instructions
        step_indicators = [
            'step 1', 'step 2', '1.', '2.', '3.', 
            'first', 'then', 'next', 'finally',
            'to fix', 'to resolve', 'solution:', 'workaround:',
            'remedy:', 'mitigation:', 'action:', 'steps:'
        ]
        
        if any(indicator in desc_lower for indicator in step_indicators):
            return True
            
        # Look for imperative verbs suggesting actions
        action_verbs = [
            'update', 'install', 'restart', 'configure', 'change',
            'modify', 'replace', 'remove', 'add', 'set', 'run',
            'execute', 'apply', 'download', 'upgrade'
        ]
        
        # Must have at least 2 action verbs to be considered actionable
        action_count = sum(1 for verb in action_verbs if verb in desc_lower)
        
        return action_count >= 2

    def _is_title_unique(self, title, all_titles):
        """Check if title is unique enough (not replicated across many bugs)"""
        if not title:
            return False
            
        # Normalize title for comparison
        normalized_title = re.sub(r'\d+', 'N', title.lower())
        normalized_title = re.sub(r'[^\w\s]', ' ', normalized_title)
        normalized_title = ' '.join(normalized_title.split())
        
        # Count similar titles
        similar_count = 0
        for other_title in all_titles:
            if other_title != title:
                other_normalized = re.sub(r'\d+', 'N', other_title.lower())
                other_normalized = re.sub(r'[^\w\s]', ' ', other_normalized)
                other_normalized = ' '.join(other_normalized.split())
                
                # Consider similar if 80% of words match
                title_words = set(normalized_title.split())
                other_words = set(other_normalized.split())
                
                if title_words and other_words:
                    overlap = len(title_words.intersection(other_words))
                    similarity = overlap / max(len(title_words), len(other_words))
                    
                    if similarity > 0.8:
                        similar_count += 1
        
        # Consider unique if fewer than 3 similar titles
        return similar_count < 3

    def _evaluate_bot_bug_actionability(self, bug_id, title, description, all_titles, progress_callback=None):
        """Evaluate if a bot-created bug passes the actionability test"""
        
        # Test 1: Clear remediation steps
        has_remediation = self._has_clear_remediation_steps(description)
        
        # Test 2: Check for dead links
        links = self._extract_links_from_text(description)
        has_dead_links = False
        
        if links:
            if progress_callback:
                progress_callback(0, f"Checking links for bug {bug_id}...")
            
            for link in links:
                time.sleep(0.2)  # Rate limiting
                is_accessible, reason = self._check_link_actionability(link)
                if not is_accessible and ("404" in reason or "not found" in reason.lower()):
                    has_dead_links = True
                    break
        
        # Test 3: Title uniqueness
        is_unique_title = self._is_title_unique(title, all_titles)
        
        # Pass all three tests to be considered actionable
        passes_test = has_remediation and not has_dead_links and is_unique_title
        
        return passes_test, {
            'has_remediation': has_remediation,
            'has_dead_links': has_dead_links,
            'is_unique_title': is_unique_title
        }

    def analyze_and_separate_bugs(self, bugs_data, progress_callback=None):
        """Analyze bugs and separate into questionable and actionable categories"""
        questionable_bugs = []
        actionable_bugs_data = []
        questionable_by_title_pattern = defaultdict(list)
        bot_created_bugs = []
        
        total_bugs = len(bugs_data)
        all_titles = [bug[1] for bug in bugs_data]  # Extract all titles for uniqueness check
        
        if progress_callback:
            progress_callback(0, "Starting bug analysis...")
        
        # First pass: identify questionable bugs and separate bot-created ones
        for i, bug_tuple in enumerate(bugs_data):
            if progress_callback:
                progress_callback(
                    int((i / total_bugs) * 60),  # First 60% for basic analysis
                    f"Analyzing bug {bug_tuple[0]}..."
                )
            
            # Handle different tuple lengths for backward compatibility
            if len(bug_tuple) == 6:
                bug_id, title, description, url, created, activated = bug_tuple
                created_by = "Unknown"
            else:
                bug_id, title, description, url, created, activated, created_by = bug_tuple
            
            desc_text = (description or "").strip()
            title_text = (title or "").strip()
            combined_text = f"{title_text} {desc_text}".lower()
            
            is_questionable = False
            
            # Check if creator is a real person
            if not self._is_real_person_name(created_by):
                # Store bot-created bugs for special evaluation
                bot_created_bugs.append((bug_id, title, description, url, created, activated, created_by))
                continue
                
            # Check for empty or extremely minimal descriptions
            elif len(desc_text) < 10 or not desc_text:
                is_questionable = True
                self.questionable_categories["Empty/Minimal Description"].append((bug_id, title, description, url, created, activated))
                # Track title patterns
                title_pattern = re.sub(r'\d+', 'N', title_text)
                title_pattern = re.sub(r'[^\w\s]', '', title_pattern).strip()
                if title_pattern:
                    questionable_by_title_pattern[title_pattern].append((bug_id, title, description, url, created, activated))
            
            # Check for broken references
            elif any(pattern in combined_text for pattern in [
                "see attachment", "see link", "see document", "refer to", "check the",
                "attached file", "linked document", "external reference"
            ]):
                is_questionable = True
                self.questionable_categories["Broken References"].append((bug_id, title, description, url, created, activated))
                
            # Check for vague internal references
            elif any(pattern in combined_text for pattern in [
                "see above", "as mentioned", "per discussion", "like before", "same issue",
                "ditto", "idem", "^", "same as #", "duplicate of #",
                "internal ticket", "see jira", "check slack", "email thread",
                "meeting notes", "verbal request", "phone call"
            ]):
                is_questionable = True
                self.questionable_categories["Vague Internal References"].append((bug_id, title, description, url, created, activated))
                
            # Check for cryptic technical jargon without context
            elif any(pattern in combined_text for pattern in [
                "config issue", "env problem", "deployment thing", "server stuff",
                "database issue", "network problem", "api error", "ui bug"
            ]) and len(desc_text) < 50:
                is_questionable = True
                self.questionable_categories["Cryptic Technical Jargon"].append((bug_id, title, description, url, created, activated))
                
            # Check for non-descriptive placeholders
            elif any(pattern in combined_text for pattern in [
                "needs fixing", "broken", "doesn't work", "not working", "issue with",
                "problem in", "error in", "bug in", "fix this", "update this"
            ]) and len(desc_text) < 30:
                is_questionable = True
                self.questionable_categories["Non-Descriptive Placeholders"].append((bug_id, title, description, url, created, activated))
                
            # Check for copy-paste artifacts or formatting issues
            elif any(pattern in combined_text for pattern in [
                "lorem ipsum", "test test", "xxx", "yyy", "zzz", "abc", "123",
                "temp", "temporary", "temp fix", "quick fix", "hack"
            ]):
                is_questionable = True
                self.questionable_categories["Copy-Paste Artifacts"].append((bug_id, title, description, url, created, activated))
                
            # Check for descriptions that are just repeating the title
            elif desc_text.lower() == title_text.lower():
                is_questionable = True
                self.questionable_categories["Duplicate Title/Description"].append((bug_id, title, description, url, created, activated))
                
            # Check for descriptions with mostly punctuation or special characters
            elif len([c for c in desc_text if c.isalnum()]) < len(desc_text) * 0.5 and len(desc_text) > 10:
                is_questionable = True
                self.questionable_categories["Special Characters Soup"].append((bug_id, title, description, url, created, activated))
                
            # Check for single word descriptions
            elif len(desc_text.split()) <= 2 and desc_text.lower() not in ["no description", "see title"]:
                is_questionable = True
                self.questionable_categories["Single Word Description"].append((bug_id, title, description, url, created, activated))
                
            if is_questionable:
                questionable_bugs.append((bug_id, title, description, url, created, activated))
            else:
                actionable_bugs_data.append((bug_id, title, description, url, created, activated))
        
        # Second pass: evaluate bot-created bugs for actionability
        if bot_created_bugs:
            if progress_callback:
                progress_callback(60, "Evaluating bot-created bugs...")
            
            for i, bug_tuple in enumerate(bot_created_bugs):
                bug_id, title, description, url, created, activated, created_by = bug_tuple
                
                if progress_callback:
                    progress_callback(
                        60 + int((i / len(bot_created_bugs)) * 25),
                        f"Evaluating bot bug {bug_id}..."
                    )
                
                is_actionable, test_results = self._evaluate_bot_bug_actionability(
                    bug_id, title, description, all_titles, progress_callback
                )
                
                if is_actionable:
                    # Keep as actionable
                    actionable_bugs_data.append((bug_id, title, description, url, created, activated))
                else:
                    # Mark as questionable
                    self.questionable_categories["Fake/Bot Created"].append((bug_id, title, description, url, created, activated))
                    questionable_bugs.append((bug_id, title, description, url, created, activated))
        
        # Third pass: group similar titles
        if progress_callback:
            progress_callback(85, "Grouping similar titles...")
            
        # Find groups with similar titles
        for pattern, bugs in questionable_by_title_pattern.items():
            if len(bugs) >= 3:  # Only group if 3+ bugs have similar titles
                for bug in bugs:
                    # Remove from other categories
                    for category_bugs in self.questionable_categories.values():
                        if bug in category_bugs and category_bugs != self.questionable_categories["Similar Titles Group"]:
                            category_bugs.remove(bug)
                    # Add to similar titles group
                    if bug not in self.questionable_categories["Similar Titles Group"]:
                        self.questionable_categories["Similar Titles Group"].append(bug)
        
        if progress_callback:
            progress_callback(100, "Analysis complete!")
        
        return questionable_bugs, actionable_bugs_data

    def generate_questionable_section(self, questionable_bugs, assigned_to_email):
        """Generate markdown for questionable bugs section"""
        md = []
        
        if not questionable_bugs:
            return md
            
        md.append("## ❓ Questionable Non-Actionable Bugs")
        md.append(f"**Total Count:** {len(questionable_bugs)} bugs with insufficient or problematic descriptions")
        md.append("**⚠️ Recommendation:** Review these first to clean up your backlog before focusing on actionable bugs.\n")
        
        # Display non-empty categories
        for category_name, bugs_in_category in self.questionable_categories.items():
            if bugs_in_category:
                md.append(f"### 🔸 {category_name} ({len(bugs_in_category)} bugs)")
                md.append(f"**Issue:** {self.category_explanations[category_name]}")
                
                # Special note for bot-created bugs
                if category_name == "Fake/Bot Created":
                    md.append("**Note:** These bot-created bugs failed the actionability test (lack clear remediation steps, have dead links, or non-unique titles)")
                
                # Create query links for this category
                bug_ids = [str(bug[0]) for bug in bugs_in_category]
                
                if len(bug_ids) <= BATCH_SIZE:
                    # Single query for small batches
                    wiql_query = f"""SELECT [System.Id], [System.Title], [System.State] 
FROM WorkItems 
WHERE [System.WorkItemType] = 'Bug' 
AND [System.AssignedTo] = '{assigned_to_email}' 
AND [System.State] = 'Active' 
AND [System.Id] IN ({','.join(bug_ids)})"""
                    
                    encoded_wiql = quote(wiql_query)
                    query_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems?_a=query&wiql={encoded_wiql}"
                    md.append(f"**[→ Review all {category_name} bugs]({query_url})**")
                else:
                    # Multiple queries for large batches
                    md.append(f"**Query links (batched due to size):**")
                    for i in range(0, len(bug_ids), BATCH_SIZE):
                        batch_ids = bug_ids[i:i + BATCH_SIZE]
                        batch_num = (i // BATCH_SIZE) + 1
                        
                        wiql_query = f"""SELECT [System.Id], [System.Title], [System.State] 
FROM WorkItems 
WHERE [System.WorkItemType] = 'Bug' 
AND [System.AssignedTo] = '{assigned_to_email}' 
AND [System.State] = 'Active' 
AND [System.Id] IN ({','.join(batch_ids)})"""
                        
                        encoded_wiql = quote(wiql_query)
                        query_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems?_a=query&wiql={encoded_wiql}"
                        md.append(f"  - [Batch {batch_num}]({query_url})")
                
                # Show a few examples
                md.append("\n**Examples:**")
                for bug_id, title, description, url, created, activated in bugs_in_category[:2]:
                    desc_preview = (description or "No description")[:80] + "..." if len(description or "") > 80 else (description or "No description")
                    md.append(f"- Bug {bug_id}: *\"{desc_preview}\"*")
                md.append("")
        
        md.append("**📋 Overall Recommended Actions:**")
        md.append("- **Immediate:** Close bugs with fake creators that fail actionability tests")
        md.append("- **Quick Win:** Add descriptions to minimal bugs or close if obsolete")
        md.append("- **Medium Term:** Request clarification for vague references and cryptic jargon")
        md.append("- **Best Practice:** Establish bug description standards to prevent future issues")
        md.append("")
        md.append("---")
        md.append("")
        
        return md