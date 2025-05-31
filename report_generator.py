from urllib.parse import quote
from datetime import datetime, timezone
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE

class ReportGenerator:
    def __init__(self, analyzer, categorizer):
        self.analyzer = analyzer
        self.categorizer = categorizer

    def generate_report(self, bugs_data, created_dates, activated_dates):
        """Generate the markdown report for the bugs"""
        md = []
        
        # First, analyze the bugs to get stats
        avg_age_days, avg_active_days = self.analyzer.analyze_bugs(bugs_data)
        
        # Then, categorize the bugs into meaningful buckets
        buckets = self.categorizer.extract_meaningful_buckets(bugs_data)
        
        # Sort buckets by count (largest first)
        sorted_buckets = sorted(buckets.items(), key=lambda x: x[1]["count"], reverse=True)

        # BUG STATS SECTION
        total_bugs = len(bugs_data)
        md.append("## 🐞 Bug Stats")
        md.append(f"- **Total active bugs:** {total_bugs}")
        md.append(f"- **Average bug age:** {avg_age_days:.1f} days")
        md.append(f"- **Average length of being active:** {avg_active_days:.1f} days\n")

        # ACTIONABLE BUG ANALYSIS SECTION
        if sorted_buckets:
            md.append("## 📊 Actionable Bug Analysis by Issue Type")
            
            for bucket_name, bucket_info in sorted_buckets:
                md.append(f"### {bucket_info['count']} bugs likely related to: {bucket_name}")
                md.append(f"**What these bugs are about:** {bucket_info['explanation']}")
                md.append(f"**Recommended next steps:** {bucket_info['action']}")
                md.append(f"**[→ View all {bucket_name} bugs in Azure DevOps]({bucket_info['query_url']})**")
                
                # Show sample bugs
                md.append("\n**Sample bugs:**")
                for bug_id, title, description, url, created, activated in bucket_info['bugs'][:3]:
                    md.append(f"- [{title}]({url})")
                
                if bucket_info['count'] > 3:
                    md.append(f"...and {bucket_info['count'] - 3} more")
                md.append("")

            # Overall recommendations
            md.append("## 💡 Priority Recommendations for Actionable Bugs")
            if sorted_buckets:
                top_bucket = sorted_buckets[0]
                md.append(f"1. **Focus on {top_bucket[0]}** - This is your largest actionable category with {top_bucket[1]['count']} bugs")
                md.append(f"2. **{top_bucket[1]['action']}**")
                
            if avg_age_days > 60:
                md.append("3. **Triage old bugs** - Some actionable bugs are quite old and may need to be closed or deprioritized")
            
            if len(sorted_buckets) > 3:
                md.append("4. **Consider batch processing** - You have multiple actionable issue types that could benefit from focused sprints")
        else:
            md.append("## 📊 No clear patterns found in actionable bugs")
            md.append("Your actionable bugs don't fit common categories. Consider manual review or different grouping criteria.")

        return "\n".join(md)