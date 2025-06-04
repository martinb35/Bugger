// Bug analysis and categorization logic ported from Python
use crate::azure_devops::Bug;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QuestionableCategory {
    EmptyMinimalDescription,
    DeadLinks,
    SingleWordDescription,
    DuplicateTitleDescription,
    SpecialCharactersSoup,
}

#[derive(Debug, Clone)]
pub struct AnalysisResult {
    pub actionable: Vec<Bug>,
    pub questionable: Vec<(Bug, QuestionableCategory)>,
}

pub fn analyze_bugs(bugs: Vec<Bug>) -> AnalysisResult {
    let mut actionable = Vec::new();
    let mut questionable = Vec::new();
    for bug in bugs {
        if let Some(cat) = is_questionable(&bug) {
            questionable.push((bug, cat));
        } else {
            actionable.push(bug);
        }
    }
    AnalysisResult { actionable, questionable }
}

pub fn is_questionable(bug: &Bug) -> Option<QuestionableCategory> {
    let desc = bug.description.as_deref().unwrap_or("").trim();
    if desc.is_empty() {
        return Some(QuestionableCategory::EmptyMinimalDescription);
    }
    if desc.len() < 8 {
        return Some(QuestionableCategory::SingleWordDescription);
    }
    if desc.chars().all(|c| !c.is_alphanumeric()) {
        return Some(QuestionableCategory::SpecialCharactersSoup);
    }
    if desc == bug.title {
        return Some(QuestionableCategory::DuplicateTitleDescription);
    }
    if desc.contains("http") && desc.contains("404") {
        return Some(QuestionableCategory::DeadLinks);
    }
    None
}

// Categorization logic (simple keyword-based)
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum BugCategory {
    Crash,
    Performance,
    Security,
    FileSystem,
    Memory,
    Other,
}

pub fn categorize_bugs(bugs: &[Bug]) -> std::collections::HashMap<BugCategory, Vec<&Bug>> {
    use BugCategory::*;
    let mut map: std::collections::HashMap<BugCategory, Vec<&Bug>> = std::collections::HashMap::new();
    for bug in bugs {
        let text = format!("{} {}", bug.title, bug.description.as_deref().unwrap_or(""));
        let cat = if text.contains("crash") || text.contains("bsod") {
            Crash
        } else if text.contains("slow") || text.contains("hang") {
            Performance
        } else if text.contains("security") || text.contains("auth") {
            Security
        } else if text.contains("file") || text.contains("disk") {
            FileSystem
        } else if text.contains("memory") || text.contains("leak") {
            Memory
        } else {
            Other
        };
        map.entry(cat).or_default().push(bug);
    }
    map
}
