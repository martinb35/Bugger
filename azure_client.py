import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timezone
from config import ORG, PROJECT, USER_EMAIL, PERSONAL_ACCESS_TOKEN

class AzureDevOpsClient:
    def __init__(self):
        self.org = ORG
        self.project = PROJECT
        self.user_email = USER_EMAIL
        self.personal_access_token = PERSONAL_ACCESS_TOKEN

    def fetch_active_bugs(self):
        """Fetch active bugs assigned to the user"""
        wiql_query = {
            "query": f"""
                SELECT [System.Id]
                FROM WorkItems
                WHERE [System.WorkItemType] = 'Bug'
                AND [System.AssignedTo] = '{self.user_email}'
                AND [System.State] = 'Active'
            """
        }

        url = f"https://dev.azure.com/{self.org}/{self.project}/_apis/wit/wiql?api-version=7.0"
        response = requests.post(
            url,
            json=wiql_query,
            auth=HTTPBasicAuth('', self.personal_access_token)
        )
        response.raise_for_status()
        work_items = response.json().get("workItems", [])

        return work_items

    def fetch_bug_details(self, work_items):
        """Fetch detailed information for a list of work items"""
        if not work_items:
            return [], [], []

        def chunked(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        bugs_data = []
        created_dates = []
        activated_dates = []
        now = datetime.now(timezone.utc)

        for chunk in chunked(work_items, 200):
            ids = [str(item["id"]) for item in chunk]
            ids_str = ",".join(ids)
            details_url = (
                f"https://dev.azure.com/{self.org}/{self.project}/_apis/wit/workitems"
                f"?ids={ids_str}"
                f"&fields=System.Id,System.Title,System.State,System.CreatedDate,Microsoft.VSTS.Common.ActivatedDate,System.Description,Microsoft.VSTS.TCM.ReproSteps"
                f"&api-version=7.0"
            )
            details_response = requests.get(
                details_url,
                auth=HTTPBasicAuth('', self.personal_access_token)
            )
            details_response.raise_for_status()
            details = details_response.json().get("value", [])
            
            for bug in details:
                fields = bug["fields"]
                bug_id = bug["id"]
                title = fields.get("System.Title", "No Title")
                description = fields.get("System.Description", "")
                repro_steps = fields.get("Microsoft.VSTS.TCM.ReproSteps", "")
                
                # Combine description and repro steps for analysis
                full_description = f"{description}\n{repro_steps}".strip()
                
                url = f"https://dev.azure.com/{self.org}/{self.project}/_workitems/edit/{bug_id}"
                
                created = fields.get("System.CreatedDate")
                activated = fields.get("Microsoft.VSTS.Common.ActivatedDate")
                
                bugs_data.append((bug_id, title, full_description, url, created, activated))
                
                if created:
                    created_dates.append((bug_id, datetime.fromisoformat(created.rstrip("Z")).replace(tzinfo=timezone.utc)))
                if activated:
                    activated_dates.append((bug_id, datetime.fromisoformat(activated.rstrip("Z")).replace(tzinfo=timezone.utc)))

        return bugs_data, created_dates, activated_dates