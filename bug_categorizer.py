from urllib.parse import quote
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE

class BugCategorizer:
    """Categorize actionable bugs into meaningful buckets"""
    
    def __init__(self):
        # Common Windows/OS patterns
        self.patterns = {
            "BSoD/Crashes": {
                "keywords": ["bsod", "blue screen", "crash", "exception", "fault", "bugcheck", "stop error"],
                "explanation": "System crashes and blue screen errors that require immediate investigation",
                "action": "Analyze crash dumps, check driver compatibility, and review recent system changes"
            },
            "Boot/Startup": {
                "keywords": ["boot", "startup", "start", "initialization", "init", "loading"],
                "explanation": "Issues preventing system or application startup",
                "action": "Check boot configuration, startup dependencies, and initialization sequences"
            },
            "Performance/Hangs": {
                "keywords": ["slow", "hang", "freeze", "performance", "timeout", "unresponsive"],
                "explanation": "Performance degradation and system responsiveness issues",
                "action": "Profile performance bottlenecks, check resource usage, and optimize critical paths"
            },
            "Driver Issues": {
                "keywords": ["driver", "device", "hardware", "pnp", "plug and play"],
                "explanation": "Hardware driver compatibility and device management problems",
                "action": "Update drivers, check hardware compatibility, and review device manager errors"
            },
            "Memory Issues": {
                "keywords": ["memory", "leak", "heap", "allocation", "out of memory", "oom"],
                "explanation": "Memory management problems including leaks and allocation failures",
                "action": "Run memory analysis tools, check for leaks, and optimize memory usage"
            },
            "Security/Access": {
                "keywords": ["security", "permission", "access", "privilege", "auth", "token"],
                "explanation": "Security vulnerabilities and access control issues",
                "action": "Review security policies, check permissions, and audit access controls"
            },
            "File System": {
                "keywords": ["file", "disk", "storage", "ntfs", "fat32", "corruption"],
                "explanation": "File system corruption and storage-related problems",
                "action": "Run disk checks, verify file system integrity, and check storage health"
            }
        }

    def extract_meaningful_buckets(self, bugs_data):
        """Group bugs by meaningful patterns and create queries for each bucket"""
        buckets = {}
        
        # Group bugs by patterns
        for pattern_name, pattern_info in self.patterns.items():
            matching_bugs = []
            matching_bug_ids = []
            
            for bug_id, title, description, url, created, activated in bugs_data:
                text = f"{title} {description}".lower()
                if any(keyword in text for keyword in pattern_info["keywords"]):
                    matching_bugs.append((bug_id, title, description, url, created, activated))
                    matching_bug_ids.append(str(bug_id))
            
            if matching_bugs:  # Only include buckets with bugs
                # Create query URLs using specific bug IDs instead of keywords
                query_urls = self._create_query_urls_for_bugs(matching_bug_ids, pattern_name)
                
                buckets[pattern_name] = {
                    "bugs": matching_bugs,
                    "bug_ids": matching_bug_ids,
                    "explanation": pattern_info["explanation"],
                    "action": pattern_info["action"],
                    "query_urls": query_urls,  # Now this is a list of URLs
                    "count": len(matching_bugs)
                }
        
        return buckets
    
    def _create_query_urls_for_bugs(self, bug_ids, category_name):
        """Create Azure DevOps query URLs for a list of bug IDs"""
        query_urls = []
        
        if len(bug_ids) <= BATCH_SIZE:
            # Single query for small batches
            wiql_query = f"""SELECT [System.Id], [System.Title], [System.State] 
FROM WorkItems 
WHERE [System.WorkItemType] = 'Bug' 
AND [System.AssignedTo] = '{USER_EMAIL}' 
AND [System.State] = 'Active' 
AND [System.Id] IN ({','.join(bug_ids)})"""
            
            encoded_wiql = quote(wiql_query)
            query_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems?_a=query&wiql={encoded_wiql}"
            query_urls.append({
                'url': query_url,
                'label': f"View all {category_name} bugs"
            })
        else:
            # Multiple queries for large batches
            for i in range(0, len(bug_ids), BATCH_SIZE):
                batch_ids = bug_ids[i:i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                
                wiql_query = f"""SELECT [System.Id], [System.Title], [System.State] 
FROM WorkItems 
WHERE [System.WorkItemType] = 'Bug' 
AND [System.AssignedTo] = '{USER_EMAIL}' 
AND [System.State] = 'Active' 
AND [System.Id] IN ({','.join(batch_ids)})"""
                
                encoded_wiql = quote(wiql_query)
                query_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems?_a=query&wiql={encoded_wiql}"
                query_urls.append({
                    'url': query_url,
                    'label': f"Batch {batch_num} ({len(batch_ids)} bugs)"
                })
        
        return query_urls