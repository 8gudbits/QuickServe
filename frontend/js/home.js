class QuickServeClient {
  constructor() {
    this.serverUrl = localStorage.getItem("quickserve_server");
    this.token = localStorage.getItem("quickserve_token");
    this.username = localStorage.getItem("quickserve_username");
    this.permissions = JSON.parse(
      localStorage.getItem("quickserve_permissions") || "{}"
    );

    if (!this.serverUrl || !this.token) {
      window.location.href = "login.html";
      return;
    }

    this.userPermissions = this.permissions;
    this.previewableTypes = [
      // Text & Documents
      "txt",
      "pdf",
      "md",

      // Images
      "jpg",
      "jpeg",
      "png",
      "gif",
      "bmp",
      "svg",
      "webp",
      "ico",
      "avif",

      // Web Files
      "html",
      "htm",
      "css",
      "js",
      "jsx",
      "ts",
      "tsx",
      "xml",
      "xhtml",

      // Data & Configuration
      "json",
      "csv",
      "yml",
      "yaml",
      "ini",
      "cfg",
      "config",
      "toml",

      // Video
      "mp4",
      "webm",
      "ogg",
      "mkv",
      "m4v",
      "3gp",

      // Audio
      "mp3",
      "wav",
      "flac",
      "aac",
      "m4a",
      "opus",

      // Programming Languages
      "py",
      "java",
      "c",
      "cpp",
      "cc",
      "cxx",
      "h",
      "hpp",
      "cs",
      "rb",
      "php",
      "go",
      "rs",
      "swift",
      "kt",
      "dart",
      "scala",
      "pl",
      "lua",
      "r",
      "m",

      // Shell & Scripting
      "sh",
      "bash",
      "zsh",
      "fish",
      "ps1",
      "bat",
      "cmd",
      "vbs",

      // System & Development
      "gitignore",
      "gitattributes",
      "log",
      "lock",
      "env",

      // Other
      "ics",
      "vcf",
    ];

    this.currentSelectedFile = null;
    this.pendingDeleteFile = null;
    this.suppressLoading = false;
    this.selectionMode = false;
    this.selectedFiles = new Set();
    this.zipSelectBtn = null;
    this.init();
  }

  async init() {
    await this.verifyToken();
    this.updateServerInfo();
    this.updateUIWithPermissions();

    const initialPath = this.getPathFromURL();
    await this.loadFiles(initialPath);
    this.setupEventListeners();
    this.setupContextMenu();
    this.setupZipSelection();
  }

  async verifyToken() {
    try {
      const response = await fetch(`${this.serverUrl}/api/verify-token`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Token invalid");
      }
    } catch (error) {
      this.handleAuthError();
    }
  }

  getAuthHeaders() {
    return {
      Authorization: `Bearer ${this.token}`,
      "Content-Type": "application/json",
    };
  }

  async downloadFile(filePath) {
    if (!this.userPermissions.can_download) {
      this.showError("You don't have permission to download files");
      return;
    }

    try {
      const response = await fetch(
        `${this.serverUrl}/api/download?path=${encodeURIComponent(filePath)}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;

      const filename = filePath.split("/").pop() || "download";
      a.download = filename;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      this.showSuccess("File download started");
    } catch (error) {
      this.showError(`Download failed: ${error.message}`);
    }
  }

  async previewFile(file) {
    if (!this.userPermissions.can_see_preview) {
      this.showError("You don't have permission to preview files");
      return;
    }

    if (!this.isPreviewable(file)) {
      this.showError("This file type cannot be previewed");
      return;
    }

    try {
      const response = await fetch(
        `${this.serverUrl}/api/preview?path=${encodeURIComponent(file.path)}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Preview failed: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const previewWindow = window.open(url, "_blank");

      if (!previewWindow) {
        this.showInfo("Popup blocked! Opening file in same tab");
        window.location.href = url;
      }

      this.showSuccess("File preview opened");
    } catch (error) {
      this.showError(`Preview failed: ${error.message}`);
    }
  }

  handleFileClick(file) {
    if (file.type === "folder") {
      this.navigateToPath(file.path);
    } else {
      this.downloadFile(file.path);
    }
  }

  setupContextMenu() {
    this.contextMenu = document.getElementById("contextMenu");
    this.contextMenuOverlay = document.getElementById("contextMenuOverlay");
    this.previewOption = document.getElementById("previewOption");
    this.downloadOption = document.getElementById("downloadOption");
    this.openOption = document.getElementById("openOption");
    this.downloadZipOption = document.getElementById("downloadZipOption");
    this.deleteOption = document.getElementById("deleteOption");

    this.contextMenuOverlay.addEventListener("click", () => {
      this.hideContextMenu();
    });

    this.previewOption.addEventListener("click", () => {
      if (this.currentSelectedFile && this.userPermissions.can_see_preview) {
        this.previewFile(this.currentSelectedFile);
      }
      this.hideContextMenu();
    });

    this.downloadOption.addEventListener("click", () => {
      if (this.currentSelectedFile && this.userPermissions.can_download) {
        this.downloadFile(this.currentSelectedFile.path);
      }
      this.hideContextMenu();
    });

    this.openOption.addEventListener("click", () => {
      if (this.currentSelectedFile) {
        this.navigateToPath(this.currentSelectedFile.path);
      }
      this.hideContextMenu();
    });

    this.downloadZipOption.addEventListener("click", () => {
      if (this.currentSelectedFile && this.userPermissions.can_download) {
        this.downloadFolderAsZip(this.currentSelectedFile.path);
      }
      this.hideContextMenu();
    });

    this.deleteOption.addEventListener("click", () => {
      if (this.currentSelectedFile && this.userPermissions.can_delete) {
        this.deleteFileOrFolder(this.currentSelectedFile);
      }
      this.hideContextMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.hideContextMenu();
      }
    });

    window.addEventListener(
      "scroll",
      () => {
        this.hideContextMenu();
      },
      true
    );
  }

  async downloadFolderAsZip(folderPath) {
    if (!this.userPermissions.can_download) {
      this.showError("You don't have permission to download files");
      return;
    }

    try {
      const response = await fetch(
        `${this.serverUrl}/api/download-zip?paths=${encodeURIComponent(
          folderPath
        )}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = `${folderPath.split("/").pop() || "folder"}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      this.showSuccess("Folder download started");
    } catch (error) {
      this.showError(`Download failed: ${error.message}`);
    }
  }

  setupZipSelection() {
    this.zipSelectBtn = document.getElementById("zipSelectBtn");

    if (!this.userPermissions.can_download) {
      this.zipSelectBtn.classList.add("disabled");
      this.zipSelectBtn.style.opacity = "0.5";
      this.zipSelectBtn.style.cursor = "not-allowed";
      this.zipSelectBtn.onclick = (e) => {
        e.preventDefault();
        this.showError("You don't have permission to download files");
      };
    } else {
      this.zipSelectBtn.addEventListener("click", () => {
        this.toggleSelectionMode();
      });
    }
  }

  toggleSelectionMode() {
    if (!this.userPermissions.can_download) {
      this.showError("You don't have permission to download files");
      return;
    }

    this.selectionMode = !this.selectionMode;

    if (this.selectionMode) {
      this.enterSelectionMode();
    } else {
      this.exitSelectionMode();
    }
  }

  enterSelectionMode() {
    this.selectionMode = true;
    this.selectedFiles.clear();

    this.zipSelectBtn.innerHTML =
      '<i class="fas fa-times"></i> <span>Cancel</span>';
    this.zipSelectBtn.style.background = "var(--error)";
    this.zipSelectBtn.style.color = "white";

    this.addSelectionUI();
    this.addZipActions();
    this.addSelectionControls();
  }

  exitSelectionMode() {
    this.selectionMode = false;
    this.selectedFiles.clear();

    this.zipSelectBtn.innerHTML =
      '<i class="fas fa-file-archive"></i> <span>Zip</span>';
    this.zipSelectBtn.style.background = "";
    this.zipSelectBtn.style.color = "";

    this.removeSelectionUI();
    this.removeZipActions();
    this.removeSelectionControls();
  }

  addSelectionUI() {
    const filesTableBody = document.getElementById("filesTableBody");
    const rows = filesTableBody.querySelectorAll("tr.file-item");

    rows.forEach((row) => {
      const nameCell = row.cells[0];
      const link = nameCell.querySelector("a");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "file-checkbox";
      checkbox.addEventListener("click", (e) => {
        e.stopPropagation();
      });

      checkbox.addEventListener("change", (e) => {
        const file = this.getFileFromRow(row);
        if (checkbox.checked) {
          this.selectedFiles.add(file.path);
          row.classList.add("selected");
        } else {
          this.selectedFiles.delete(file.path);
          row.classList.remove("selected");
        }
        this.updateSelectionInfo();
      });

      const nameCellContent = document.createElement("div");
      nameCellContent.className = "name-cell-content";
      nameCellContent.appendChild(checkbox);
      nameCellContent.appendChild(link);

      nameCell.innerHTML = "";
      nameCell.appendChild(nameCellContent);

      row.addEventListener("click", (e) => {
        if (
          !e.target.matches('input[type="checkbox"]') &&
          !e.target.matches("a")
        ) {
          checkbox.checked = !checkbox.checked;
          checkbox.dispatchEvent(new Event("change"));
        }
      });
    });

    document.querySelector(".table-container").classList.add("selection-mode");
  }

  removeSelectionUI() {
    const filesTableBody = document.getElementById("filesTableBody");
    const rows = filesTableBody.querySelectorAll("tr.file-item");

    rows.forEach((row) => {
      const nameCell = row.cells[0];
      const nameCellContent = nameCell.querySelector(".name-cell-content");
      const link = nameCellContent.querySelector("a");

      nameCell.innerHTML = "";
      nameCell.appendChild(link);

      row.classList.remove("selected");
    });

    document
      .querySelector(".table-container")
      .classList.remove("selection-mode");
  }

  addSelectionControls() {
    const tableContainer = document.querySelector(".table-container");

    const controlsRow = document.createElement("div");
    controlsRow.className = "selection-controls-row";
    controlsRow.innerHTML = `
        <button class="control-btn" id="selectAllBtn">
            <i class="fas fa-check-square"></i> Select All
        </button>
        <button class="control-btn" id="selectNoneBtn">
            <i class="fas fa-square"></i> Select None
        </button>
        <button class="control-btn" id="selectFoldersBtn">
            <i class="fas fa-folder"></i> Select Folders
        </button>
        <button class="control-btn" id="selectFilesBtn">
            <i class="fas fa-file"></i> Select Files
        </button>
        <button class="control-btn control-btn-primary" id="downloadSelectedFromPanel" disabled>
            <i class="fas fa-download"></i> Download as ZIP
        </button>
        <div class="selection-stats" id="selectionStats">
            0 items selected
        </div>
    `;

    tableContainer.insertBefore(controlsRow, tableContainer.firstChild);

    document.getElementById("selectAllBtn").addEventListener("click", () => {
      this.selectAll();
    });

    document.getElementById("selectNoneBtn").addEventListener("click", () => {
      this.selectNone();
    });

    document
      .getElementById("selectFoldersBtn")
      .addEventListener("click", () => {
        this.selectFoldersOnly();
      });

    document.getElementById("selectFilesBtn").addEventListener("click", () => {
      this.selectFilesOnly();
    });

    document
      .getElementById("downloadSelectedFromPanel")
      .addEventListener("click", () => {
        this.downloadSelectedAsZip();
      });
  }

  removeSelectionControls() {
    const controlsRow = document.querySelector(".selection-controls-row");
    if (controlsRow) {
      controlsRow.remove();
    }
  }

  selectAll() {
    const checkboxes = document.querySelectorAll(".file-checkbox");
    checkboxes.forEach((checkbox) => {
      if (!checkbox.checked) {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event("change"));
      }
    });
  }

  selectNone() {
    const checkboxes = document.querySelectorAll(".file-checkbox");
    checkboxes.forEach((checkbox) => {
      if (checkbox.checked) {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event("change"));
      }
    });
  }

  selectFoldersOnly() {
    const rows = document.querySelectorAll("tr.file-item");
    rows.forEach((row) => {
      const checkbox = row.querySelector(".file-checkbox");
      const isFolder = row.querySelector(".fa-folder") !== null;

      if (isFolder && !checkbox.checked) {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event("change"));
      } else if (!isFolder && checkbox.checked) {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event("change"));
      }
    });
  }

  selectFilesOnly() {
    const rows = document.querySelectorAll("tr.file-item");
    rows.forEach((row) => {
      const checkbox = row.querySelector(".file-checkbox");
      const isFolder = row.querySelector(".fa-folder") !== null;

      if (!isFolder && !checkbox.checked) {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event("change"));
      } else if (isFolder && checkbox.checked) {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event("change"));
      }
    });
  }

  addZipActions() {
    const navButtonsRow = document.querySelector(".nav-buttons-row");

    const zipActions = document.createElement("div");
    zipActions.className = "zip-actions";
    zipActions.innerHTML = `
        <button class="zip-action-btn zip-download" id="downloadSelectedZip" disabled>
            <i class="fas fa-download"></i> Download Selected
        </button>
        <div class="selection-info" id="selectionInfo">
            0 items selected
        </div>
    `;

    navButtonsRow.appendChild(zipActions);

    document
      .getElementById("downloadSelectedZip")
      .addEventListener("click", () => {
        this.downloadSelectedAsZip();
      });
  }

  removeZipActions() {
    const zipActions = document.querySelector(".zip-actions");
    if (zipActions) {
      zipActions.remove();
    }
  }

  updateSelectionInfo() {
    const selectionInfo = document.getElementById("selectionInfo");
    const selectionStats = document.getElementById("selectionStats");
    const downloadBtn = document.getElementById("downloadSelectedZip");
    const downloadPanelBtn = document.getElementById(
      "downloadSelectedFromPanel"
    );

    if (selectionInfo && downloadBtn && selectionStats && downloadPanelBtn) {
      const count = this.selectedFiles.size;
      const message = `${count} item${count !== 1 ? "s" : ""} selected`;

      selectionInfo.textContent = message;
      selectionStats.textContent = message;
      downloadBtn.innerHTML = `<i class="fas fa-download"></i> Download Selected (${count})`;
      downloadPanelBtn.innerHTML = `<i class="fas fa-download"></i> Download as ZIP (${count})`;

      const isDisabled = count === 0;
      downloadBtn.disabled = isDisabled;
      downloadPanelBtn.disabled = isDisabled;
    }
  }

  getFileFromRow(row) {
    const nameCell = row.cells[0];
    const link = nameCell.querySelector("a");
    const icon = link.querySelector("i");
    const name = Array.from(link.childNodes)
      .find((node) => node.nodeType === Node.TEXT_NODE)
      .textContent.trim();
    const isFolder = icon.classList.contains("fa-folder");

    return {
      name: name,
      path: this.getCurrentPath() ? `${this.getCurrentPath()}/${name}` : name,
      type: isFolder ? "folder" : "file",
    };
  }

  getCurrentPath() {
    return this.getPathFromURL();
  }

  async downloadSelectedAsZip() {
    if (this.selectedFiles.size === 0) {
      this.showError("Please select at least one file or folder to download");
      return;
    }

    if (!this.userPermissions.can_download) {
      this.showError("You don't have permission to download files");
      return;
    }

    try {
      const paths = Array.from(this.selectedFiles);
      const pathsParam = paths
        .map((path) => encodeURIComponent(path))
        .join("&paths=");

      const response = await fetch(
        `${this.serverUrl}/api/download-zip?paths=${pathsParam}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = `selected_files_${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      this.showSuccess(`Downloading ${this.selectedFiles.size} items as ZIP`);
      this.exitSelectionMode();
    } catch (error) {
      this.showError("Failed to download selected files: " + error.message);
    }
  }

  updateUIWithPermissions() {
    const uploadLabel = document.getElementById("uploadLabel");
    const zipSelectBtn = document.getElementById("zipSelectBtn");

    if (!this.userPermissions.can_upload) {
      uploadLabel.classList.add("disabled");
      uploadLabel.style.opacity = "0.5";
      uploadLabel.style.cursor = "not-allowed";
      uploadLabel.onclick = (e) => {
        e.preventDefault();
        this.showError("You don't have permission to upload files");
      };
    }

    if (!this.userPermissions.can_download) {
      zipSelectBtn.classList.add("disabled");
      zipSelectBtn.style.opacity = "0.5";
      zipSelectBtn.style.cursor = "not-allowed";
      zipSelectBtn.onclick = (e) => {
        e.preventDefault();
        this.showError("You don't have permission to download files");
      };
    }
  }

  showContextMenu(x, y, file) {
    this.hideContextMenu();

    this.currentSelectedFile = file;

    this.openOption.style.display = "none";
    this.previewOption.style.display = "none";
    this.downloadOption.style.display = "none";
    this.downloadZipOption.style.display = "none";
    this.deleteOption.style.display = "none";

    if (file.type === "folder") {
      this.openOption.style.display = "flex";
      this.downloadZipOption.style.display = "flex";
      this.deleteOption.style.display = "flex";
      this.downloadZipOption.classList.toggle(
        "disabled",
        !this.userPermissions.can_download
      );
      this.deleteOption.classList.toggle(
        "disabled",
        !this.userPermissions.can_delete
      );
    } else {
      this.previewOption.style.display = "flex";
      this.downloadOption.style.display = "flex";
      this.deleteOption.style.display = "flex";
      const isPreviewable = this.isPreviewable(file);
      this.previewOption.classList.toggle(
        "disabled",
        !isPreviewable || !this.userPermissions.can_see_preview
      );
      this.downloadOption.classList.toggle(
        "disabled",
        !this.userPermissions.can_download
      );
      this.deleteOption.classList.toggle(
        "disabled",
        !this.userPermissions.can_delete
      );
    }

    this.contextMenu.style.left = x + "px";
    this.contextMenu.style.top = y + "px";
    this.contextMenu.style.display = "block";
    this.contextMenuOverlay.style.display = "block";

    const rect = this.contextMenu.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
      this.contextMenu.style.left = x - rect.width + "px";
    }
    if (rect.bottom > window.innerHeight) {
      this.contextMenu.style.top = y - rect.height + "px";
    }
  }

  hideContextMenu() {
    this.contextMenu.style.display = "none";
    this.contextMenuOverlay.style.display = "none";
    this.currentSelectedFile = null;
  }

  isPreviewable(file) {
    const fileExt = file.name.split(".").pop().toLowerCase();
    return this.previewableTypes.includes(fileExt);
  }

  handleMenuButtonClick(file, event) {
    event.stopPropagation();
    const rect = event.target.getBoundingClientRect();
    this.showContextMenu(rect.right - 180, rect.bottom + 5, file);
  }

  deleteFileOrFolder(file) {
    if (!this.userPermissions.can_delete) {
      this.showError("You don't have permission to delete files");
      return;
    }

    this.showDeleteModal(file);
  }

  showDeleteModal(file) {
    this.pendingDeleteFile = file;
    const itemType = file.type === "folder" ? "folder" : "file";
    const message = `Are you sure you want to delete the ${itemType} "<strong>${file.name}</strong>"? This action cannot be undone.`;

    document.getElementById("deleteModalMessage").innerHTML = message;
    document.getElementById("deleteModal").style.display = "flex";
  }

  hideDeleteModal() {
    document.getElementById("deleteModal").style.display = "none";
    this.pendingDeleteFile = null;
  }

  async executeDelete() {
    if (!this.pendingDeleteFile) return;

    const file = this.pendingDeleteFile;
    this.hideDeleteModal();

    if (!this.userPermissions.can_delete) {
      this.showError("You don't have permission to delete files");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("path", file.path);

      const response = await fetch(`${this.serverUrl}/api/delete`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();

        if (result.status === "success") {
          const itemType = file.type === "folder" ? "folder" : "file";
          const successMessage = `${
            itemType.charAt(0).toUpperCase() + itemType.slice(1)
          } deleted successfully`;

          this.showSuccess(successMessage);

          const currentPath = this.getPathFromURL();
          setTimeout(() => {
            this.loadFiles(currentPath);
          }, 100);
        } else {
          throw new Error(result.message || "Delete failed");
        }
      } else {
        const errorText = await response.text();
        throw new Error(`Delete failed: ${errorText}`);
      }
    } catch (error) {
      console.error("Delete error:", error);
      const itemType = file.type === "folder" ? "folder" : "file";
      this.showError(`Failed to delete ${itemType}: ${error.message}`);
    }
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
    const isNavigation = !this.suppressLoading;
    if (isNavigation) {
      this.showLoading();
    }

    try {
      const url = `${this.serverUrl}/api/files?path=${encodeURIComponent(
        path
      )}`;
      const response = await fetch(url, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });

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
    } finally {
      this.suppressLoading = false;
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

    filesTableBody.style.opacity = "0.7";
    filesTableBody.style.transition = "opacity 0.2s ease";

    setTimeout(() => {
      filesTableBody.innerHTML = "";

      if (data.files.length === 0) {
        filesTable.style.display = "none";
        emptyState.style.display = "block";
        this.hideLoading();
        this.updateNavigation(actualPath);
        filesTableBody.style.opacity = "1";
        return;
      }

      data.files.forEach((file) => {
        const row = document.createElement("tr");
        row.className = "file-item";

        const nameCell = document.createElement("td");
        const link = document.createElement("a");
        link.href = "#";

        if (file.type === "folder") {
          link.innerHTML = `<i class="fas fa-folder"></i> ${file.name}`;
          link.addEventListener("click", (e) => {
            e.preventDefault();
            this.handleFileClick(file);
          });
        } else {
          link.innerHTML = `<i class="fas fa-file"></i> ${file.name}`;
          link.addEventListener("click", (e) => {
            e.preventDefault();
            this.handleFileClick(file);
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

        const menuCell = document.createElement("td");
        menuCell.className = "menu-column";

        const menuButton = document.createElement("button");
        menuButton.className = "menu-button";
        menuButton.innerHTML = '<i class="fas fa-ellipsis-v"></i>';
        menuButton.setAttribute("aria-label", "File options");
        menuButton.addEventListener("click", (e) => {
          this.handleMenuButtonClick(file, e);
        });
        menuCell.appendChild(menuButton);

        row.appendChild(menuCell);

        filesTableBody.appendChild(row);
      });

      filesTable.style.display = "table";
      emptyState.style.display = "none";
      this.hideLoading();
      this.updateNavigation(actualPath);

      if (this.selectionMode) {
        setTimeout(() => {
          this.addSelectionUI();
          this.updateSelectionInfo();
        }, 150);
      }

      setTimeout(() => {
        filesTableBody.style.opacity = "1";
      }, 50);
    }, 100);
  }

  async uploadFile(file) {
    if (!this.userPermissions.can_upload) {
      this.showError("You don't have permission to upload files");
      return;
    }

    const currentPath = this.getPathFromURL();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("path", currentPath);

    try {
      const response = await fetch(`${this.serverUrl}/api/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();

        this.showSuccess("File uploaded successfully!");

        setTimeout(() => {
          this.loadFiles(currentPath);
        }, 100);
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      this.showError("Upload failed");
    }
  }

  async searchFiles(pattern) {
    if (!pattern || pattern.length < 2) {
      this.showError("Please enter at least 2 characters to search");
      return;
    }

    this.showLoading();
    const currentPath = this.getPathFromURL();

    try {
      const url = `${this.serverUrl}/api/search?path=${encodeURIComponent(
        currentPath
      )}&pattern=${encodeURIComponent(pattern)}`;
      const response = await fetch(url, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        this.displaySearchResults(data, pattern);
      } else if (response.status === 401) {
        this.handleAuthError();
      } else {
        throw new Error("Search failed");
      }
    } catch (error) {
      this.showError("Search failed - please try again");
      this.hideLoading();
    }
  }

  displaySearchResults(data, pattern) {
    const filesTable = document.getElementById("filesTable");
    const filesTableBody = document.getElementById("filesTableBody");
    const emptyState = document.getElementById("emptyState");
    const currentPathText = document.getElementById("currentPathText");

    const searchPath = data.search_path || "";
    let displayPath = searchPath
      ? `${searchPath} (Search: "${pattern}")`
      : `Search: "${pattern}"`;
    currentPathText.textContent = displayPath;

    filesTableBody.innerHTML = "";

    if (data.results.length === 0) {
      filesTable.style.display = "none";
      emptyState.style.display = "block";
      emptyState.innerHTML = `<i class="fas fa-search"></i><p>No files found matching "${pattern}"</p>`;
      this.hideLoading();
      this.updateNavigation(searchPath);
      return;
    }

    const headerRow = document.createElement("tr");
    headerRow.className = "search-header-row";
    headerRow.innerHTML = `<td colspan="4"><i class="fas fa-search"></i> Found ${data.count} files matching "${pattern}"<button class="clear-search-btn" id="clearSearch">Clear Search</button></td>`;
    filesTableBody.appendChild(headerRow);

    data.results.forEach((file) => {
      const row = document.createElement("tr");
      row.className = "file-item";

      const nameCell = document.createElement("td");
      const link = document.createElement("a");
      link.href = "#";

      let fileContent = `<i class="fas fa-file"></i> ${file.name}`;
      if (file.directory && file.directory !== ".") {
        fileContent += `<span class="file-directory">in ${file.directory}</span>`;
      }

      link.innerHTML = fileContent;

      link.addEventListener("click", (e) => {
        e.preventDefault();
        this.handleFileClick(file);
      });

      nameCell.appendChild(link);
      row.appendChild(nameCell);

      const dateCell = document.createElement("td");
      dateCell.textContent = file.date_modified;
      row.appendChild(dateCell);

      const sizeCell = document.createElement("td");
      sizeCell.textContent = this.formatFileSize(file.size);
      row.appendChild(sizeCell);

      const menuCell = document.createElement("td");
      menuCell.className = "menu-column";

      const menuButton = document.createElement("button");
      menuButton.className = "menu-button";
      menuButton.innerHTML = '<i class="fas fa-ellipsis-v"></i>';
      menuButton.setAttribute("aria-label", "File options");
      menuButton.addEventListener("click", (e) => {
        this.handleMenuButtonClick(file, e);
      });
      menuCell.appendChild(menuButton);

      row.appendChild(menuCell);

      filesTableBody.appendChild(row);
    });

    filesTable.style.display = "table";
    emptyState.style.display = "none";
    this.hideLoading();
    this.updateNavigation(searchPath);

    setTimeout(() => {
      const clearSearchBtn = document.getElementById("clearSearch");
      if (clearSearchBtn) {
        clearSearchBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.loadFiles(searchPath);
        });
      }
    }, 0);
  }

  handleAuthError() {
    localStorage.clear();
    window.location.href = "login.html";
  }

  logout() {
    localStorage.clear();
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
    this.showToast(message, "error");
  }

  showSuccess(message) {
    this.showToast(message, "success");
  }

  showInfo(message) {
    this.showToast(message, "info");
  }

  showToast(message, type = "info", duration = 5000) {
    const toastContainer = document.getElementById("toastContainer");

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "info-circle";
    if (type === "success") icon = "check-circle";
    if (type === "error") icon = "exclamation-circle";

    toast.innerHTML = `<i class="fas fa-${icon} toast-icon"></i><div class="toast-content">${message}</div><button class="toast-close" aria-label="Close notification"><i class="fas fa-times"></i></button>`;

    toastContainer.appendChild(toast);

    let removeTimeout;
    if (duration > 0) {
      removeTimeout = setTimeout(() => {
        this.removeToast(toast);
      }, duration);
    }

    const closeBtn = toast.querySelector(".toast-close");
    closeBtn.addEventListener("click", () => {
      if (removeTimeout) clearTimeout(removeTimeout);
      this.removeToast(toast);
    });

    return toast;
  }

  removeToast(toast) {
    toast.classList.add("hiding");
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }

  updateNavigation(currentPath) {
    const backBtn = document.getElementById("backBtn");
    const parentPath = this.getParentPath(currentPath);
    backBtn.disabled = !currentPath || currentPath === "";
  }

  setupSearch() {
    const searchBtn = document.getElementById("searchBtn");
    const searchBox = document.getElementById("searchBox");
    const searchInput = document.getElementById("searchInput");
    const executeSearch = document.getElementById("executeSearch");
    const closeSearch = document.getElementById("closeSearch");

    const showSearchBox = () => {
      searchBox.style.display = "block";
      setTimeout(() => searchInput.focus(), 100);
    };

    const hideSearchBox = () => {
      searchBox.style.display = "none";
      searchInput.value = "";
    };

    const performSearch = () => {
      const pattern = searchInput.value.trim();
      if (pattern) {
        this.searchFiles(pattern);
        hideSearchBox();
      }
    };

    searchBtn.addEventListener("click", showSearchBox);
    executeSearch.addEventListener("click", performSearch);
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        performSearch();
      }
    });
    closeSearch.addEventListener("click", hideSearchBox);

    if (window.innerWidth > 768) {
      document.addEventListener("click", (e) => {
        if (!searchBox.contains(e.target) && !searchBtn.contains(e.target)) {
          hideSearchBox();
        }
      });
    }
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
      this.logout();
    });

    document.getElementById("cancelDelete").addEventListener("click", () => {
      this.hideDeleteModal();
    });

    document.getElementById("confirmDelete").addEventListener("click", () => {
      this.executeDelete();
    });

    document.getElementById("deleteModal").addEventListener("click", (e) => {
      if (e.target.id === "deleteModal") {
        this.hideDeleteModal();
      }
    });

    this.setupSearch();

    window.addEventListener("popstate", (event) => {
      const path = event.state ? event.state.path : this.getPathFromURL();
      this.loadFiles(path);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new QuickServeClient();
});

