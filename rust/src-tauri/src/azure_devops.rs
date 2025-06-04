use base64::Engine; // Needed for .encode()
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde_json::Value;
use crate::AppConfig;

pub struct AzureDevOpsClient {
    pub config: AppConfig,
    client: Client,
}

#[derive(Debug, Clone)]
pub struct Bug {
    pub id: u64,
    pub title: String,
    pub state: String,
    pub created_date: Option<String>,
    pub description: Option<String>,
}

impl AzureDevOpsClient {
    pub fn new(config: AppConfig) -> Self {
        AzureDevOpsClient {
            config,
            client: Client::new(),
        }
    }

    pub fn fetch_active_bugs(&self) -> Result<Vec<u64>, String> {
        let url = format!(
            "https://dev.azure.com/{}/{}/_apis/wit/wiql?api-version=7.0",
            self.config.org, self.config.project
        );
        let query = serde_json::json!({
            "query": format!(
                "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' AND [System.State] <> 'Closed' AND [System.AssignedTo] = '{}' ORDER BY [System.CreatedDate] DESC",
                self.config.user_email
            )
        });
        let mut headers = HeaderMap::new();
        let pat = format!("Basic {}", base64::engine::general_purpose::STANDARD.encode(format!(":{}", self.config.azure_devops_pat)));
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&pat).map_err(|e| format!("Invalid header value: {}", e))?);
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        let body = serde_json::to_vec(&query).map_err(|e| format!("JSON serialize error: {}", e))?;
        let resp = self
            .client
            .post(&url)
            .headers(headers)
            .body(body)
            .send()
            .map_err(|e| format!("Request error: {}", e))?;
        let status = resp.status();
        let resp_text = resp.text().map_err(|e| format!("Response text error: {}", e))?;
        if !status.is_success() {
            println!("Azure DevOps API error ({}): {}", status, resp_text);
            return Err(format!("Azure DevOps API error ({}): {}", status, resp_text));
        }
        let json: Value = serde_json::from_str(&resp_text).map_err(|e| format!("JSON error: {}\nRaw response: {}", e, resp_text))?;
        let ids = json["workItems"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .filter_map(|item| item["id"].as_u64())
            .collect();
        Ok(ids)
    }

    pub fn fetch_bug_details(&self, ids: &[u64]) -> Result<Vec<Bug>, String> {
        if ids.is_empty() {
            return Ok(vec![]);
        }
        let url = format!(
            "https://dev.azure.com/{}/{}/_apis/wit/workitemsbatch?api-version=7.0",
            self.config.org, self.config.project
        );
        let body_json = serde_json::json!({
            "ids": ids,
            "fields": [
                "System.Id",
                "System.Title",
                "System.State",
                "System.CreatedDate",
                "System.Description"
            ]
        });
        let mut headers = HeaderMap::new();
        let pat = format!("Basic {}", base64::engine::general_purpose::STANDARD.encode(format!(":{}", self.config.azure_devops_pat)));
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&pat).unwrap());
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        let body = serde_json::to_vec(&body_json).map_err(|e| format!("JSON serialize error: {}", e))?;
        let resp = self
            .client
            .post(&url)
            .headers(headers)
            .body(body)
            .send()
            .map_err(|e| format!("Request error: {}", e))?;
        let status = resp.status();
        let resp_text = resp.text().map_err(|e| format!("Response text error: {}", e))?;
        if !status.is_success() {
            println!("Azure DevOps API error ({}): {}", status, resp_text);
            return Err(format!("Azure DevOps API error ({}): {}", status, resp_text));
        }
        let json: Value = serde_json::from_str(&resp_text).map_err(|e| format!("JSON error: {}\nRaw response: {}", e, resp_text))?;
        let mut bugs = vec![];
        if let Some(items) = json["value"].as_array() {
            for item in items {
                let fields = item["fields"].as_object();
                if let Some(id) = item["id"].as_u64() {
                    let title = fields.and_then(|f| f.get("System.Title")).and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let state = fields.and_then(|f| f.get("System.State")).and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let created_date = fields.and_then(|f| f.get("System.CreatedDate")).and_then(|v| v.as_str()).map(|s| s.to_string());
                    let description = fields.and_then(|f| f.get("System.Description")).and_then(|v| v.as_str()).map(|s| s.to_string());
                    bugs.push(Bug {
                        id,
                        title,
                        state,
                        created_date,
                        description,
                    });
                } else {
                    println!("Warning: Missing or invalid bug ID in response item: {:?}", item);
                }
            }
        }
        Ok(bugs)
    }
}
