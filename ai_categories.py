AI_QUESTIONABLE_CATEGORIES = {
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

AI_CATEGORY_EXPLANATIONS = {
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