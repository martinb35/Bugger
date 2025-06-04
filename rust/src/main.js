const { invoke } = window.__TAURI__.core;

let greetInputEl;
let greetMsgEl;

async function greet() {
  // Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
  greetMsgEl.textContent = await invoke("greet", { name: greetInputEl.value });
}

const fetchBugsBtn = document.getElementById("fetch-bugs-btn");
const reportArea = document.getElementById("report-area");

async function fetchAndAnalyzeBugs() {
  reportArea.innerHTML = "<em>Fetching and analyzing bugs...</em>";
  try {
    const report = await invoke("fetch_and_analyze_bugs");
    reportArea.innerHTML = report;
  } catch (err) {
    reportArea.innerHTML = `<span style='color:red;'>Error: ${err}</span>`;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  greetInputEl = document.querySelector("#greet-input");
  greetMsgEl = document.querySelector("#greet-msg");
  document.querySelector("#greet-form").addEventListener("submit", (e) => {
    e.preventDefault();
    greet();
  });

  if (fetchBugsBtn) {
    fetchBugsBtn.addEventListener("click", fetchAndAnalyzeBugs);
  }
});
