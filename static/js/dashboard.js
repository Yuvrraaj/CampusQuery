document.addEventListener("DOMContentLoaded", () => {
  const enterBtn = document.getElementById("enterAssistantBtn");

  // Smooth transition to assistant page
  enterBtn.addEventListener("click", () => {
    document.body.classList.add("fade-out");
    setTimeout(() => {
      window.location.href = "/assistant";
    }, 800);
  });
});

// Fade-out effect
const css = `
  .fade-out { 
    opacity: 0;
    transition: opacity 0.8s ease-in-out;
  }
`;
const style = document.createElement("style");
style.textContent = css;
document.head.append(style);
