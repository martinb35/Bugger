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

fn main() {
    tauri_app_lib::run()
}
