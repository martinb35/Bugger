from urllib.parse import quote
from config import ORG, PROJECT, USER_EMAIL

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
            for bug_id, title, description, url, created, activated in bugs_data:
                text = f"{title} {description}".lower()
                if any(keyword in text for keyword in pattern_info["keywords"]):
                    matching_bugs.append((bug_id, title, description, url, created, activated))
            
            if matching_bugs:  # Only include buckets with bugs
                # Create a proper WIQL query with correct syntax
                keyword_conditions = []
                for kw in pattern_info["keywords"][:3]:  # Use top 3 keywords
                    keyword_conditions.append(f"[System.Title] Contains '{kw}'")
                    keyword_conditions.append(f"[System.Description] Contains '{kw}'")
                
                wiql = f"""SELECT [System.Id], [System.Title], [System.State] 
                          FROM WorkItems 
                          WHERE [System.WorkItemType] = 'Bug' 
                          AND [System.AssignedTo] = '{USER_EMAIL}' 
                          AND [System.State] = 'Active' 
                          AND ({' OR '.join(keyword_conditions)})"""
                
                # Properly encode the WIQL query for URL
                encoded_wiql = quote(wiql)
                query_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems?_a=query&wiql={encoded_wiql}"
                
                buckets[pattern_name] = {
                    "bugs": matching_bugs,
                    "explanation": pattern_info["explanation"],
                    "action": pattern_info["action"],
                    "query_url": query_url,
                    "count": len(matching_bugs)
                }
        
        return buckets