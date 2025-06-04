import gradio as gr
from azure_client import AzureDevOpsClient
from bug_analyzer import BugAnalyzer
from bug_categorizer import BugCategorizer
from report_generator import ReportGenerator
from questionable_analyzer import QuestionableAnalyzer
from config import AI_ENABLED

# Conditionally import AI analyzer
if AI_ENABLED:
    try:
        from ai_bug_analyzer import AIBugAnalyzer
        print("✅ AI-powered analysis enabled")
    except ImportError:
        AI_ENABLED = False
        print("⚠️ Failed to load AI analyzer - falling back to heuristic analysis")

if not AI_ENABLED:
    print("📊 Using heuristic-based analysis")

def fetch_and_summarize_bugs(progress=gr.Progress()):
    """Main function to fetch and analyze bugs"""
    try:
        # Initialize components
        client = AzureDevOpsClient()

        # --- ADO Connectivity Check ---
        try:
            # Try fetching project info or a minimal API call
            project_info = client.get_project_info()  # You may need to implement this method
            print(f"[ADO CONNECTIVITY] Project info: {project_info}")
        except Exception as ado_err:
            print(f"[ADO ERROR] Could not access Azure DevOps project: {ado_err}")
            return f"Error: Could not access Azure DevOps project. Details: {ado_err}"

        # Choose analyzer based on AI availability
        if AI_ENABLED:
            analyzer_instance = AIBugAnalyzer()
            analysis_type = "AI-powered"
        else:
            analyzer_instance = QuestionableAnalyzer()
            analysis_type = "heuristic"
        
        progress(0.1, desc="Fetching bug list...")
        
        # Fetch bug data
        work_items = client.fetch_active_bugs()
        
        if not work_items:
            user_email = getattr(client, "user_email", None)
            if not user_email:
                # Try to get from env if not set on client
                import os
                user_email = os.getenv("AZURE_DEVOPS_USER_EMAIL", "(email not configured)")
            return (
                f"No active bugs assigned to you.\n\n"
                f"Tip: Please check your Azure DevOps account information in the `.env` file.\n"
                f"Currently using email: `{user_email}`"
            )
        
        progress(0.2, desc="Fetching bug details...")
        
        # Get detailed bug information
        bugs_data, created_dates, activated_dates = client.fetch_bug_details(work_items)
        
        progress(0.3, desc=f"Running {analysis_type} bug analysis...")
        
        # Analysis with progress (works for both AI and heuristic)
        def analysis_progress(percent, message):
            progress(0.3 + (percent / 100) * 0.6, desc=message)
        
        questionable_bugs, actionable_bugs_data = analyzer_instance.analyze_and_separate_bugs(
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
        
        # Add analysis mode indicator
        if AI_ENABLED:
            md.append("# 🤖 AI-Powered Bug Analysis Report")
            md.append("*Analysis powered by GPT-4o for enhanced accuracy*\n")
        else:
            md.append("# 📊 Heuristic Bug Analysis Report")
            md.append("*Analysis using pattern-based heuristics*\n")
        
        # Add questionable bugs section
        md.extend(analyzer_instance.generate_questionable_section(questionable_bugs))
        
        # Initialize components for actionable bugs analysis
        bug_analyzer = BugAnalyzer()
        categorizer = BugCategorizer()
        report_generator = ReportGenerator(bug_analyzer, categorizer)
        
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
    if AI_ENABLED:
        title = "# 🤖 Bugger - AI-Powered Bug Analysis"
        subtitle = "Enhanced with GPT-4o for intelligent bug categorization"
    else:
        title = "# 📊 Bugger - Heuristic Bug Analysis"
        subtitle = "Pattern-based bug analysis (install openai package to enable AI)"
    
    gr.Markdown(title)
    gr.Markdown(f"*{subtitle}*")
    
    with gr.Row():
        btn = gr.Button("🔄 Refresh Analysis", scale=1)
        
    if AI_ENABLED:
        initial_message = "Click 'Refresh Analysis' to start AI-powered bug analysis..."
    else:
        initial_message = "Click 'Refresh Analysis' to start heuristic bug analysis..."
        
    output = gr.Markdown(value=initial_message)
    
    # Both button click and demo load use the same function with progress
    btn.click(fn=fetch_and_summarize_bugs, outputs=output, show_progress=True)
    
    # Use a button click to trigger initial load so progress is visible
    demo.load(fn=lambda: gr.update(visible=True), outputs=btn).then(
        fn=fetch_and_summarize_bugs, outputs=output, show_progress=True
    )

if __name__ == "__main__":
    demo.launch(share=False)