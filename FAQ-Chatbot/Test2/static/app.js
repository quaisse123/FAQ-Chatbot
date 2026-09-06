const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("send-button");
const statusPill = document.getElementById("status");

function setStatus(text, isBusy) {
  statusPill.textContent = text;
  if (text.toLowerCase().includes("offline")) {
    statusPill.dataset.state = "offline";
    return;
  }
  statusPill.dataset.state = isBusy ? "busy" : "ready";
}

function addMessage(role, text, meta) {
  const metaData = typeof meta === "string" ? { label: meta } : meta || {};
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const metaEl = document.createElement("div");
  metaEl.className = "meta";
  if (metaData.label) {
    const label = document.createElement("span");
    label.className = "meta-label";
    label.textContent = metaData.label;
    metaEl.appendChild(label);
  }
  if (metaData.tag) {
    const tag = document.createElement("span");
    tag.className = "meta-tag";
    tag.textContent = metaData.tag;
    metaEl.appendChild(tag);
  }

  wrapper.appendChild(bubble);
  wrapper.appendChild(metaEl);
  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;

  return wrapper;
}

function addTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const typing = document.createElement("div");
  typing.className = "typing";
  typing.innerHTML = "<span></span><span></span><span></span>";

  bubble.appendChild(typing);
  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;

  return wrapper;
}

async function sendMessage(text) {
  if (!text.trim()) {
    return;
  }

  addMessage("user", text.trim(), { label: "You" });
  input.value = "";
  input.style.height = "auto";
  sendButton.disabled = true;
  setStatus("Thinking...", true);

  const typingIndicator = addTypingIndicator();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text.trim() }),
    });

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();
    typingIndicator.remove();

    addMessage("assistant", data.answer, {
      label: "Assistant",
      tag: data.category || "",
    });
    setStatus("Ready", false);
  } catch (error) {
    typingIndicator.remove();
    addMessage("assistant", "Something went wrong. Please try again.", {
      label: "Assistant",
    });
    setStatus("Offline", false);
  } finally {
    sendButton.disabled = false;
  }
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", autoResize);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
