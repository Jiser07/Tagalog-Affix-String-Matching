const queryInput = document.getElementById("query");
const algoSelect = document.getElementById("algo");
const searchBtn = document.getElementById("searchBtn");
const nextBtn = document.getElementById("nextBtn");
const clearBtn = document.getElementById("clearBtn");
const normDiv = document.getElementById("norm");
const statusDiv = document.getElementById("status");
const errorDiv = document.getElementById("error");

function showError(msg) {
  errorDiv.textContent = msg;
  errorDiv.style.display = "block";
}

function clearMessages() {
  errorDiv.style.display = "none";
  errorDiv.textContent = "";
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

async function ensureContentScript(tabId) {
  await chrome.scripting.executeScript({
    target: { tabId },
    files: ["content.js"]
  });
}

async function runSearch() {
  clearMessages();
  const query = queryInput.value.trim();
  if (!query) return;

  let tab;
  try {
    tab = await getActiveTab();
    await ensureContentScript(tab.id);
  } catch (err) {
    showError("Cannot run on this browser page. Open a real website (e.g. tl.wikipedia.org) first.");
    return;
  }

  chrome.tabs.sendMessage(tab.id, { action: "extractWords" }, async (extractRes) => {
    if (chrome.runtime.lastError || !extractRes) {
      showError("Could not read text from this page. Try refreshing the webpage.");
      return;
    }

    try {
      const apiRes = await fetch("http://127.0.0.1:8765/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          words: extractRes.words,
          algorithm: algoSelect.value
        })
      });

      const data = await apiRes.json();

      if (data.derived_root && data.derived_root !== data.raw_query) {
        normDiv.textContent = `Query normalized: '${data.raw_query}' -> root '${data.derived_root}'`;
      } else {
        normDiv.textContent = "";
      }

      chrome.tabs.sendMessage(
        tab.id,
        { action: "highlight", classifications: data.classifications },
        (hlRes) => {
          if (!hlRes) return;
          const diff = hlRes.affixTotal - hlRes.plainTotal;
          const diffText = diff >= 0 ? `+${diff} more` : `${diff}`;
          statusDiv.style.display = "block";
          statusDiv.innerHTML =
            `<b>Plain (Ctrl+F):</b> ${hlRes.plainTotal} match(es)<br>` +
            `<b>Affix-Aware:</b> ${hlRes.affixTotal} match(es) (${diffText})<br>` +
            `<b>Python Server Time:</b> ${data.elapsed_ms} ms`;
        }
      );
    } catch (err) {
      showError("Python server not running! Run: python demo/extension_server.py");
    }
  });
}

searchBtn.addEventListener("click", runSearch);
queryInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});

nextBtn.addEventListener("click", async () => {
  try {
    const tab = await getActiveTab();
    await ensureContentScript(tab.id);
    chrome.tabs.sendMessage(tab.id, { action: "nextMatch" });
  } catch (err) {}
});

clearBtn.addEventListener("click", async () => {
  clearMessages();
  normDiv.textContent = "";
  statusDiv.style.display = "none";
  try {
    const tab = await getActiveTab();
    await ensureContentScript(tab.id);
    chrome.tabs.sendMessage(tab.id, { action: "clear" });
  } catch (err) {}
});