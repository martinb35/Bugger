from urllib.parse import quote
from datetime import datetime, timezone
from config import ORG, PROJECT, USER_EMAIL, BATCH_SIZE

class ReportGenerator:
    def __init__(self, analyzer, categorizer):
        self.analyzer = analyzer
        self.categorizer = categorizer

    def generate_report(self, bugs_data, created_dates, activated_dates, total_bugs_count, questionable_bugs_count):
        """Generate the markdown report for the bugs"""
        md = []
        try:
            # Calculate stats using the already-parsed dates
            try:
                avg_age_days, avg_active_days = self.analyzer.calculate_stats(created_dates, activated_dates)
            except Exception as e:
                print(f"[ERROR] Failed to calculate stats: {e}")
                avg_age_days, avg_active_days = 0, 0

            # Then, categorize the bugs into meaningful buckets
            try:
                buckets = self.categorizer.extract_meaningful_buckets(bugs_data)
            except Exception as e:
                print(f"[ERROR] Failed to categorize bugs: {e}")
                buckets = {}

            # Sort buckets by count (largest first)
            try:
                sorted_buckets = sorted(buckets.items(), key=lambda x: x[1]["count"], reverse=True)
            except Exception as e:
                print(f"[ERROR] Failed to sort buckets: {e}")
                sorted_buckets = []

            # BUG STATS SECTION
            md.append("## 🐞 Bug Stats")
            md.append(f"- **Total active bugs:** {total_bugs_count}")
            md.append(f"- **Actionable bugs:** {len(bugs_data)}")
            if questionable_bugs_count > 0:
                md.append(f"- **Questionable bugs:** {questionable_bugs_count} (excluded from analysis below)")
            md.append(f"- **Average bug age:** {avg_age_days:.1f} days")
            md.append(f"- **Average length of being active:** {avg_active_days:.1f} days\n")

            # Verify counts add up
            try:
                categorized_count = sum(bucket["count"] for _, bucket in sorted_buckets)
                uncategorized_count = len(bugs_data) - categorized_count
            except Exception as e:
                print(f"[ERROR] Failed to count categorized/uncategorized bugs: {e}")
                categorized_count = 0
                uncategorized_count = len(bugs_data)

            # ACTIONABLE BUG ANALYSIS SECTION
            if sorted_buckets:
                md.append("## 📊 Actionable Bug Analysis by Issue Type")
                md.append("*Note: Questionable bugs excluded from this analysis*\n")
                
                for bucket_name, bucket_info in sorted_buckets:
                    try:
                        md.append(f"### {bucket_info['count']} bugs likely related to: {bucket_name}")
                        md.append(f"**What these bugs are about:** {bucket_info['explanation']}")
                        md.append(f"**Recommended next steps:** {bucket_info['action']}")
                        
                        # Display query links
                        if len(bucket_info['query_urls']) == 1:
                            md.append(f"**[→ {bucket_info['query_urls'][0]['label']} in Azure DevOps]({bucket_info['query_urls'][0]['url']})**")
                        else:
                            md.append("**Query links (batched due to size):**")
                            for query in bucket_info['query_urls']:
                                md.append(f"- [{query['label']}]({query['url']})")
                        
                        # Show sample bugs
                        md.append("\n**Sample bugs:**")
                        for bug_id, title, description, url, created, activated in bucket_info['bugs'][:3]:
                            md.append(f"- [{title}]({url})")
                        
                        if bucket_info['count'] > 3:
                            md.append(f"...and {bucket_info['count'] - 3} more")
                        md.append("")
                    except Exception as e:
                        print(f"[ERROR] Failed to process bucket '{bucket_name}': {e}")
                
                # Add uncategorized bugs if any
                if uncategorized_count > 0:
                    md.append(f"### {uncategorized_count} bugs don't fit any category")
                    md.append("These bugs don't match any of the defined patterns and may need manual review.\n")

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

        except Exception as e:
            print(f"[FATAL ERROR] Failed to generate report: {e}")
            md.append(f"**Error generating report:** {e}")

        return "\n".join(md)