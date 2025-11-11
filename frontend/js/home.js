class QuickServeClient {
  constructor() {
    this.serverUrl = sessionStorage.getItem("quickserve_server");
    this.username = sessionStorage.getItem("quickserve_username");
    this.password = sessionStorage.getItem("quickserve_password");

    if (!this.serverUrl || !this.username) {
      window.location.href = "login.html";
      return;
    }

    this.init();
  }

  async init() {
    this.updateServerInfo();

    const initialPath = this.getPathFromURL();

    await this.loadFiles(initialPath);
    this.setupEventListeners();
  }

  getPathFromURL() {
    const hash = window.location.hash.substring(1);
    return hash || "";
  }

  updateURL(path) {
    const newHash = path ? `#${path}` : "";
    const newURL = `home.html${newHash}`;
    window.history.replaceState({ path }, "", newURL);
  }

  navigateToPath(path) {
    const newHash = path ? `#${path}` : "";
    const newURL = `home.html${newHash}`;
    window.history.pushState({ path }, "", newURL);
    this.loadFiles(path);
  }

  getParentPath(currentPath) {
    if (!currentPath) return "";

    const parts = currentPath.split("/").filter((part) => part);
    if (parts.length === 0) return "";

    parts.pop();
    return parts.join("/");
  }

  updateServerInfo() {
    const serverText = document.getElementById("serverText");
    const serverUrl = new URL(this.serverUrl);
    serverText.textContent = serverUrl.host;
  }

  async loadFiles(path) {
    this.showLoading();

    try {
      const response = await fetch(
        `${this.serverUrl}/api/files?path=${encodeURIComponent(path)}`,
        {
          headers: this.getAuthHeaders(),
        }
      );

      if (response.ok) {
        const data = await response.json();
        this.displayFiles(data, path);
      } else if (response.status === 401) {
        this.handleAuthError();
      } else {
        throw new Error("Failed to load files");
      }
    } catch (error) {
      this.showError("Failed to connect to server");
    }
  }

  displayFiles(data, requestedPath) {
    const filesTable = document.getElementById("filesTable");
    const filesTableBody = document.getElementById("filesTableBody");
    const emptyState = document.getElementById("emptyState");
    const currentPathText = document.getElementById("currentPathText");

    const actualPath = data.current_dir || "";
    this.updateURL(actualPath);

    let displayPath = actualPath || "/";
    if (displayPath === "") {
      displayPath = "/";
    }

    currentPathText.textContent = displayPath;

    filesTableBody.innerHTML = "";

    if (data.files.length === 0) {
      filesTable.style.display = "none";
      emptyState.style.display = "block";
      this.hideLoading();
      this.updateNavigation(actualPath);
      return;
    }

    data.files.forEach((file) => {
      const row = document.createElement("tr");

      const nameCell = document.createElement("td");
      const link = document.createElement("a");
      link.href = "#";

      if (file.type === "folder") {
        link.innerHTML = `<i class="fas fa-folder"></i> ${file.name}`;
        link.addEventListener("click", (e) => {
          e.preventDefault();
          this.navigateToPath(file.path);
        });
      } else {
        link.innerHTML = `<i class="fas fa-file"></i> ${file.name}`;
        link.addEventListener("click", (e) => {
          e.preventDefault();
          this.downloadFile(file.path);
        });
      }

      nameCell.appendChild(link);
      row.appendChild(nameCell);

      const dateCell = document.createElement("td");
      dateCell.textContent = file.date_modified;
      row.appendChild(dateCell);

      const sizeCell = document.createElement("td");
      sizeCell.textContent = this.formatFileSize(file.size);
      row.appendChild(sizeCell);

      filesTableBody.appendChild(row);
    });

    filesTable.style.display = "table";
    emptyState.style.display = "none";
    this.hideLoading();
    this.updateNavigation(actualPath);
  }

  async downloadFile(filePath) {
    try {
      const response = await fetch(
        `${this.serverUrl}/api/download?file_path=${encodeURIComponent(
          filePath
        )}`,
        {
          headers: this.getAuthHeaders(),
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;

        const filename = filePath.split("/").pop() || "download";
        a.download = filename;

        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      this.showError("Download failed");
    }
  }

  async uploadFile(file) {
    const currentPath = this.getPathFromURL();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("path", currentPath);

    try {
      const response = await fetch(`${this.serverUrl}/api/upload`, {
        method: "POST",
        headers: this.getAuthHeaders(false),
        body: formData,
      });

      if (response.ok) {
        await this.loadFiles(currentPath);
        this.showTempMessage("Upload successful!");
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      this.showError("Upload failed");
    }
  }

  getAuthHeaders(isJson = true) {
    const headers = {};
    if (isJson) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  handleAuthError() {
    sessionStorage.clear();
    window.location.href = "login.html";
  }

  formatFileSize(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  showLoading() {
    document.getElementById("loadingState").style.display = "block";
    document.getElementById("filesTable").style.display = "none";
    document.getElementById("emptyState").style.display = "none";
  }

  hideLoading() {
    document.getElementById("loadingState").style.display = "none";
  }

  showError(message) {
    alert(message);
  }

  showTempMessage(message) {
    const uploadLabel = document.getElementById("uploadLabel");
    const originalText = uploadLabel.innerHTML;
    uploadLabel.innerHTML = `<i class="fas fa-check"></i> ${message}`;
    setTimeout(() => {
      uploadLabel.innerHTML = originalText;
    }, 2000);
  }

  updateNavigation(currentPath) {
    const backBtn = document.getElementById("backBtn");
    const parentPath = this.getParentPath(currentPath);
    backBtn.disabled = !currentPath || currentPath === "";
  }

  setupEventListeners() {
    const fileInput = document.getElementById("file-input");
    const uploadLabel = document.getElementById("uploadLabel");

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file) {
        this.uploadFile(file);
        fileInput.value = "";
      }
    });

    document.getElementById("backBtn").addEventListener("click", () => {
      const currentPath = this.getPathFromURL();
      const parentPath = this.getParentPath(currentPath);
      if (parentPath !== undefined) {
        this.navigateToPath(parentPath);
      }
    });

    document.getElementById("rootBtn").addEventListener("click", () => {
      this.navigateToPath("");
    });

    document.getElementById("logoutLink").addEventListener("click", (e) => {
      e.preventDefault();
      sessionStorage.clear();
      window.location.href = "login.html";
    });

    window.addEventListener("popstate", (event) => {
      const path = event.state ? event.state.path : this.getPathFromURL();
      this.loadFiles(path);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new QuickServeClient();
});

