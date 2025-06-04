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

#[tauri::command]
fn fetch_and_analyze_bugs() -> Result<String, String> {
    println!("[Tauri backend] fetch_and_analyze_bugs called");
    let config = AppConfig::from_env()?;
    let client = AzureDevOpsClient::new(config);
    let ids = client.fetch_active_bugs()?;
    if ids.is_empty() {
        return Ok("<b>No active bugs assigned to you.</b>".to_string());
    }
    let bugs = client.fetch_bug_details(&ids)?;
    let mut html = String::from("<h2>Active Bugs</h2><ul>");
    for bug in bugs {
        html.push_str(&format!(
            "<li><b>#{}:</b> {}<br><small>State: {} | Created: {} | Activated: {}</small>",
            bug.id,
            html_escape::encode_text(&bug.title),
            html_escape::encode_text(&bug.state),
            bug.created_date.as_deref().unwrap_or("-"),
            bug.activated_date.as_deref().unwrap_or("-")
        ));
        if let Some(desc) = &bug.description {
            if !desc.trim().is_empty() {
                html.push_str(&format!(
                    "<br><details><summary>Description</summary><div style='white-space:pre-wrap'>{}</div></details>",
                    html_escape::encode_text(desc)
                ));
            }
        }
        html.push_str("</li>");
    }
    html.push_str("</ul>");
    Ok(html)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![fetch_and_analyze_bugs])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
