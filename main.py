import gradio as gr
from azure_client import AzureDevOpsClient
from bug_analyzer import BugAnalyzer
from bug_categorizer import BugCategorizer
from report_generator import ReportGenerator
from questionable_analyzer import QuestionableAnalyzer

def fetch_and_summarize_bugs(progress=gr.Progress()):
    """Main function to fetch and analyze bugs"""
    try:
        # Initialize components
        client = AzureDevOpsClient()
        questionable_analyzer = QuestionableAnalyzer()
        
        progress(0.1, desc="Fetching bug list...")
        
        # Fetch bug data
        work_items = client.fetch_active_bugs()
        
        if not work_items:
            return "No active bugs assigned to you."
        
        progress(0.2, desc="Fetching bug details...")
        
        # Get detailed bug information
        bugs_data, created_dates, activated_dates = client.fetch_bug_details(work_items)
        
        progress(0.3, desc="Analyzing bugs...")
        
        # Analyze and separate questionable vs actionable bugs with progress
        def analysis_progress(percent, message):
            progress(0.3 + (percent / 100) * 0.6, desc=message)
        
        questionable_bugs, actionable_bugs_data = questionable_analyzer.analyze_and_separate_bugs(
            bugs_data, 
            progress_callback=analysis_progress
        )
        
        progress(0.9, desc="Generating report...")
        
        # Filter created_dates and activated_dates to only include actionable bugs
        actionable_bug_ids = {bug[0] for bug in actionable_bugs_data}
        actionable_created_dates = [(id, dt) for id, dt in created_dates if id in actionable_bug_ids]
        actionable_activated_dates = [(id, dt) for id, dt in activated_dates if id in actionable_bug_ids]
        
        # Start building the complete report
        md = []
        
        # Add questionable bugs section first
        md.extend(questionable_analyzer.generate_questionable_section(questionable_bugs))
        
        # Initialize components for actionable bugs analysis
        analyzer = BugAnalyzer()
        categorizer = BugCategorizer()
        report_generator = ReportGenerator(analyzer, categorizer)
        
        # Generate report for actionable bugs only
        report = report_generator.generate_report(
            actionable_bugs_data, 
            actionable_created_dates, 
            actionable_activated_dates,
            len(bugs_data),  # total bugs count
            len(questionable_bugs)  # questionable bugs count
        )
        
        # Combine all sections
        final_report = "\n".join(md) + report
        
        progress(1.0, desc="Complete!")
        
        return final_report
        
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# 🐞 Bugger")
    
    with gr.Row():
        btn = gr.Button("🔄 Refresh Analysis", scale=1)
        
    output = gr.Markdown(value="Click 'Refresh Analysis' to start bug analysis...")
    
    # Both button click and demo load use the same function with progress
    btn.click(fn=fetch_and_summarize_bugs, outputs=output, show_progress=True)
    
    # Use a button click to trigger initial load so progress is visible
    demo.load(fn=lambda: gr.update(visible=True), outputs=btn).then(
        fn=fetch_and_summarize_bugs, outputs=output, show_progress=True
    )

if __name__ == "__main__":
    demo.launch(share=False)