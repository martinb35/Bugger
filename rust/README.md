# Tauri Bug Analyzer

This is a minimal Tauri desktop app scaffolded for porting Python-based Azure DevOps bug analysis to Rust. The backend is written in Rust, and the frontend is HTML/JS. To run in development mode:

```
npm run tauri dev
```

To build a release version:

```
npm run tauri build
```

## Next Steps
- Port Azure DevOps bug analysis logic from Python to Rust in `src-tauri`.
- Connect the frontend button to trigger analysis and display the report.
