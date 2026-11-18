"use strict";

const app = document.querySelector("#app");

function shuffle(options) {
  for (let index = options.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [options[index], options[other]] = [options[other], options[index]];
  }
}

function paragraph(text, className = "") {
  const element = document.createElement("p");
  element.textContent = text;
  element.className = className;
  element.tabIndex = -1;
  return element;
}

function loadingIndicator() {
  const namespace = "http://www.w3.org/2000/svg";
  const icon = document.createElementNS(namespace, "svg");
  icon.setAttribute("class", "loading-indicator");
  icon.setAttribute("width", "16");
  icon.setAttribute("height", "16");
  icon.setAttribute("viewBox", "0 0 16 16");
  icon.setAttribute("aria-hidden", "true");
  const cells = [[0, 0], [6, 0], [12, 0], [12, 6], [12, 12], [6, 12], [0, 12], [0, 6]];
  cells.forEach(([x, y], index) => {
    const cell = document.createElementNS(namespace, "rect");
    cell.setAttribute("x", x);
    cell.setAttribute("y", y);
    cell.setAttribute("width", "4");
    cell.setAttribute("height", "4");
    cell.setAttribute("fill", index >= 1 && index <= 3 ? "#000000" : "#E1E1E1");
    // Offset the eight clockwise cells by one 100ms step.
    cell.style.animationDelay = `${-((3 - index + 8) % 8) * 100}ms`;
    icon.append(cell);
  });
  return icon;
}

function showQuestion(question, onAnswer) {
  const prompt = paragraph(question.prompt);
  prompt.id = "question";
  const options = document.createElement("div");
  options.className = question.swatches ? "options swatches" : "options";
  options.setAttribute("role", "group");
  options.setAttribute("aria-labelledby", prompt.id);

  for (const option of question.options) {
    const button = document.createElement("button");
    button.type = "button";
    if (question.swatches) {
      button.className = "swatch";
      button.style.backgroundColor = option.label;
      button.setAttribute("aria-label", option.label);
    } else {
      button.textContent = option.label;
    }
    button.addEventListener("click", () => {
      if (!button.isConnected) return;
      for (const control of options.children) control.disabled = true;
      onAnswer(option.id);
    });
    options.append(button);
  }

  app.className = "";
  app.replaceChildren(prompt);
  if (question.image) {
    const image = document.createElement("img");
    image.className = "marmot";
    image.src = question.image;
    image.alt = question.imageAlt;
    app.append(image);
  }
  app.append(options);
  prompt.focus();
}

function startJourney(content) {
  // Shuffle once per visit, retaining stable answer IDs through retries.
  for (const question of content.questions) {
    shuffle(question.options);
    if (question.followup) shuffle(question.followup.options);
  }

  function failVerification() {
    const message = paragraph(content.failure, "error");
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "retry";
    retry.textContent = content.retry;
    retry.addEventListener("click", () => verify(0));
    app.className = "";
    app.replaceChildren(message, retry);
    message.focus();
  }

  function showError() {
    app.className = "error-screen";
    const messages = content.error.map((text, index) =>
      paragraph(text, ["error", "", "module-error", "exit-code"][index])
    );
    app.replaceChildren(...messages);
    messages[0].focus();
  }

  function wait() {
    const queue = content.waitQueues[Math.floor(Math.random() * content.waitQueues.length)];
    const message = paragraph("", "wait");
    message.setAttribute("role", "status");
    message.setAttribute("aria-live", "polite");
    message.setAttribute("aria-atomic", "true");
    app.className = "wait-screen";
    const heading = paragraph(content.waitHeading, "wait-heading");
    app.replaceChildren(heading, loadingIndicator(), message);
    message.textContent = queue[0];
    message.focus();
    let index = 0;
    function advance() {
      index += 1;
      if (index === queue.length) {
        showError();
        return;
      }
      message.textContent = queue[index];
      window.setTimeout(advance, 2000);
    }
    window.setTimeout(advance, 2000);
  }

  function verify(index) {
    const question = content.questions[index];
    showQuestion(question, (answer) => {
      if (question.followup && answer !== "A") {
        showQuestion(question.followup, (confirmation) => {
          if (question.correct.includes(answer) && question.followup.correct.includes(confirmation)) {
            wait();
          } else {
            failVerification();
          }
        });
      } else if (!question.correct.includes(answer)) {
        failVerification();
      } else {
        verify(index + 1);
      }
    });
  }

  verify(0);
}

fetch("content.json")
  .then((response) => {
    if (!response.ok) throw new Error(`Could not load content.json: ${response.status}`);
    return response.json();
  })
  .then(startJourney);
