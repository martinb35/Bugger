import gradio as gr
from azure_client import AzureDevOpsClient
from bug_analyzer import BugAnalyzer
from bug_categorizer import BugCategorizer
from report_generator import ReportGenerator
from questionable_analyzer import QuestionableAnalyzer

def fetch_and_summarize_bugs():
    """Main function to fetch and analyze bugs"""
    try:
        # Initialize components
        client = AzureDevOpsClient()
        questionable_analyzer = QuestionableAnalyzer()
        
        # Fetch bug data
        work_items = client.fetch_active_bugs()
        
        if not work_items:
            return "No active bugs assigned to you."
        
        # Get detailed bug information
        bugs_data, created_dates, activated_dates = client.fetch_bug_details(work_items)
        
        # Analyze and separate questionable vs actionable bugs
        questionable_bugs, actionable_bugs_data = questionable_analyzer.analyze_and_separate_bugs(bugs_data)
        
        # Start building the complete report
        md = []
        
        # Add questionable bugs section first
        md.extend(questionable_analyzer.generate_questionable_section(questionable_bugs))
        
        # Initialize components for actionable bugs analysis
        analyzer = BugAnalyzer()
        categorizer = BugCategorizer()
        report_generator = ReportGenerator(analyzer, categorizer)
        
        # Generate report for actionable bugs only
        report = report_generator.generate_report(actionable_bugs_data, created_dates, activated_dates)
        
        # Update bug stats to show both totals
        lines = report.split("\n")
        updated_lines = []
        for line in lines:
            if line.startswith("- **Total active bugs:**"):
                updated_lines.append(f"- **Total active bugs:** {len(bugs_data)}")
                updated_lines.append(f"- **Actionable bugs:** {len(actionable_bugs_data)}")
                if questionable_bugs:
                    updated_lines.append(f"- **Questionable bugs:** {len(questionable_bugs)} (excluded from analysis below)")
            else:
                updated_lines.append(line)
        
        # Combine all sections
        final_report = "\n".join(md) + "\n".join(updated_lines)
        
        return final_report
        
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# 🐞 My Active Bugs Dashboard")
    output = gr.Markdown()
    btn = gr.Button("🔄 Refresh Analysis")
    btn.click(fn=fetch_and_summarize_bugs, outputs=output)
    demo.load(fn=fetch_and_summarize_bugs, outputs=output)

if __name__ == "__main__":
    demo.launch(share=True)