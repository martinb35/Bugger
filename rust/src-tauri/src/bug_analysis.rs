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
    Driver,
    Boot,
    UI,
    Network,
    Other,
}

pub fn categorize_bugs(bugs: &[Bug]) -> std::collections::HashMap<BugCategory, Vec<&Bug>> {
    use BugCategory::*;
    let mut map: std::collections::HashMap<BugCategory, Vec<&Bug>> = std::collections::HashMap::new();
    for bug in bugs {
        let text = format!("{} {}", bug.title.to_lowercase(), bug.description.as_deref().unwrap_or("").to_lowercase());
        let cat = if text.contains("crash") || text.contains("bsod") || text.contains("exception") || text.contains("fault") || text.contains("bugcheck") {
            Crash
        } else if text.contains("slow") || text.contains("hang") || text.contains("freeze") || text.contains("performance") || text.contains("timeout") || text.contains("unresponsive") {
            Performance
        } else if text.contains("security") || text.contains("permission") || text.contains("access") || text.contains("privilege") || text.contains("auth") || text.contains("token") {
            Security
        } else if text.contains("file") || text.contains("disk") || text.contains("storage") || text.contains("ntfs") || text.contains("fat32") || text.contains("corruption") {
            FileSystem
        } else if text.contains("memory") || text.contains("leak") || text.contains("heap") || text.contains("allocation") || text.contains("out of memory") || text.contains("oom") {
            Memory
        } else if text.contains("driver") || text.contains("device") || text.contains("hardware") || text.contains("pnp") || text.contains("plug and play") {
            Driver
        } else if text.contains("boot") || text.contains("startup") || text.contains("start") || text.contains("initialization") || text.contains("init") || text.contains("loading") {
            Boot
        } else if text.contains("ui") || text.contains("button") || text.contains("window") || text.contains("dialog") || text.contains("menu") || text.contains("screen") {
            UI
        } else if text.contains("network") || text.contains("connect") || text.contains("disconnect") || text.contains("timeout") || text.contains("tcp") || text.contains("udp") {
            Network
        } else {
            Other
        };
        map.entry(cat).or_default().push(bug);
    }
    map
}
