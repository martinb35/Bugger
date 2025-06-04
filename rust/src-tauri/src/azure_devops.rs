use base64::Engine; // Needed for .encode()
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde_json::Value;
use std::collections::HashMap;
use crate::AppConfig;

pub struct AzureDevOpsClient {
    pub config: AppConfig,
    client: Client,
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
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&pat).unwrap());
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        let body = serde_json::to_vec(&query).map_err(|e| format!("JSON serialize error: {}", e))?;
        let resp = self
            .client
            .post(&url)
            .headers(headers)
            .body(body)
            .send()
            .map_err(|e| format!("Request error: {}", e))?;
        let resp_text = resp.text().map_err(|e| format!("Response text error: {}", e))?;
        let json: Value = serde_json::from_str(&resp_text).map_err(|e| format!("JSON error: {}", e))?;
        let ids = json["workItems"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .filter_map(|item| item["id"].as_u64())
            .collect();
        Ok(ids)
    }

    pub fn fetch_bug_details(&self, ids: &[u64]) -> Result<(Vec<HashMap<String, Value>>, Vec<(u64, String)>, Vec<(u64, String)>), String> {
        if ids.is_empty() {
            return Ok((vec![], vec![], vec![]));
        }
        let ids_str = ids.iter().map(|id| id.to_string()).collect::<Vec<_>>().join(",");
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
                "System.ActivatedDate",
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
        let resp_text = resp.text().map_err(|e| format!("Response text error: {}", e))?;
        let json: Value = serde_json::from_str(&resp_text).map_err(|e| format!("JSON error: {}", e))?;
        let mut bugs_data = vec![];
        let mut created_dates = vec![];
        let mut activated_dates = vec![];
        if let Some(items) = json["value"].as_array() {
            for item in items {
                let mut bug = HashMap::new();
                if let Some(fields) = item["fields"].as_object() {
                    for (k, v) in fields {
                        bug.insert(k.clone(), v.clone());
                        if k == "System.CreatedDate" {
                            if let Some(id) = item["id"].as_u64() {
                                if let Some(date) = v.as_str() {
                                    created_dates.push((id, date.to_string()));
                                }
                            }
                        }
                        if k == "System.ActivatedDate" {
                            if let Some(id) = item["id"].as_u64() {
                                if let Some(date) = v.as_str() {
                                    activated_dates.push((id, date.to_string()));
                                }
                            }
                        }
                    }
                }
                bugs_data.push(bug);
            }
        }
        Ok((bugs_data, created_dates, activated_dates))
    }
}
