import requests
import base64
from datetime import datetime, timezone
from config import ORG, PROJECT, USER_EMAIL, AZURE_DEVOPS_PAT

class AzureDevOpsClient:
    def __init__(self):
        self.org = ORG
        self.project = PROJECT
        self.user_email = USER_EMAIL
        self.pat = AZURE_DEVOPS_PAT
        
        # Create authentication header
        auth_string = f":{self.pat}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
        
        self.base_url = f"https://dev.azure.com/{self.org}/{self.project}/_apis"

    def fetch_active_bugs(self):
        """Fetch active bugs assigned to the user"""
        wiql_query = f"""
        SELECT [System.Id]
        FROM WorkItems 
        WHERE [System.WorkItemType] = 'Bug' 
        AND [System.AssignedTo] = '{self.user_email}' 
        AND [System.State] = 'Active'
        """
        
        wiql_url = f"{self.base_url}/wit/wiql?api-version=7.0"
        
        try:
            response = requests.post(
                wiql_url,
                headers=self.headers,
                json={"query": wiql_query},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch bugs: {response.status_code} - {response.text}")
            
            result = response.json()
            work_items = result.get('workItems', [])
            
            return [item['id'] for item in work_items]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error fetching bugs: {str(e)}")

    def fetch_bug_details(self, work_item_ids):
        """Fetch detailed information for the given work item IDs"""
        if not work_item_ids:
            return [], [], []
        
        # Split into smaller batches to avoid URL length limits
        batch_size = 20
        all_bugs_data = []
        all_created_dates = []
        all_activated_dates = []
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            
            # Build URL for batch work item details
            ids_str = ','.join(map(str, batch_ids))
            fields = [
                'System.Id',
                'System.Title', 
                'System.Description',
                'System.CreatedDate',
                'Microsoft.VSTS.Common.ActivatedDate',
                'System.CreatedBy'
            ]
            fields_str = ','.join(fields)
            
            details_url = f"{self.base_url}/wit/workitems?ids={ids_str}&fields={fields_str}&api-version=7.0"
            
            try:
                response = requests.get(details_url, headers=self.headers, timeout=30)
                
                if response.status_code == 404:
                    # Some work items might not exist, try individual fetching
                    for work_item_id in batch_ids:
                        try:
                            single_url = f"{self.base_url}/wit/workitems/{work_item_id}?fields={fields_str}&api-version=7.0"
                            single_response = requests.get(single_url, headers=self.headers, timeout=10)
                            
                            if single_response.status_code == 200:
                                single_result = single_response.json()
                                bugs_data, created_dates, activated_dates = self._process_work_items([single_result])
                                all_bugs_data.extend(bugs_data)
                                all_created_dates.extend(created_dates)
                                all_activated_dates.extend(activated_dates)
                                
                        except Exception:
                            # Skip individual items that fail
                            continue
                    continue
                    
                elif response.status_code != 200:
                    raise Exception(f"Failed to fetch bug details: {response.status_code} - {response.text}")
                
                result = response.json()
                work_items = result.get('value', [])
                
                bugs_data, created_dates, activated_dates = self._process_work_items(work_items)
                all_bugs_data.extend(bugs_data)
                all_created_dates.extend(created_dates)
                all_activated_dates.extend(activated_dates)
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error fetching bug details: {str(e)}")
        
        return all_bugs_data, all_created_dates, all_activated_dates

    def _process_work_items(self, work_items):
        """Process work items and extract relevant data"""
        bugs_data = []
        created_dates = []
        activated_dates = []
        
        for item in work_items:
            bug_id = item['id']
            fields = item.get('fields', {})
            
            title = fields.get('System.Title', 'No Title')
            description = fields.get('System.Description', '')
            created_date_str = fields.get('System.CreatedDate')
            activated_date_str = fields.get('Microsoft.VSTS.Common.ActivatedDate')
            
            # Handle created by field
            created_by_field = fields.get('System.CreatedBy', {})
            if isinstance(created_by_field, dict):
                created_by = created_by_field.get('displayName', '')
            else:
                created_by = str(created_by_field) if created_by_field else ''
            
            # Parse dates
            created_date = None
            if created_date_str:
                try:
                    created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                    created_dates.append((bug_id, created_date))
                except ValueError:
                    pass
            
            activated_date = None
            if activated_date_str:
                try:
                    activated_date = datetime.fromisoformat(activated_date_str.replace('Z', '+00:00'))
                    activated_dates.append((bug_id, activated_date))
                except ValueError:
                    pass
            
            # Generate work item URL
            url = f"https://dev.azure.com/{self.org}/{self.project}/_workitems/edit/{bug_id}"
            
            bugs_data.append((bug_id, title, description, url, created_date, activated_date, created_by))
        
        return bugs_data, created_dates, activated_dates

    def get_project_info(self):
        """Fetch basic project info to test connectivity"""
        from config import API_VERSION
        url = f"https://dev.azure.com/{ORG}/_apis/projects/{PROJECT}?api-version={API_VERSION}"
        response = requests.get(url, auth=("", AZURE_DEVOPS_PAT))
        response.raise_for_status()
        return response.json()