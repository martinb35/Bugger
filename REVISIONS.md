## Revision History

### v0.0.3 (2025-06-02)
- **🤖 AI-Powered Analysis**: Integrated GPT-4o for intelligent bug categorization and actionability assessment
- **Smart Fallback System**: Optional OpenAI dependency - gracefully falls back to heuristic analysis when unavailable
- **Enhanced Bot Detection**: AI-powered real person vs bot/system creator identification
- **Intelligent Categorization**: GPT-4o analyzes bug descriptions for nuanced classification beyond keyword matching
- **Advanced Title Grouping**: AI identifies duplicate and similar bug titles with higher accuracy
- **Dual Mode Interface**: Dynamic UI that shows current analysis mode (AI-powered vs heuristic)
- **Robust Error Handling**: Comprehensive fallback mechanisms ensure application works with or without OpenAI package
- **Progress Tracking**: Enhanced progress indicators for AI analysis operations

### v0.0.2 (2025-05-30)
- **Major Refactoring**: Split monolithic main.py (400+ lines) into modular components
- **Fixed Bug Count Discrepancy**: Query links now use specific bug IDs instead of keyword searches
- **Added Batch Query Support**: Categories with >50 bugs are split into multiple queries
- **Improved Statistics**: Bug age and active duration now calculated only from actionable bugs
- **Better Organization**: Each module has single responsibility, no code duplication
- **Added Group Similar Titles**: Bugs with similar titles are grouped together in questionable bugs section

### v0.0.1 (Initial Release)
- Basic bug analysis functionality
- Single file implementation
- Keyword-based categorization
- Initial questionable bug detection
