const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const clearButton = document.getElementById("clear");
const llmToggle = document.getElementById("llm-toggle");
const status = document.getElementById("status");
const statusTitle = document.getElementById("status-title");
const statusSteps = status ? Array.from(status.querySelectorAll(".status-step")) : [];

let statusTimers = [];

if (status) {
  status.hidden = true;
}

function clearStatusTimers() {
  statusTimers.forEach((timer) => clearTimeout(timer));
  statusTimers = [];
}

function resetStatus(useLlm) {
  if (!status) {
    return [];
  }

  status.hidden = false;
  status.scrollIntoView({ block: "nearest", behavior: "smooth" });
  if (statusTitle) {
    statusTitle.textContent = "Working...";
  }

  statusSteps.forEach((step) => {
    step.classList.remove("is-active", "is-done", "is-skipped");
    if (step.dataset.llm === "true" && !useLlm) {
      step.classList.add("is-skipped");
    }
  });

  return statusSteps
    .map((step, index) => ({ step, index }))
    .filter(({ step }) => !step.classList.contains("is-skipped"))
    .map(({ index }) => index);
}

function setActiveStep(activeIndex) {
  statusSteps.forEach((step, index) => {
    if (step.classList.contains("is-skipped")) {
      return;
    }
    step.classList.remove("is-active", "is-done");
    if (index < activeIndex) {
      step.classList.add("is-done");
    } else if (index === activeIndex) {
      step.classList.add("is-active");
    }
  });
}

function finishStatus(success) {
  if (!status) {
    return;
  }

  clearStatusTimers();
  statusSteps.forEach((step) => {
    if (step.classList.contains("is-skipped")) {
      return;
    }
    step.classList.remove("is-active");
    step.classList.add("is-done");
  });

  if (statusTitle) {
    statusTitle.textContent = success ? "Done" : "There was an error";
  }

  statusTimers.push(
    setTimeout(() => {
      status.hidden = true;
    }, 900)
  );
}

function addMessage(text, role) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text;
  chat.appendChild(message);
  chat.scrollTop = chat.scrollHeight;
}

async function askBot(question) {
  const useLlm = llmToggle ? llmToggle.checked : true;
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, use_llm: useLlm }),
  });

  if (!response.ok) {
    return {
      ok: false,
      answer: "Sorry, something went wrong. Please try again.",
    };
  }

  const data = await response.json();
  return {
    ok: true,
    answer: data.answer || "I did not find a good match.",
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) {
    addMessage("Please type a question.", "bot");
    return;
  }

  addMessage(question, "user");
  input.value = "";
  input.focus();

  const useLlm = llmToggle ? llmToggle.checked : true;
  clearStatusTimers();
  const stepOrder = resetStatus(useLlm);
  if (stepOrder.length > 0) {
    setActiveStep(stepOrder[0]);
    if (stepOrder[1] !== undefined) {
      statusTimers.push(setTimeout(() => setActiveStep(stepOrder[1]), 200));
    }
    if (stepOrder[2] !== undefined) {
      statusTimers.push(setTimeout(() => setActiveStep(stepOrder[2]), 500));
    }
  }

  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  input.disabled = true;
  if (llmToggle) {
    llmToggle.disabled = true;
  }
  clearButton.disabled = true;
  const result = await askBot(question);
  submitButton.disabled = false;
  input.disabled = false;
  if (llmToggle) {
    llmToggle.disabled = false;
  }
  clearButton.disabled = false;
  finishStatus(result.ok);
  addMessage(result.answer, "bot");
});

clearButton.addEventListener("click", () => {
  chat.innerHTML = "";
  addMessage("Hi! Ask me about delivery, payments, refunds, or scheduling.", "bot");
  if (status) {
    status.hidden = true;
  }
  input.focus();
});
