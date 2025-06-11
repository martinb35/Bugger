import re
import requests
import time
from collections import defaultdict
from urllib.parse import quote
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE, AZURE_DEVOPS_PAT

class AIBugAnalyzer:
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
            "Non-Actionable Bot Created": [],
            "Dead Links": []
        }
        
        self.category_explanations = {
            "Empty/Minimal Description": "Bugs with no description or insufficient detail to understand the issue",
            "Broken References": "Bugs pointing to missing attachments, links, or documents",
            "Vague Internal References": "Bugs referencing discussions, emails, or meetings without context",
            "Cryptic Technical Jargon": "Bugs with generic technical terms that don't explain the actual problem",
            "Non-Descriptive Placeholders": "Bugs with placeholder text that doesn't explain what's broken",
            "Copy-Paste Artifacts": "Bugs with test data, Lorem Ipsum, or temporary content",
            "Duplicate Title/Description": "Bugs where description just repeats the title without adding details",
            "Special Characters Soup": "Bugs with descriptions full of special characters and no meaningful text",
            "Single Word Description": "Bugs with only 1-2 word descriptions that provide no context",
            "Similar Titles Group": "Multiple bugs with nearly identical titles - likely duplicates",
            "Non-Actionable Bot Created": "Bot-created bugs that fail the actionability test",
            "Dead Links": "Bugs with broken or inaccessible links"
        }

    def _call_ai_api(self, prompt, max_tokens=150):
        """Call GPT-4o API to evaluate bug actionability"""
        try:
            import openai
            
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Updated to GPT-4o
                messages=[
                    {"role": "system", "content": "You are a bug triage expert. Analyze bug reports for actionability."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1  # Low temperature for consistent results
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            return "AI_UNAVAILABLE: OpenAI package not installed"
        except Exception as e:
            # Fallback to basic heuristics if AI fails
            return f"AI_ERROR: {str(e)[:50]}"

    def _is_real_person_name(self, created_by):
        """AI-enhanced check if the bug creator appears to be a real person"""
        if not created_by:
            return False
            
        prompt = f"""
        Analyze this name/username to determine if it appears to be a real person or an automated system/bot:
        
        Name: "{created_by}"
        
        Consider:
        - Bot indicators (bot, system, auto, service, script, automation, test, dummy, fake, admin, api, webhook, deploy)
        - Generic patterns (user123, test, admin123, temp)
        - Real name patterns (first/last name combinations, reasonable email addresses)
        
        Respond with only: "REAL_PERSON" or "BOT_SYSTEM"
        """
        
        result = self._call_ai_api(prompt, max_tokens=10)
        
        # Fallback to heuristics if AI is unavailable
        if "AI_UNAVAILABLE" in result or "AI_ERROR" in result:
            return self._fallback_person_check(created_by)
        
        return "REAL_PERSON" in result

    def _fallback_person_check(self, created_by):
        """Fallback heuristic check for real person names"""
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
        ]
        
        if any(re.match(pattern, name) for pattern in generic_patterns):
            return False
            
        # Should have reasonable length
        return len(name) > 3

    def _evaluate_bug_actionability(self, title, description, created_by):
        """GPT-4o powered evaluation of bug actionability"""
        
        prompt = f"""
        Evaluate this bug report for actionability. A bug is actionable if someone can understand the problem and take concrete steps to fix it.

        Title: "{title}"
        Description: "{description}"
        Created by: "{created_by}"

        Evaluate based on these criteria:
        1. Clear problem description (not just "doesn't work" or "broken")
        2. Sufficient detail to understand the issue
        3. No broken references to missing attachments/links
        4. Not just placeholder text or test data
        5. Contains specific information, not vague references
        6. For bot-created bugs: must have clear remediation steps

        Categorize as one of:
        - ACTIONABLE: Bug has sufficient detail and clear problem description
        - EMPTY_DESCRIPTION: No description or minimal detail (less than 10 meaningful characters)
        - BROKEN_REFERENCES: References missing attachments, links, or documents
        - VAGUE_REFERENCES: References internal discussions, emails, meetings without context
        - CRYPTIC_JARGON: Generic technical terms without explaining the actual problem
        - PLACEHOLDER_TEXT: Placeholder text like "needs fixing" without explanation
        - COPY_PASTE_ARTIFACTS: Test data, Lorem Ipsum, or temporary content
        - DUPLICATE_TITLE_DESC: Description just repeats the title
        - SPECIAL_CHARACTERS: Mostly special characters, no meaningful text
        - SINGLE_WORD: Only 1-2 words that provide no context
        - NON_ACTIONABLE_BOT: Bot-created without clear remediation steps

        Respond with only the category name.
        """
        
        result = self._call_ai_api(prompt, max_tokens=50)
        
        # Fallback to heuristics if AI is unavailable
        if "AI_UNAVAILABLE" in result or "AI_ERROR" in result:
            return self._fallback_actionability_check(title, description)
        
        return result.strip()

    def _fallback_actionability_check(self, title, description):
        """Fallback heuristic actionability check"""
        desc_text = (description or "").strip()
        
        if len(desc_text) < 10:
            return "EMPTY_DESCRIPTION"
        elif desc_text.lower() == (title or "").lower():
            return "DUPLICATE_TITLE_DESC"
        elif len(desc_text.split()) <= 2:
            return "SINGLE_WORD"
        else:
            return "ACTIONABLE"

    def _check_for_dead_links(self, description):
        """Extract and check links for accessibility"""
        if not description:
            return []
            
        # Extract URLs
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, description)
        
        # Extract Azure DevOps work item references
        workitem_pattern = r'#(\d+)'
        workitem_refs = re.findall(workitem_pattern, description)
        
        # Convert work item refs to URLs
        for ref in workitem_refs:
            urls.append(f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/{ref}")
        
        dead_links = []
        for url in urls:
            try:
                headers = {'User-Agent': 'Bugger-Analysis-Tool/1.0'}
                
                # Add Azure DevOps authentication for Azure DevOps URLs
                if 'dev.azure.com' in url or 'visualstudio.com' in url:
                    import base64
                    auth_string = f":{AZURE_DEVOPS_PAT}"
                    auth_bytes = auth_string.encode('ascii')
                    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                    headers['Authorization'] = f'Basic {auth_b64}'
                
                response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
                
                if response.status_code == 404:
                    dead_links.append(url)
                    
            except:
                dead_links.append(url)  # Consider inaccessible links as dead
                
            time.sleep(0.2)  # Rate limiting
                
        return dead_links

    def _group_similar_titles(self, bugs_by_category):
        """GPT-4o powered grouping of bugs with priority for cryptic and similar titles"""
        all_bugs = []
        for category_bugs in bugs_by_category.values():
            all_bugs.extend(category_bugs)

        if len(all_bugs) < 3:
            return []

        # Extract titles for AI analysis
        titles = [bug[1] for bug in all_bugs]

        prompt = f"""
        Analyze these bug titles to prioritize grouping of bugs with very similar and cryptic titles:

        {chr(10).join([f"{i}: {title}" for i, title in enumerate(titles)])}

        Look for:
        - Titles that are nearly identical with cryptic technical jargon or placeholders.
        - Same core issue described differently but with similar cryptic patterns.
        - Clear duplicates that should be consolidated into specific groups.

        Respond with groups in this format:
        GROUP1: 0,1,2
        GROUP2: 5,7,9

        Only include groups with 3+ items. If no groups found, respond with: NONE
        """

        result = self._call_ai_api(prompt, max_tokens=200)

        # Fallback to heuristic grouping if AI unavailable
        if "AI_UNAVAILABLE" in result or "AI_ERROR" in result:
            return self._fallback_title_grouping(all_bugs)

        similar_groups = []
        if "NONE" not in result:
            lines = result.strip().split('\n')
            for line in lines:
                if 'GROUP' in line and ':' in line:
                    try:
                        indices_str = line.split(':')[1].strip()
                        indices = [int(x.strip()) for x in indices_str.split(',')]
                        if len(indices) >= 3:
                            group_bugs = [all_bugs[i] for i in indices if i < len(all_bugs)]
                            similar_groups.extend(group_bugs)
                    except:
                        continue

        return similar_groups

    def analyze_and_separate_bugs(self, bugs_data, progress_callback=None):
        """GPT-4o powered analysis to separate questionable and actionable bugs"""
        questionable_bugs = []
        actionable_bugs_data = []
        
        total_bugs = len(bugs_data)
        
        if progress_callback:
            progress_callback(0, "Starting GPT-4o powered bug analysis...")
        
        # Reset categories
        for category in self.questionable_categories:
            self.questionable_categories[category] = []
        
        # Analyze each bug with GPT-4o
        for i, bug_tuple in enumerate(bugs_data):
            if progress_callback:
                progress_callback(
                    int((i / total_bugs) * 80),
                    f"GPT-4o analyzing bug {bug_tuple[0]}..."
                )
            
            # Handle different tuple lengths for backward compatibility
            if len(bug_tuple) == 6:
                bug_id, title, description, url, created, activated = bug_tuple
                created_by = "Unknown"
            else:
                bug_id, title, description, url, created, activated, created_by = bug_tuple
            
            # GPT-4o evaluation
            category = self._evaluate_bug_actionability(title, description or "", created_by or "")
            
            bug_data = (bug_id, title, description, url, created, activated)
            
            if category == "ACTIONABLE":
                # Check for dead links even in actionable bugs
                dead_links = self._check_for_dead_links(description)
                if dead_links:
                    self.questionable_categories["Dead Links"].append(bug_data)
                    questionable_bugs.append(bug_data)
                else:
                    actionable_bugs_data.append(bug_data)
            else:
                # Map AI categories to our category system
                category_mapping = {
                    "EMPTY_DESCRIPTION": "Empty/Minimal Description",
                    "BROKEN_REFERENCES": "Broken References", 
                    "VAGUE_REFERENCES": "Vague Internal References",
                    "CRYPTIC_JARGON": "Cryptic Technical Jargon",
                    "PLACEHOLDER_TEXT": "Non-Descriptive Placeholders",
                    "COPY_PASTE_ARTIFACTS": "Copy-Paste Artifacts",
                    "DUPLICATE_TITLE_DESC": "Duplicate Title/Description",
                    "SPECIAL_CHARACTERS": "Special Characters Soup",
                    "SINGLE_WORD": "Single Word Description",
                    "NON_ACTIONABLE_BOT": "Non-Actionable Bot Created"
                }
                
                mapped_category = category_mapping.get(category, "Empty/Minimal Description")
                self.questionable_categories[mapped_category].append(bug_data)
                questionable_bugs.append(bug_data)
        
        # GPT-4o powered similar title grouping
        if progress_callback:
            progress_callback(80, "GPT-4o grouping similar titles...")
            
        similar_bugs = self._group_similar_titles(self.questionable_categories)
        if similar_bugs:
            # Remove from other categories and add to similar group
            for bug in similar_bugs:
                for category_bugs in self.questionable_categories.values():
                    if bug in category_bugs and category_bugs != self.questionable_categories["Similar Titles Group"]:
                        category_bugs.remove(bug)
                
                if bug not in self.questionable_categories["Similar Titles Group"]:
                    self.questionable_categories["Similar Titles Group"].append(bug)
        
        if progress_callback:
            progress_callback(100, "GPT-4o analysis complete!")
        
        return questionable_bugs, actionable_bugs_data

    def generate_questionable_section(self, questionable_bugs, assigned_to_email):
        """Generate markdown for questionable bugs section with detailed explanations"""
        md = []

        if not questionable_bugs:
            return md

        md.append("## ❓ GPT-4o Detected Non-Actionable Bugs")
        md.append(f"**Total Count:** {len(questionable_bugs)} bugs flagged by GPT-4o as non-actionable")
        md.append("**⚠️ Recommendation:** GPT-4o has identified these bugs as lacking sufficient detail or having issues that prevent immediate action.")

        # Display non-empty categories with detailed explanations
        for category_name, bugs_in_category in self.questionable_categories.items():
            if bugs_in_category:
                md.append(f"### 🤖 {category_name} ({len(bugs_in_category)} bugs)")
                md.append(f"**GPT-4o Assessment:** {self.category_explanations[category_name]}")
                md.append("**Detailed Explanation:** These bugs lack specific details that would allow the receiver to act upon them effectively. For example:")
                md.append("- Missing clear problem descriptions, making it unclear what needs to be fixed.")
                md.append("- References to missing attachments or links that are crucial for understanding the issue.")
                md.append("- Placeholder text or test data that does not provide actionable information.")
                md.append("- Vague references to internal discussions or emails without context.")

                # Create query links for this category
                bug_ids = [str(bug[0]) for bug in bugs_in_category]

                if len(bug_ids) <= BATCH_SIZE:
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

                # Show examples with detailed previews
                md.append("\n**Examples:**")
                for bug_id, title, description, url, created, activated in bugs_in_category[:2]:
                    desc_preview = (description or "No description")[:80] + "..." if len(description or "") > 80 else (description or "No description")
                    md.append(f"- Bug {bug_id}: *\"{desc_preview}\"* - This bug lacks actionable details such as clear steps to reproduce or specific error messages.")
                md.append("")

        md.append("**🤖 GPT-4o Recommended Actions:**")
        md.append("- **High Confidence:** GPT-4o flagged bugs can likely be closed or require clarification")
        md.append("- **Quick Wins:** Empty descriptions and placeholder text bugs")
        md.append("- **Review Required:** Verify GPT-4o assessments for complex technical bugs")
        md.append("- **Process Improvement:** Use GPT-4o insights to improve bug reporting standards")
        md.append("")
        md.append("---")
        md.append("")

        return md

    def _fallback_title_grouping(self, all_bugs):
        """Fallback heuristic title grouping"""
        # Simple heuristic - group by normalized titles
        title_groups = defaultdict(list)

        for bug in all_bugs:
            title = bug[1] or ""
            # Normalize title
            normalized = re.sub(r'\d+', 'N', title.lower())
            normalized = re.sub(r'[^\w\s]', ' ', normalized)
            normalized = ' '.join(normalized.split())

            title_groups[normalized].append(bug)

        # Return bugs from groups with 2+ items
        similar_bugs = []
        for group_bugs in title_groups.values():
            if len(group_bugs) >= 2:
                similar_bugs.extend(group_bugs)

        return similar_bugs