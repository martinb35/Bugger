QUESTIONABLE_CATEGORIES = {
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

CATEGORY_EXPLANATIONS = {
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