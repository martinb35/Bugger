const { invoke } = window.__TAURI__.core;

window.addEventListener("DOMContentLoaded", () => {
  const fetchBugsBtn = document.getElementById("fetch-bugs-btn");
  const reportArea = document.getElementById("report-area");

  // Show initial message on load
  if (reportArea) {
    reportArea.innerHTML = `<div class="initial-message">
      Click <b>Refresh Analysis</b> to start heuristic bug analysis...
    </div>`;
  }

  if (fetchBugsBtn && reportArea) {
    fetchBugsBtn.addEventListener("click", async () => {
      reportArea.innerHTML = `<div class="spinner"></div><em>Fetching and analyzing bugs...</em>`;
      try {
        const report = await invoke("fetch_and_analyze_bugs");
        reportArea.innerHTML = report;
      } catch (err) {
        reportArea.innerHTML = `<span style='color:red;'>Error: ${err}</span>`;
      }
    });
  }
});
