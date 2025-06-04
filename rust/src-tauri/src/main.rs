// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;

fn load_env() {
    // Load .env file if present
    let _ = dotenvy::dotenv();
}

pub struct AppConfig {
    pub org: String,
    pub project: String,
    pub user_email: String,
    pub azure_devops_pat: String,
    pub openai_api_key: Option<String>,
    pub ai_enabled: bool,
}

impl AppConfig {
    pub fn from_env() -> Result<Self, String> {
        load_env();
        let org = env::var("AZURE_DEVOPS_ORG").map_err(|_| "Missing AZURE_DEVOPS_ORG")?;
        let project = env::var("AZURE_DEVOPS_PROJECT").map_err(|_| "Missing AZURE_DEVOPS_PROJECT")?;
        let user_email = env::var("AZURE_DEVOPS_USER_EMAIL").map_err(|_| "Missing AZURE_DEVOPS_USER_EMAIL")?;
        let azure_devops_pat = env::var("AZURE_DEVOPS_PAT").map_err(|_| "Missing AZURE_DEVOPS_PAT")?;
        let openai_api_key = env::var("OPENAI_API_KEY").ok();
        let ai_enabled = openai_api_key.is_some();
        Ok(AppConfig {
            org,
            project,
            user_email,
            azure_devops_pat,
            openai_api_key,
            ai_enabled,
        })
    }
}

mod azure_devops;
use azure_devops::AzureDevOpsClient;
mod bug_analysis;
use bug_analysis::{analyze_bugs, categorize_bugs};

#[tauri::command]
fn fetch_and_analyze_bugs() -> Result<String, String> {
    println!("[Tauri backend] fetch_and_analyze_bugs called");
    let config = AppConfig::from_env()?;
    let client = AzureDevOpsClient::new(config);
    let ids = client.fetch_active_bugs()?;
    if ids.is_empty() {
        return Ok("<b>No active bugs assigned to you.</b>".to_string());
    }
    let all_bugs = client.fetch_bug_details(&ids)?;
    println!("[Tauri backend] Found {} bugs", all_bugs.len());
    let analysis = analyze_bugs(all_bugs);
    let actionable = &analysis.actionable;
    let questionable = &analysis.questionable;
    let categorized = categorize_bugs(actionable);
    // Generate HTML report
    let mut html = String::new();
    html.push_str("<h2>📈 Bug Stats</h2><ul>");
    html.push_str(&format!("<li><b>Total active bugs:</b> {}</li>", actionable.len() + questionable.len()));
    html.push_str(&format!("<li><b>Actionable bugs:</b> {}</li>", actionable.len()));
    html.push_str(&format!("<li><b>Questionable bugs:</b> {}</li>", questionable.len()));
    html.push_str("</ul>");
    if !questionable.is_empty() {
        html.push_str("<details open><summary>❓ Questionable Non-Actionable Bugs</summary><div class='warning'>Review these first to clean up your backlog before focusing on actionable bugs.</div><ul>");
        for (bug, cat) in questionable {
            html.push_str(&format!(
                "<li><b>#{}:</b> {}<br><span class='category-Other'><small>Reason: {:?}</small></span></li>",
                bug.id,
                html_escape::encode_text(&bug.title), // only escape user content
                cat // do not escape HTML tags
            ));
        }
        html.push_str("</ul></details>");
    }
    html.push_str("<h2>🗂️ Actionable Bug Categories</h2>");
    for (cat, bugs) in &categorized {
        let cat_class = format!("category-{:?}", cat);
        html.push_str(&format!("<details><summary><span class='{}'>{:?} ({})</span></summary><ul>", cat_class, cat, bugs.len()));
        for bug in bugs.iter() {
            html.push_str(&format!(
                "<li><b>#{}:</b> {}<br><small>State: {} | Created: {}</small>",
                bug.id,
                html_escape::encode_text(&bug.title), // only escape user content
                html_escape::encode_text(&bug.state),
                bug.created_date.as_deref().unwrap_or("-")
            ));
            if let Some(desc) = &bug.description {
                if !desc.trim().is_empty() {
                    html.push_str(&format!(
                        "<br><details><summary>Description</summary><div style='white-space:pre-wrap'>{}</div></details>",
                        desc // DO NOT escape here, allow HTML/markdown in bug descriptions
                    ));
                }
            }
            html.push_str("</li>");
        }
        html.push_str("</ul></details>");
    }
    Ok(html)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![fetch_and_analyze_bugs])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
