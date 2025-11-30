const togglePassword = document.getElementById("togglePassword");
const password = document.getElementById("password");
const icon = togglePassword.querySelector("i");
const loginForm = document.getElementById("loginForm");
const errorMessage = document.getElementById("errorMessage");
const submitBtn = document.getElementById("submitBtn");

document.addEventListener("DOMContentLoaded", function () {
  resetSubmitButton();
});

togglePassword.addEventListener("click", function () {
  const type =
    password.getAttribute("type") === "password" ? "text" : "password";
  password.setAttribute("type", type);
  icon.classList.toggle("fa-eye-slash");
});

async function sha256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hashHex;
}

loginForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const server = document.getElementById("server").value;
  const username = document.getElementById("username").value;
  const passwordValue = document.getElementById("password").value;

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<div class="spinner"></div> CONNECTING...';

  let serverUrl = server.trim();
  if (!serverUrl.startsWith("http://") && !serverUrl.startsWith("https://")) {
    serverUrl = "http://" + serverUrl;
  }

  try {
    new URL(serverUrl);
  } catch (e) {
    showError("Please enter a valid server URL");
    resetSubmitButton();
    return;
  }

  try {
    const hashedPassword = await sha256(passwordValue);

    const response = await fetch(`${serverUrl}/api/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username,
        password: hashedPassword,
      }),
    });

    if (response.ok) {
      const data = await response.json();

      localStorage.setItem("quickserve_server", serverUrl);
      localStorage.setItem("quickserve_token", data.token);
      localStorage.setItem("quickserve_username", username);
      localStorage.setItem(
        "quickserve_permissions",
        JSON.stringify(data.permissions)
      );

      window.location.href = "home.html";
    } else {
      const errorData = await response.json();
      showError(errorData.detail || "Login failed");
      resetSubmitButton();
    }
  } catch (error) {
    showError(
      "Cannot connect to server. Please check the server URL and try again."
    );
    resetSubmitButton();
  }
});

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.style.display = "block";
}

function resetSubmitButton() {
  submitBtn.disabled = false;
  submitBtn.textContent = "CONNECT TO SERVER";
  submitBtn.innerHTML = "CONNECT TO SERVER";
}

window.addEventListener("load", function () {
  const savedServer = localStorage.getItem("quickserve_server");
  if (savedServer) {
    document.getElementById("server").value = savedServer;
  }
});

window.addEventListener("pageshow", function (event) {
  if (
    event.persisted ||
    (window.performance && window.performance.navigation.type === 2)
  ) {
    resetSubmitButton();
  }
});

