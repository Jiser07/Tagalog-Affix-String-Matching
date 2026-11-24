if (!window.__affixCtrlFInstalled) {
  window.__affixCtrlFInstalled = true;

  let matchElements = [];
  let currentIndex = -1;

  const COLOR_MAP = {
    both: "#FFE58A",
    affix_only: "#8FE3A0",
    plain_only: "#F4A3A3"
  };

  function getTextNodes() {
    const skipTags = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEXTAREA", "INPUT", "SELECT", "MARK"]);
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement && skipTags.has(node.parentElement.tagName)) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    const nodes = [];
    let current;
    while ((current = walker.nextNode())) {
      nodes.push(current);
    }
    return nodes;
  }

  function clearHighlights() {
    const marks = document.querySelectorAll('mark[data-affix-hl="1"]');
    marks.forEach((mark) => {
      const parent = mark.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(mark.textContent), mark);
        parent.normalize();
      }
    });
    matchElements = [];
    currentIndex = -1;
  }

  function extractUniqueWords() {
    const textNodes = getTextNodes();
    const wordSet = new Set();
    const wordRegex = /[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)?/g;

    for (const node of textNodes) {
      const matches = node.nodeValue.match(wordRegex);
      if (matches) {
        for (const w of matches) {
          wordSet.add(w.toLowerCase());
        }
      }
    }
    return Array.from(wordSet);
  }

  function applyHighlights(classifications) {
    clearHighlights();

    const textNodes = getTextNodes();
    const wordRegex = /[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)?/g;

    let bothCount = 0;
    let affixOnlyCount = 0;
    let plainOnlyCount = 0;

    for (const node of textNodes) {
      const text = node.nodeValue;
      wordRegex.lastIndex = 0;
      let match;
      let lastIndex = 0;
      let hasHit = false;
      const frag = document.createDocumentFragment();

      while ((match = wordRegex.exec(text)) !== null) {
        const word = match[0];
        const category = classifications[word.toLowerCase()];

        if (category) {
          hasHit = true;
          if (match.index > lastIndex) {
            frag.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
          }

          const mark = document.createElement("mark");
          mark.setAttribute("data-affix-hl", "1");
          mark.style.backgroundColor = COLOR_MAP[category];
          mark.style.color = "#000";
          mark.style.padding = "0 2px";
          mark.style.borderRadius = "3px";
          mark.textContent = word;
          frag.appendChild(mark);
          matchElements.push(mark);

          if (category === "both") bothCount++;
          else if (category === "affix_only") affixOnlyCount++;
          else if (category === "plain_only") plainOnlyCount++;

          lastIndex = wordRegex.lastIndex;
        }
      }

      if (hasHit) {
        if (lastIndex < text.length) {
          frag.appendChild(document.createTextNode(text.slice(lastIndex)));
        }
        node.parentNode.replaceChild(frag, node);
      }
    }

    if (matchElements.length > 0) {
      focusMatch(0);
    }

    return {
      plainTotal: bothCount + plainOnlyCount,
      affixTotal: bothCount + affixOnlyCount,
      bothCount,
      affixOnlyCount,
      plainOnlyCount
    };
  }

  function focusMatch(idx) {
    if (matchElements.length === 0) return;
    if (currentIndex >= 0 && matchElements[currentIndex]) {
      matchElements[currentIndex].style.outline = "none";
    }
    currentIndex = idx % matchElements.length;
    const el = matchElements[currentIndex];
    el.style.outline = "2px solid #1565C0";
    el.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "extractWords") {
      sendResponse({ words: extractUniqueWords() });
    } else if (msg.action === "highlight") {
      sendResponse(applyHighlights(msg.classifications || {}));
    } else if (msg.action === "nextMatch") {
      if (matchElements.length > 0) focusMatch(currentIndex + 1);
      sendResponse({ ok: true });
    } else if (msg.action === "clear") {
      clearHighlights();
      sendResponse({ ok: true });
    }
    return true;
  });
}