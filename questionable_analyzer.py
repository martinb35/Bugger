import re
from collections import defaultdict
from urllib.parse import quote
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE

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
            "Similar Titles Group": []
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
            "Similar Titles Group": "Multiple bugs with nearly identical titles - likely duplicates or related issues that should be consolidated"
        }

    def analyze_and_separate_bugs(self, bugs_data):
        """Analyze bugs and separate into questionable and actionable categories"""
        questionable_bugs = []
        actionable_bugs_data = []
        questionable_by_title_pattern = defaultdict(list)
        
        # First pass: identify questionable bugs
        for bug_id, title, description, url, created, activated in bugs_data:
            desc_text = (description or "").strip()
            title_text = (title or "").strip()
            combined_text = f"{title_text} {desc_text}".lower()
            
            is_questionable = False
            
            # Check for empty or extremely minimal descriptions
            if len(desc_text) < 10 or not desc_text:
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
            ]):
                is_questionable = True
                self.questionable_categories["Cryptic Technical Jargon"].append((bug_id, title, description, url, created, activated))
                
            # Check for non-descriptive placeholders
            elif any(pattern in combined_text for pattern in [
                "needs fixing", "broken", "doesn't work", "not working", "issue with",
                "problem in", "error in", "bug in", "fix this", "update this"
            ]):
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
            elif len([c for c in desc_text if c.isalnum()]) < len(desc_text) * 0.5:
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
        
        # Second pass: find groups with similar titles
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
        
        return questionable_bugs, actionable_bugs_data

    def generate_questionable_section(self, questionable_bugs):
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
                
                # Create query links for this category
                bug_ids = [str(bug[0]) for bug in bugs_in_category]
                
                if len(bug_ids) <= BATCH_SIZE:
                    # Single query for small batches
                    wiql_query = f"""SELECT [System.Id], [System.Title], [System.State] 
FROM WorkItems 
WHERE [System.WorkItemType] = 'Bug' 
AND [System.AssignedTo] = '{USER_EMAIL}' 
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
AND [System.AssignedTo] = '{USER_EMAIL}' 
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
        md.append("- **Immediate:** Close bugs with broken references or copy-paste artifacts")
        md.append("- **Quick Win:** Add descriptions to empty/minimal bugs or close if obsolete")
        md.append("- **Medium Term:** Request clarification for vague references and cryptic jargon")
        md.append("- **Best Practice:** Establish bug description standards to prevent future issues")
        md.append("")
        md.append("---")
        md.append("")
        
        return md