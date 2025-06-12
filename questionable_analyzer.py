import re
import requests
import time
from collections import defaultdict
from urllib.parse import quote
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE
from questionable_categories import QUESTIONABLE_CATEGORIES, CATEGORY_EXPLANATIONS
from questionable_utils import (
    is_real_person_name,
    extract_links_from_text,
    check_link_actionability,
    has_clear_remediation_steps,
    is_title_unique,
    evaluate_bot_bug_actionability,
    has_repro_steps,
)

class QuestionableAnalyzer:
    def __init__(self):
        # Use a copy to avoid shared state
        self.questionable_categories = {k: [] for k in QUESTIONABLE_CATEGORIES}
        self.category_explanations = CATEGORY_EXPLANATIONS

    def analyze_and_separate_bugs(self, bugs_data, progress_callback=None):
        questionable_bugs = []
        actionable_bugs_data = []
        questionable_by_title_pattern = defaultdict(list)
        bot_created_bugs = []

        total_bugs = len(bugs_data)
        all_titles = [bug[1] for bug in bugs_data]

        if progress_callback:
            progress_callback(0, "Starting bug analysis...")

        for i, bug_tuple in enumerate(bugs_data):
            if progress_callback:
                progress_callback(
                    int((i / total_bugs) * 60),
                    f"Analyzing bug {bug_tuple[0]}..."
                )

            if len(bug_tuple) == 6:
                bug_id, title, description, url, created, activated = bug_tuple
                created_by = "Unknown"
                repro_steps = ""
            elif len(bug_tuple) == 7:
                bug_id, title, description, url, created, activated, created_by = bug_tuple
                repro_steps = ""
            elif len(bug_tuple) == 8:
                bug_id, title, description, url, created, activated, created_by, repro_steps = bug_tuple
            else:
                bug_id, title, description, url, created, activated = bug_tuple
                created_by = "Unknown"
                repro_steps = ""

            desc_text = (description or "").strip()
            repro_steps_text = (repro_steps or "").strip()
            title_text = (title or "").strip()
            combined_text = f"{title_text} {desc_text} {repro_steps_text}".lower()

            is_questionable = False

            # Check if creator is a real person
            if not is_real_person_name(created_by):
                bot_created_bugs.append((bug_id, title, description, url, created, activated, created_by))
                continue

            # Check for empty or extremely minimal descriptions AND repro steps
            elif (len(desc_text) < 10 or not desc_text) and (len(repro_steps_text) < 10 or not repro_steps_text) and not has_repro_steps(desc_text + " " + repro_steps_text):
                is_questionable = True
                self.questionable_categories["Empty/Minimal Description"].append((bug_id, title, description, url, created, activated))
                title_pattern = re.sub(r'\d+', 'N', title_text)
                title_pattern = re.sub(r'[^\w\s]', '', title_pattern).strip()
                if title_pattern:
                    questionable_by_title_pattern[title_pattern].append((bug_id, title, description, url, created, activated))

            elif any(pattern in combined_text for pattern in [
                "see attachment", "see link", "see document", "refer to", "check the",
                "attached file", "linked document", "external reference"
            ]):
                is_questionable = True
                self.questionable_categories["Broken References"].append((bug_id, title, description, url, created, activated))

            elif any(pattern in combined_text for pattern in [
                "see above", "as mentioned", "per discussion", "like before", "same issue",
                "ditto", "idem", "^", "same as #", "duplicate of #",
                "internal ticket", "see jira", "check slack", "email thread",
                "meeting notes", "verbal request", "phone call"
            ]):
                is_questionable = True
                self.questionable_categories["Vague Internal References"].append((bug_id, title, description, url, created, activated))

            elif any(pattern in combined_text for pattern in [
                "config issue", "env problem", "deployment thing", "server stuff",
                "database issue", "network problem", "api error", "ui bug"
            ]) and len(desc_text) < 50:
                is_questionable = True
                self.questionable_categories["Cryptic Technical Jargon"].append((bug_id, title, description, url, created, activated))

            elif any(pattern in combined_text for pattern in [
                "needs fixing", "broken", "doesn't work", "not working", "issue with",
                "problem in", "error in", "bug in", "fix this", "update this"
            ]) and len(desc_text) < 30:
                is_questionable = True
                self.questionable_categories["Non-Descriptive Placeholders"].append((bug_id, title, description, url, created, activated))

            elif any(pattern in combined_text for pattern in [
                "lorem ipsum", "test test", "xxx", "yyy", "zzz", "abc", "123",
                "temp", "temporary", "temp fix", "quick fix", "hack"
            ]):
                is_questionable = True
                self.questionable_categories["Copy-Paste Artifacts"].append((bug_id, title, description, url, created, activated))

            elif desc_text.lower() == title_text.lower():
                is_questionable = True
                self.questionable_categories["Duplicate Title/Description"].append((bug_id, title, description, url, created, activated))

            elif len([c for c in desc_text if c.isalnum()]) < len(desc_text) * 0.5 and len(desc_text) > 10:
                is_questionable = True
                self.questionable_categories["Special Characters Soup"].append((bug_id, title, description, url, created, activated))

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

                is_actionable = evaluate_bot_bug_actionability(
                    bug_id, title, description, all_titles, progress_callback
                )

                if is_actionable:
                    actionable_bugs_data.append((bug_id, title, description, url, created, activated))
                else:
                    self.questionable_categories["Fake/Bot Created"].append((bug_id, title, description, url, created, activated))
                    questionable_bugs.append((bug_id, title, description, url, created, activated))

        # Third pass: group similar titles
        if progress_callback:
            progress_callback(85, "Grouping similar titles...")

        for pattern, bugs in questionable_by_title_pattern.items():
            if len(bugs) >= 3:
                for bug in bugs:
                    for category_bugs in self.questionable_categories.values():
                        if bug in category_bugs and category_bugs != self.questionable_categories["Similar Titles Group"]:
                            category_bugs.remove(bug)
                    if bug not in self.questionable_categories["Similar Titles Group"]:
                        self.questionable_categories["Similar Titles Group"].append(bug)

        if progress_callback:
            progress_callback(100, "Analysis complete!")

        return questionable_bugs, actionable_bugs_data

    def generate_questionable_section(self, questionable_bugs):
        md = []

        if not questionable_bugs:
            return md

        md.append("## ❓ Questionable Non-Actionable Bugs")
        md.append(f"**Total Count:** {len(questionable_bugs)} bugs with insufficient or problematic descriptions")
        md.append("**⚠️ Recommendation:** Review these first to clean up your backlog before focusing on actionable bugs.\n")

        for category_name, bugs_in_category in self.questionable_categories.items():
            if bugs_in_category:
                md.append(f"### 🔸 {category_name} ({len(bugs_in_category)} bugs)")
                md.append(f"**Issue:** {self.category_explanations[category_name]}")

                if category_name == "Fake/Bot Created":
                    md.append("**Note:** These bot-created bugs failed the actionability test (lack clear remediation steps, have dead links, or non-unique titles)")

                bug_ids = [str(bug[0]) for bug in bugs_in_category]

                if len(bug_ids) <= BATCH_SIZE:
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