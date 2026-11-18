const API_URL = window.DATADOCK_API_URL;

document.addEventListener("DOMContentLoaded", () => {
    // 1. Auth Protection Check
    const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";
    const userEmail = localStorage.getItem("userEmail") || "user@example.com";

    if (!isLoggedIn) {
        window.location.href = "index.html";
        return;
    }

    const isSupportedDataset = filename => /\.(csv|xlsx)$/i.test(filename);

    document.querySelectorAll(".dataset-metric, .version-card, .dashboard-panel").forEach(card => {
        card.classList.add("dashboard-rotatable");
    });

    document.addEventListener("click", event => {
        if (!(event.target instanceof Element)) return;
        if (event.target.closest("button, a, input, select, textarea, label, [role='button']")) return;

        const card = event.target.closest(".dataset-metric, .version-card, .dashboard-panel");
        if (!card) return;

        card.classList.remove("is-rotating");
        void card.offsetWidth;
        card.classList.add("is-rotating");
    });

    document.addEventListener("animationend", event => {
        if (event.animationName === "dashboard-card-spin") {
            event.target.classList.remove("is-rotating");
        }
    });

    // Display user email
    const userDisplay = document.getElementById("userDisplayEmail");
    if (userDisplay) {
        userDisplay.textContent = userEmail;
    }

    // Logout handler
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("isLoggedIn");
            localStorage.removeItem("userEmail");
            localStorage.removeItem("access_token");
            window.location.href = "index.html";
        });
    }

    // 2. Main Navigation Tabs (Upload vs Compare)
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    function activateTab(tabId, recordHistory = false) {
        const targetBtn = [...tabBtns].find(button => button.dataset.tab === tabId);
        const targetPane = document.getElementById(tabId);
        if (!targetBtn || !targetPane) return;

        const isAlreadyActive = targetBtn.classList.contains("active");
        tabBtns.forEach(button => button.classList.toggle("active", button === targetBtn));
        tabPanes.forEach(pane => pane.classList.toggle("active", pane === targetPane));

        if (recordHistory && !isAlreadyActive) {
            window.history.pushState({ tab: tabId }, "", `#${tabId}`);
        }
    }

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            activateTab(btn.dataset.tab, true);
        });
    });

    window.addEventListener("popstate", () => {
        activateTab(window.location.hash.slice(1) || "tab-home");
    });

    if (window.location.hash) {
        activateTab(window.location.hash.slice(1));
    } else {
      // A fresh dashboard load always starts on Home.
      activateTab("tab-home");
    }

    document.querySelectorAll("[data-tab-target]").forEach(action => {
        action.addEventListener("click", () => {
            const targetTab = document.querySelector(`.primary-nav [data-tab="${action.dataset.tabTarget}"]`);
            if (targetTab) targetTab.click();
        });
    });

    const demoSourceButton = document.getElementById("demoSourceButton");
    const realSourceButton = document.getElementById("realSourceButton");
    const demoSourcePanel = document.getElementById("demoSourcePanel");
    const realSourcePanel = document.getElementById("realSourcePanel");

    function setComparisonSource(source) {
        if (!demoSourceButton || !realSourceButton || !demoSourcePanel || !realSourcePanel) return;
        const showDemo = source === "demo";
        demoSourceButton.classList.toggle("active", showDemo);
        realSourceButton.classList.toggle("active", !showDemo);
        demoSourceButton.setAttribute("aria-selected", String(showDemo));
        realSourceButton.setAttribute("aria-selected", String(!showDemo));
        demoSourcePanel.hidden = !showDemo;
        realSourcePanel.hidden = showDemo;
    }

    if (demoSourceButton) demoSourceButton.addEventListener("click", () => setComparisonSource("demo"));
    if (realSourceButton) realSourceButton.addEventListener("click", () => setComparisonSource("real"));

    // 3. Subtabs Navigation in Results View
    const subtabBtns = document.querySelectorAll(".subtab-btn");
    const subtabContents = document.querySelectorAll(".subtab-content");

    subtabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.subtab;
            subtabBtns.forEach(b => b.classList.remove("active"));
            subtabContents.forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(target).classList.add("active");
        });
    });

    // 4. Single CSV File Upload Handler (Upload Tab)
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("csvFileInput");
    const uploadFormatSelect = document.getElementById("uploadFormatSelect");
    const selectedBadge = document.getElementById("fileSelectionBadge");
    const selectedFileName = document.getElementById("selectedFileName");
    const selectedFileSize = document.getElementById("selectedFileSize");
    const uploadBtn = document.getElementById("uploadBtn");
    const messageEl = document.getElementById("uploadMessage");

    let selectedFile = null;

    if (dropZone) {
        dropZone.addEventListener("click", () => fileInput.click());

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith(uploadFormatSelect.value)) {
            showAlert(`Please choose a ${uploadFormatSelect.value} file.`, "error");
            selectedFile = null;
            uploadBtn.disabled = true;
            selectedBadge.style.display = "none";
            fileInput.value = "";
            return;
        }

        selectedFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = `(${formatBytes(file.size)})`;
        selectedBadge.style.display = "block";
        uploadBtn.disabled = false;
        hideAlert();
    }

    if (uploadFormatSelect) {
        uploadFormatSelect.addEventListener("change", () => {
            if (fileInput) fileInput.accept = uploadFormatSelect.value;
            const hint = document.getElementById("uploadDropzoneHint");
            if (hint) hint.textContent = `Drag & Drop a ${uploadFormatSelect.value} file here`;
            if (fileInput) fileInput.value = "";
            selectedFile = null;
            if (uploadBtn) uploadBtn.disabled = true;
            if (selectedBadge) selectedBadge.style.display = "none";
            hideAlert();
        });
    }

    if (uploadBtn) {
        uploadBtn.addEventListener("click", async () => {
            if (!selectedFile) return;

            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading & Processing...';
            hideAlert();

            const formData = new FormData();
            formData.append("file", selectedFile);
            formData.append("user_email", userEmail);

            try {
                const response = await fetch(`${API_URL}/upload-csv`, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    showAlert(`Successfully uploaded "${data.file.filename}"! (${data.file.row_count} rows processed)`, "success");
                    selectedFile = null;
                    fileInput.value = "";
                    selectedBadge.style.display = "none";
                    loadHistory();
                } else {
                    showAlert(data.detail || "Dataset upload failed.", "error");
                }
            } catch (err) {
                console.error("Upload error:", err);
                showAlert("Cannot connect to server. Ensure backend is running.", "error");
            } finally {
                uploadBtn.disabled = selectedFile ? false : true;
                uploadBtn.innerHTML = '<i class="fa-solid fa-upload"></i> Upload & Process Dataset';
            }
        });
    }

    // 5. Fetch & Render CSV History Table & Dropdown Options
    let historyDatasets = [];

    async function loadHistory() {
        try {
            const response = await fetch(`${API_URL}/history?user_email=${encodeURIComponent(userEmail)}`);
            const data = await response.json();

            if (response.ok && data.history) {
                historyDatasets = data.history;
                renderHistoryTable(data.history);
                renderRecentDatasets(data.history);
                populateHistoryDropdowns(data.history);
            }
        } catch (err) {
            console.error("Fetch history error:", err);
        }
    }

    function renderRecentDatasets(items) {
        const list = document.getElementById("recentDatasetsList");
        if (!list) return;

        if (!items.length) {
            list.innerHTML = '<p class="home-empty">No uploaded datasets yet.</p>';
            return;
        }

        list.innerHTML = items.slice(0, 3).map(item => {
            const version = item.filename.match(/v\d+/i)?.[0] || "CSV";
            return `
                <article class="recent-item">
                    <div>
                        <div class="recent-name">${escapeHtml(item.filename)}</div>
                        <span class="recent-meta">${Number(item.row_count || 0).toLocaleString()} rows · ${escapeHtml(item.upload_date)}</span>
                    </div>
                    <span class="recent-version">${escapeHtml(version)}</span>
                </article>
            `;
        }).join("");
    }

    function renderHistoryTable(items) {
        const tbody = document.getElementById("historyTableBody");
        const totalFilesEl = document.getElementById("statTotalFiles");
        const totalRowsEl = document.getElementById("statTotalRows");

        if (!tbody) return;

        let totalRows = 0;
        if (totalFilesEl) totalFilesEl.textContent = items.length;

        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-history">
                        <i class="fa-solid fa-file-excel"></i>
                        <p>No datasets uploaded yet. Upload a CSV or XLSX dataset above to get started.</p>
                    </td>
                </tr>
            `;
            if (totalRowsEl) totalRowsEl.textContent = "0";
            return;
        }

        tbody.innerHTML = items.map((item, idx) => {
            totalRows += (item.row_count || 0);
            return `
                <tr>
                    <td>${idx + 1}</td>
                    <td style="font-weight: 600; color: #ffffff;">
                        <i class="fa-solid fa-file-csv" style="color:#34e89a; margin-right: 0.5rem;"></i>
                        ${escapeHtml(item.filename)}
                    </td>
                    <td>${item.upload_date}</td>
                    <td>${item.file_size}</td>
                    <td><strong style="color:#7affbf;">${item.row_count.toLocaleString()}</strong></td>
                    <td><span class="badge-status"><i class="fa-solid fa-circle-check"></i> ${item.status}</span></td>
                    <td>
                        <div class="table-actions">
                            <a href="${API_URL}/download-csv/${item.id}" target="_blank" class="btn-action">
                                <i class="fa-solid fa-download"></i> Download
                            </a>
                            <button type="button" class="btn-action btn-delete" data-delete-id="${item.id}">
                                <i class="fa-solid fa-trash"></i> Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        if (totalRowsEl) totalRowsEl.textContent = totalRows.toLocaleString();
    }

    document.addEventListener("click", async (event) => {
        const deleteButton = event.target.closest("[data-delete-id]");
        if (!deleteButton) return;

        const fileId = Number(deleteButton.dataset.deleteId);
        if (!fileId) return;

        const confirmed = window.confirm("Delete this dataset from the system and remove its uploaded file?");
        if (!confirmed) return;

        try {
            const response = await fetch(`${API_URL}/history/${fileId}`, {
                method: "DELETE"
            });
            const data = await response.json();

            if (!response.ok) {
                showAlert(data.detail || "Unable to delete dataset.", "error");
                return;
            }

            showAlert("Dataset removed successfully.", "success");
            await loadHistory();
        } catch (err) {
            console.error("Delete dataset error:", err);
            showAlert("Could not delete dataset. Please check the backend server.", "error");
        }
    });

    function populateHistoryDropdowns(items) {
        const selectA = document.getElementById("selectFileA");
        const selectB = document.getElementById("selectFileB");

        if (!selectA || !selectB) return;

        const options = items.map(item => `<option value="${item.id}">${escapeHtml(item.filename)} (${item.row_count} rows - ${item.upload_date})</option>`).join("");
        selectA.innerHTML = '<option value="">-- Select Baseline Dataset (File A) --</option>' + options;
        selectB.innerHTML = '<option value="">-- Select Comparison Dataset (File B) --</option>' + options;
    }

    // 6. Dual Comparison Selection & Drag-and-Drop
    const modeUploadBtn = document.getElementById("modeUploadFilesBtn");
    const modeSelectBtn = document.getElementById("modeSelectHistoryBtn");
    const uploadModeView = document.getElementById("compareUploadModeView");
    const historyModeView = document.getElementById("compareHistoryModeView");

    let currentCompareMode = "upload"; // 'upload' or 'history'
    let compareFileA = null;
    let compareFileB = null;

    if (modeUploadBtn && modeSelectBtn) {
        modeUploadBtn.addEventListener("click", () => {
            currentCompareMode = "upload";
            modeUploadBtn.classList.add("active");
            modeSelectBtn.classList.remove("active");
            uploadModeView.style.display = "block";
            historyModeView.style.display = "none";
        });

        modeSelectBtn.addEventListener("click", () => {
            currentCompareMode = "history";
            modeSelectBtn.classList.add("active");
            modeUploadBtn.classList.remove("active");
            uploadModeView.style.display = "none";
            historyModeView.style.display = "block";
        });
    }

    // Setup Dual Dropzones A & B
    setupDualDropzone("dropZoneA", "fileInputA", "badgeA", "nameA", "formatSelectA", (f) => compareFileA = f);
    setupDualDropzone("dropZoneB", "fileInputB", "badgeB", "nameB", "formatSelectB", (f) => compareFileB = f);

    function setupDualDropzone(zoneId, inputId, badgeId, nameId, formatSelectId, onSelect) {
        const zone = document.getElementById(zoneId);
        const input = document.getElementById(inputId);
        const badge = document.getElementById(badgeId);
        const nameEl = document.getElementById(nameId);
        const formatSelect = document.getElementById(formatSelectId);
        const hint = document.getElementById(`dropzoneHint${inputId.slice(-1)}`);

        if (!zone || !input) return;

        formatSelect.addEventListener("change", () => {
            input.accept = formatSelect.value;
            hint.textContent = `Drop a ${formatSelect.value} file (${inputId.slice(-1)})`;
            input.value = "";
            badge.style.display = "none";
            onSelect(null);
            hideCompareAlert();
        });

        zone.addEventListener("click", () => input.click());

        zone.addEventListener("dragover", (e) => {
            e.preventDefault();
            zone.classList.add("dragover");
        });

        zone.addEventListener("dragleave", () => {
            zone.classList.remove("dragover");
        });

        function selectFile(file) {
            if (!file.name.toLowerCase().endsWith(formatSelect.value)) {
                onSelect(null);
                badge.style.display = "none";
                input.value = "";
                showCompareAlert(`Please choose a ${formatSelect.value} file.`, "error");
                return;
            }

            nameEl.textContent = file.name;
            badge.style.display = "block";
            onSelect(file);
        }

        zone.addEventListener("drop", (e) => {
            e.preventDefault();
            zone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                selectFile(e.dataTransfer.files[0]);
            }
        });

        input.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                selectFile(e.target.files[0]);
            }
        });
    }

    // Domain Selector State
    let currentDomain = "finance";

    const domainFinanceBtn = document.getElementById("domainFinanceBtn");
    const domainHealthcareBtn = document.getElementById("domainHealthcareBtn");
    const domainAcademicsBtn = document.getElementById("domainAcademicsBtn");
    const domainSoftwareBtn = document.getElementById("domainSoftwareBtn");

    const domainItems = [
        { key: "finance", btn: domainFinanceBtn },
        { key: "healthcare", btn: domainHealthcareBtn },
        { key: "academics", btn: domainAcademicsBtn },
        { key: "software_systems", btn: domainSoftwareBtn }
    ];

    domainItems.forEach(item => {
        if (item.btn) {
            item.btn.addEventListener("click", () => setDomain(item.key));
        }
    });

    const domainButtons = domainItems.map(d => d.btn).filter(Boolean);
    const updateDomainRotation = () => {
        const scrollRange = document.documentElement.scrollHeight - window.innerHeight;
        const scrollProgress = scrollRange > 0 ? window.scrollY / scrollRange : 0;
        const rotation = Math.min(1, Math.max(0, scrollProgress)) * 360;

        domainButtons.forEach((button, index) => {
            button.style.setProperty("--scroll-rotation", `${rotation + index * 8}deg`);
        });
    };

    window.addEventListener("scroll", updateDomainRotation, { passive: true });
    updateDomainRotation();

    const DOMAIN_METADATA = {
        finance: {
            title: "Finance",
            tagHtml: '<i class="fa-solid fa-building-columns"></i> Finance Domain',
            tagClass: "domain-badge-tag finance",
            descHtml: '<i class="fa-solid fa-shield-halved" style="color: #34e89a; margin-right: 0.4rem;"></i> Evaluating financial transactions & loan records with 8 regulatory validation rules (Tx ID uniqueness, non-negative amounts, credit score 300–900).',
            ruleNoticeHtml: '<i class="fa-solid fa-shield-halved" style="color: #34e89a; margin-right: 0.4rem;"></i> Configured for <strong>Finance</strong>. Datasets will be audited against monetary amounts, non-negative balances, and loan interest rates.',
            keyPlaceholder: "e.g. Transaction_ID, Loan_ID, Account_No, Trade_ID (Leave blank to auto-detect)",
            btnLabel: "Run Financial Profiling & Comparison",
            presetContainerId: "domainPresetsFinance"
        },
        healthcare: {
            title: "Healthcare",
            tagHtml: '<i class="fa-solid fa-hospital-user"></i> Healthcare Domain',
            tagClass: "domain-badge-tag healthcare",
            descHtml: '<i class="fa-solid fa-shield-halved" style="color: #38bdf8; margin-right: 0.4rem;"></i> Evaluating clinical patient diagnostics & hospital vitals with 8 clinical rules (Patient ID uniqueness, age 0–120, blood glucose 50–500 mg/dL, BMI 10–70).',
            ruleNoticeHtml: '<i class="fa-solid fa-shield-halved" style="color: #38bdf8; margin-right: 0.4rem;"></i> Configured for <strong>Healthcare</strong>. Datasets will be audited against clinical biomarker ranges, patient vitals, and diagnostic taxonomy.',
            keyPlaceholder: "e.g. Patient_ID, EHR_ID, Record_ID, Subject_ID (Leave blank to auto-detect)",
            btnLabel: "Run Healthcare Clinical Audit & Comparison",
            presetContainerId: "domainPresetsHealthcare"
        },
        academics: {
            title: "Academics & Education",
            tagHtml: '<i class="fa-solid fa-graduation-cap"></i> Academics Domain',
            tagClass: "domain-badge-tag academics",
            descHtml: '<i class="fa-solid fa-shield-halved" style="color: #c084fc; margin-right: 0.4rem;"></i> Evaluating student transcripts, GPA scales, and course records with 10 academic validation rules (Student ID uniqueness, GPA 0.0–4.0, exam scores 0–100, attendance % 0–100%).',
            ruleNoticeHtml: '<i class="fa-solid fa-shield-halved" style="color: #c084fc; margin-right: 0.4rem;"></i> Configured for <strong>Academics & Education</strong>. Datasets will be audited against grading scales (GPA 4.0), credit limits, and enrollment standing.',
            keyPlaceholder: "e.g. Student_ID, Enrollment_ID, Roll_No, Candidate_ID (Leave blank to auto-detect)",
            btnLabel: "Run Academic Records Validation & Comparison",
            presetContainerId: "domainPresetsAcademics"
        },
        software_systems: {
            title: "IT & Software Systems",
            tagHtml: '<i class="fa-solid fa-server"></i> IT & Software Domain',
            tagClass: "domain-badge-tag software_systems",
            descHtml: '<i class="fa-solid fa-shield-halved" style="color: #fb923c; margin-right: 0.4rem;"></i> Evaluating server infrastructure telemetry & microservice logs with 9 IT rules (Incident ID uniqueness, CPU utilization 0–100%, latency >= 0ms, HTTP codes 100–599, error rates).',
            ruleNoticeHtml: '<i class="fa-solid fa-shield-halved" style="color: #fb923c; margin-right: 0.4rem;"></i> Configured for <strong>IT & Software Systems</strong>. Datasets will be audited against CPU capacity thresholds, response times, and HTTP protocols.',
            keyPlaceholder: "e.g. Incident_ID, Request_ID, Trace_ID, Server_ID, Log_ID (Leave blank to auto-detect)",
            btnLabel: "Run IT Systems Telemetry Audit & Comparison",
            presetContainerId: "domainPresetsSoftware"
        }
    };

    function setDomain(domain) {
        currentDomain = domain;
        domainItems.forEach(item => {
            if (item.btn) {
                if (item.key === domain) {
                    item.btn.classList.add("active");
                } else {
                    item.btn.classList.remove("active");
                }
            }
        });

        const meta = DOMAIN_METADATA[domain] || DOMAIN_METADATA.finance;

        // 1. Show only this domain's preset container
        const presetContainers = [
            "domainPresetsFinance",
            "domainPresetsHealthcare",
            "domainPresetsAcademics",
            "domainPresetsSoftware"
        ];
        presetContainers.forEach(cId => {
            const el = document.getElementById(cId);
            if (el) {
                el.style.display = (cId === meta.presetContainerId) ? "grid" : "none";
            }
        });

        // 2. Update domain badges & descriptions
        const demoDomainTag = document.getElementById("demoDomainTag");
        if (demoDomainTag) {
            demoDomainTag.className = meta.tagClass;
            demoDomainTag.innerHTML = meta.tagHtml;
        }

        const domainDescEl = document.getElementById("domainDescriptionText");
        if (domainDescEl) {
            domainDescEl.innerHTML = meta.descHtml;
        }

        const customDomainTitle = document.getElementById("customDomainTitle");
        if (customDomainTitle) {
            customDomainTitle.textContent = meta.title;
        }

        const customDomainTag = document.getElementById("customDomainTag");
        if (customDomainTag) {
            customDomainTag.className = meta.tagClass;
            customDomainTag.innerHTML = meta.tagHtml;
        }

        const customRuleNotice = document.getElementById("customDomainRuleNotice");
        if (customRuleNotice) {
            customRuleNotice.innerHTML = meta.ruleNoticeHtml;
        }

        const keyColInput = document.getElementById("keyColumnInput");
        if (keyColInput) {
            keyColInput.placeholder = meta.keyPlaceholder;
        }

        const runBtnLabel = document.getElementById("runCompareBtnLabel");
        if (runBtnLabel) {
            runBtnLabel.textContent = meta.btnLabel;
        }
    }

    // Initialize domain state
    setDomain("finance");

    // 6.5 Preset Demo Dataset Handlers
    const presetBankBtn = document.getElementById("presetBankBtn");
    const presetLoanBtn = document.getElementById("presetLoanBtn");
    const presetHealthBtn = document.getElementById("presetHealthBtn");
    const presetClinicalVitalsBtn = document.getElementById("presetClinicalVitalsBtn");
    const presetAcademicsBtn = document.getElementById("presetAcademicsBtn");
    const presetCourseEnrollmentBtn = document.getElementById("presetCourseEnrollmentBtn");
    const presetSoftwareBtn = document.getElementById("presetSoftwareBtn");
    const presetMicroservicesBtn = document.getElementById("presetMicroservicesBtn");

    if (presetBankBtn) {
        presetBankBtn.addEventListener("click", () => {
            setDomain("finance");
            runPresetComparison("bank-transactions");
        });
    }
    if (presetLoanBtn) {
        presetLoanBtn.addEventListener("click", () => {
            setDomain("finance");
            runPresetComparison("loan-portfolio");
        });
    }
    if (presetHealthBtn) {
        presetHealthBtn.addEventListener("click", () => {
            setDomain("healthcare");
            runPresetComparison("patient-diagnostics");
        });
    }
    if (presetClinicalVitalsBtn) {
        presetClinicalVitalsBtn.addEventListener("click", () => {
            setDomain("healthcare");
            runPresetComparison("clinical-vitals");
        });
    }
    if (presetAcademicsBtn) {
        presetAcademicsBtn.addEventListener("click", () => {
            setDomain("academics");
            runPresetComparison("student-academics");
        });
    }
    if (presetCourseEnrollmentBtn) {
        presetCourseEnrollmentBtn.addEventListener("click", () => {
            setDomain("academics");
            runPresetComparison("course-enrollment");
        });
    }
    if (presetSoftwareBtn) {
        presetSoftwareBtn.addEventListener("click", () => {
            setDomain("software_systems");
            runPresetComparison("software-systems");
        });
    }
    if (presetMicroservicesBtn) {
        presetMicroservicesBtn.addEventListener("click", () => {
            setDomain("software_systems");
            runPresetComparison("microservices-api");
        });
    }

    const tryDemoBtn = document.getElementById("tryDemoBtn");
    if (tryDemoBtn) {
        tryDemoBtn.addEventListener("click", () => {
            document.querySelector('.primary-nav [data-tab="tab-compare"]')?.click();
            setComparisonSource("demo");
            runPresetComparison("bank-transactions");
        });
    }

    async function runPresetComparison(presetKey) {
        showCompareAlert(`Generating & analyzing demo dataset preset '${presetKey}'...`, "info");
        if (runCompareBtn) runCompareBtn.disabled = true;

        try {
            const response = await fetch(`${API_URL}/api/sample-datasets/${presetKey}`, {
                method: "POST"
            });
            const data = await response.json();

            if (response.ok && data.data) {
                showComparisonReport(data.data);
                hideCompareAlert();
            } else {
                showCompareAlert(data.detail || "Failed to execute preset comparison.", "error");
            }
        } catch (err) {
            console.error("Preset comparison error:", err);
            showCompareAlert("Cannot connect to server. Ensure backend is running.", "error");
        } finally {
            if (runCompareBtn) runCompareBtn.disabled = false;
        }
    }

    // 7. Run Comparison Action
    const runCompareBtn = document.getElementById("runCompareBtn");
    const compareMsg = document.getElementById("compareMessage");
    const resultsCard = document.getElementById("comparisonResultsCard");
    const reportEmptyState = document.getElementById("reportEmptyState");
    const reportTabBtn = document.querySelector('.primary-nav [data-tab="tab-reports"]');

    let lastComparisonReport = null;

    const chartMetricSelect = document.getElementById("chartMetricSelect");
    if (chartMetricSelect) {
        chartMetricSelect.addEventListener("change", () => {
            if (lastComparisonReport) renderComparisonChart(lastComparisonReport);
        });
    }

    function showComparisonReport(data) {
        lastComparisonReport = data;
        renderComparisonResults(data);
        if (resultsCard) resultsCard.style.display = "block";
        if (reportEmptyState) reportEmptyState.style.display = "none";
        reportTabBtn?.click();
        if (resultsCard) resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    if (runCompareBtn) {
        runCompareBtn.addEventListener("click", async () => {
            const keyCol = document.getElementById("keyColumnInput").value.trim();

            showCompareAlert("Running financial profiling engine...", "info");
            runCompareBtn.disabled = true;
            runCompareBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Profiling & Comparing...';

            try {
                let response, data;

                if (currentCompareMode === "upload") {
                    if (!compareFileA || !compareFileB) {
                        showCompareAlert("Please select both baseline and comparison dataset files.", "error");
                        runCompareBtn.disabled = false;
                        runCompareBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Financial Profiling & Comparison';
                        return;
                    }

                    const formData = new FormData();
                    formData.append("file_a", compareFileA);
                    formData.append("file_b", compareFileB);
                    formData.append("domain", currentDomain);
                    if (keyCol) formData.append("key_column", keyCol);

                    response = await fetch(`${API_URL}/compare-csv`, {
                        method: "POST",
                        body: formData
                    });
                } else {
                    const idA = document.getElementById("selectFileA").value;
                    const idB = document.getElementById("selectFileB").value;

                    if (!idA || !idB) {
                        showCompareAlert("Please select both datasets from the history dropdowns.", "error");
                        runCompareBtn.disabled = false;
                        runCompareBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Profiling & Comparison';
                        return;
                    }

                    response = await fetch(`${API_URL}/compare-csv-ids`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            file_id_a: parseInt(idA),
                            file_id_b: parseInt(idB),
                            key_column: keyCol || null,
                            domain: currentDomain
                        })
                    });
                }

                data = await response.json();

                if (response.ok && data.data) {
                    showComparisonReport(data.data);
                    hideCompareAlert();
                } else {
                    showCompareAlert(data.detail || "Profiling analysis failed.", "error");
                }

            } catch (err) {
                console.error("Comparison error:", err);
                showCompareAlert("Failed to connect to comparison server.", "error");
            } finally {
                runCompareBtn.disabled = false;
                runCompareBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Financial Profiling & Comparison';
            }
        });
    }

    function renderHomeOverview(data) {
        const summary = data.summary || {};
        const drift = data.schema_drift || {};
        const validationA = data.validation_a || {};
        const validationB = data.validation_b || {};
        const missingA = Math.max(0, 100 - Number(summary.completeness_a ?? 100));
        const missingB = Math.max(0, 100 - Number(summary.completeness_b ?? 100));

        const setText = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        const setDelta = (id, text, negative = false) => {
            const element = document.getElementById(id);
            if (!element) return;
            element.textContent = text;
            element.classList.toggle("negative", negative);
        };
        const formatCount = value => Number(value || 0).toLocaleString();
        const formatPercent = value => `${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
        const statusFor = (before, after, increaseIsWorse = true) => {
            if (before === after) return "Unchanged";
            const worsened = increaseIsWorse ? after > before : after < before;
            return worsened ? "Regression" : "Improvement";
        };
        const changeRow = (label, value, status, icon) => `
            <div class="change-row">
                <span class="change-icon ${status === "Unchanged" ? "neutral" : status.toLowerCase()}"><i class="fa-solid ${icon}"></i></span>
                <span class="change-copy"><span class="change-name">${escapeHtml(label)}</span><span class="change-value">${escapeHtml(value)}</span></span>
                <span class="change-status ${status === "Unchanged" ? "neutral" : status.toLowerCase()}">${escapeHtml(status)}</span>
            </div>
        `;

        setText("overviewStatus", `${summary.name_a || "Version 1"} compared with ${summary.name_b || "Version 2"}`);
        setText("overviewRows", formatCount(summary.rows_b));
        setText("overviewColumns", formatCount(summary.cols_b));
        setText("overviewMissing", formatPercent(missingB));
        setText("overviewDuplicates", formatCount(summary.duplicates_b));

        const rowDelta = Number(summary.row_delta || 0);
        const columnDelta = Number(summary.cols_b || 0) - Number(summary.cols_a || 0);
        const missingDelta = missingB - missingA;
        const duplicateDelta = Number(summary.duplicates_b || 0) - Number(summary.duplicates_a || 0);
        const signedCount = value => `${value > 0 ? "+" : ""}${formatCount(value)}`;
        setDelta("overviewRowsDelta", `${rowDelta > 0 ? "↑" : rowDelta < 0 ? "↓" : "→"} ${signedCount(rowDelta)} (${Number(summary.row_delta_pct || 0)}%) vs. previous version`, rowDelta < 0);
        setDelta("overviewColumnsDelta", `${columnDelta > 0 ? "↑" : columnDelta < 0 ? "↓" : "→"} ${signedCount(columnDelta)} vs. previous version`, columnDelta < 0);
        setDelta("overviewMissingDelta", `${missingDelta > 0 ? "↑" : missingDelta < 0 ? "↓" : "→"} ${formatPercent(Math.abs(missingDelta))} vs. previous version`, missingDelta > 0);
        setDelta("overviewDuplicatesDelta", `${duplicateDelta > 0 ? "↑" : duplicateDelta < 0 ? "↓" : "→"} ${signedCount(duplicateDelta)} vs. previous version`, duplicateDelta > 0);

        setText("overviewNameA", summary.name_a || "Version 1");
        setText("overviewNameB", summary.name_b || "Version 2");
        setText("overviewRowsA", formatCount(summary.rows_a));
        setText("overviewRowsB", formatCount(summary.rows_b));
        setText("overviewColumnsA", formatCount(summary.cols_a));
        setText("overviewColumnsB", formatCount(summary.cols_b));
        setText("overviewMissingA", formatPercent(missingA));
        setText("overviewMissingB", formatPercent(missingB));
        setText("overviewDuplicatesA", formatCount(summary.duplicates_a));
        setText("overviewDuplicatesB", formatCount(summary.duplicates_b));

        const addedColumns = drift.columns_only_in_b || [];
        const removedColumns = drift.columns_only_in_a || [];
        const typeChanges = drift.type_mismatches || [];
        const schemaDetails = [];
        if (addedColumns.length) schemaDetails.push(`+${addedColumns.length} added`);
        if (removedColumns.length) schemaDetails.push(`-${removedColumns.length} removed`);
        if (typeChanges.length) schemaDetails.push(`${typeChanges.length} type changes`);

        const violationsA = Number(validationA.total_violations || 0);
        const violationsB = Number(validationB.total_violations || 0);
        const schemaStatus = schemaDetails.length ? "Changed" : "Unchanged";
        const changes = [
            changeRow("Missing Values", `${formatPercent(missingA)} → ${formatPercent(missingB)}`, statusFor(missingA, missingB), "fa-triangle-exclamation"),
            changeRow("Duplicate Records", `${formatCount(summary.duplicates_a)} → ${formatCount(summary.duplicates_b)}`, statusFor(Number(summary.duplicates_a || 0), Number(summary.duplicates_b || 0)), "fa-clone"),
            changeRow("Schema Changes", schemaDetails.join(" · ") || "No column changes", schemaStatus, "fa-file-circle-plus"),
            changeRow("Validation Violations", `${formatCount(violationsA)} → ${formatCount(violationsB)}`, statusFor(violationsA, violationsB), "fa-circle-check")
        ];
        const changesList = document.getElementById("homeChangesList");
        if (changesList) changesList.innerHTML = changes.join("");

        renderComparisonChart(data);
    }

    function renderComparisonChart(data) {
        const summary = data.summary || {};
        const metric = chartMetricSelect?.value || "missing";
        const missingA = Math.max(0, 100 - Number(summary.completeness_a ?? 100));
        const missingB = Math.max(0, 100 - Number(summary.completeness_b ?? 100));
        const metrics = {
            missing: { title: "Missing Values Rate", valueA: missingA, valueB: missingB, unit: "%", max: Math.max(10, Math.ceil(Math.max(missingA, missingB) / 5) * 5) },
            rows: { title: "Total Rows", valueA: Number(summary.rows_a || 0), valueB: Number(summary.rows_b || 0), unit: "", max: Math.max(Number(summary.rows_a || 0), Number(summary.rows_b || 0), 1) * 1.15 },
            quality: { title: "Quality Score", valueA: Number(summary.quality_score_a || 0), valueB: Number(summary.quality_score_b || 0), unit: "%", max: 100 }
        };
        const chart = metrics[metric] || metrics.missing;
        const formatValue = value => `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}${chart.unit}`;
        const axis = document.getElementById("chartAxis");
        if (axis) {
            axis.innerHTML = [1, 0.75, 0.5, 0.25, 0].map(fraction => `<span>${formatValue(chart.max * fraction)}</span>`).join("");
        }

        document.getElementById("chartTitle").textContent = chart.title;
        document.getElementById("chartValueA").textContent = formatValue(chart.valueA);
        document.getElementById("chartValueB").textContent = formatValue(chart.valueB);
        document.getElementById("chartBarA").style.height = `${Math.max(1, chart.valueA / chart.max * 100)}%`;
        document.getElementById("chartBarB").style.height = `${Math.max(1, chart.valueB / chart.max * 100)}%`;
        document.getElementById("comparisonChart").setAttribute("aria-label", `${chart.title}: Version 1 ${formatValue(chart.valueA)}, Version 2 ${formatValue(chart.valueB)}`);
    }

    // 8. Render Results Dashboard
    function renderComparisonResults(data) {
        renderHomeOverview(data);
        const summary = data.summary;
        const drift = data.schema_drift;
        const financial = data.financial_metrics;
        const columns = data.column_comparison;
        const rows = data.row_discrepancies;
        const classification = data.classification || {};
        const explanation = data.explanation || {};
        const valA = data.validation_a || {};
        const valB = data.validation_b || {};

        // Executive Overview Cards
        const overviewContainer = document.getElementById("overviewCardsContainer");
        const rowDeltaBadge = summary.row_delta >= 0
            ? `<span class="badge-positive">+${summary.row_delta.toLocaleString()} (+${summary.row_delta_pct}%)</span>`
            : `<span class="badge-negative">${summary.row_delta.toLocaleString()} (${summary.row_delta_pct}%)</span>`;

        const driftBadge = drift.has_drift
            ? `<span class="badge-warning"><i class="fa-solid fa-triangle-exclamation"></i> Schema Drift Detected</span>`
            : `<span class="badge-positive"><i class="fa-solid fa-circle-check"></i> Clean Alignment</span>`;

        overviewContainer.innerHTML = `
            <div class="overview-card">
                <div class="overview-title">Quality Score (V1 vs V2)</div>
                <div class="overview-val">${summary.quality_score_a}% <span style="font-size:0.9rem; color:#8c8c8c;">vs</span> ${summary.quality_score_b}%</div>
            </div>
            <div class="overview-card">
                <div class="overview-title">Total Rows Monitored</div>
                <div class="overview-val">${summary.rows_b.toLocaleString()} ${rowDeltaBadge}</div>
            </div>
            <div class="overview-card">
                <div class="overview-title">Total Columns</div>
                <div class="overview-val">${summary.cols_a} <span style="font-size:0.9rem; color:#8c8c8c;">→</span> ${summary.cols_b}</div>
            </div>
            <div class="overview-card">
                <div class="overview-title">Schema Drift Status</div>
                <div style="margin-top:0.4rem;">${driftBadge}</div>
            </div>
        `;

        // Grounded Executive AI Audit Narrative Banner
        const aiBanner = document.getElementById("aiAuditNarrativeBanner");
        if (aiBanner && explanation.headline) {
            let statusColor = "#16a34a";
            if (explanation.overall_status === "REGRESSION") statusColor = "#dc2626";
            else if (explanation.overall_status === "REQUIRES_HUMAN_REVIEW") statusColor = "#d97706";
            const modelLabel = explanation.generator === "openai"
                ? `OPENAI LLM · ${escapeHtml(explanation.model || "OpenAI")}`
                : "RULE-BASED FALLBACK · SET OPENAI_API_KEY";

            aiBanner.innerHTML = `
                <div style="background: #ffffff; border: 1px solid ${statusColor}; border-radius: 16px; padding: 1.4rem; box-shadow: 0 8px 25px rgba(15, 23, 42, 0.08);">
                    <div style="display:flex; align-items:center; justify-content:space-between; gap: 0.8rem; margin-bottom: 0.8rem; flex-wrap: wrap;">
                        <h3 style="color:#1f2937; font-size:1.15rem; font-weight:700; margin:0;"><i class="fa-solid fa-robot" style="color:${statusColor}; margin-right:0.4rem;"></i> ${escapeHtml(explanation.headline)}</h3>
                        <span style="background: rgba(255,255,255,0.9); border: 1px solid ${statusColor}; color: ${statusColor}; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.78rem; font-weight: 600;">EVIDENCE GROUNDED · ${modelLabel}</span>
                    </div>
                    <p style="font-size: 0.92rem; color: #334155; line-height: 1.6; white-space: pre-line; margin: 0;">${escapeHtml(explanation.executive_summary)}</p>
                    ${explanation.recommended_actions && explanation.recommended_actions.length > 0 ? `
                        <div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px dashed rgba(15, 23, 42, 0.15);">
                            <strong style="color:#0f766e; font-size:0.85rem;"><i class="fa-solid fa-list-check"></i> Recommended Audit Actions:</strong>
                            <ul style="margin-top:0.4rem; padding-left: 1.4rem; color: #475569; font-size: 0.88rem; line-height: 1.6;">
                                ${explanation.recommended_actions.map(act => `<li>${escapeHtml(act)}</li>`).join("")}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Schema Drift Alert Banner
        const driftBanner = document.getElementById("schemaDriftBanner");
        if (drift.has_drift) {
            let desc = [];
            if (drift.columns_only_in_a.length > 0) desc.push(`Removed in B: <strong>${drift.columns_only_in_a.join(", ")}</strong>`);
            if (drift.columns_only_in_b.length > 0) desc.push(`Added in B: <strong>${drift.columns_only_in_b.join(", ")}</strong>`);
            if (drift.type_mismatches.length > 0) {
                const types = drift.type_mismatches.map(m => `${m.column} (${m.type_a} → ${m.type_b})`).join(", ");
                desc.push(`Data Type Mismatches: <strong>${types}</strong>`);
            }
            driftBanner.innerHTML = `
                <div class="alert-banner warning">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size:1.2rem;"></i>
                    <div><strong>Schema Alert:</strong> ${desc.join(" | ")}</div>
                </div>
            `;
        } else {
            driftBanner.innerHTML = `
                <div class="alert-banner info">
                    <i class="fa-solid fa-shield-check" style="font-size:1.2rem;"></i>
                    <div><strong>Schema Verified:</strong> Baseline CSV ("${summary.name_a}") and Comparison CSV ("${summary.name_b}") share identical column definitions.</div>
                </div>
            `;
        }

        // Subtab 0: Regression Classifications Table
        const classBadgeEl = document.getElementById("classificationSummaryBadge");
        const classTbody = document.getElementById("classificationTableBody");

        const counts = classification.counts || {};
        classBadgeEl.innerHTML = `
            <div style="display:flex; gap:0.8rem; flex-wrap:wrap; font-size:0.88rem;">
                <span class="badge-negative"><i class="fa-solid fa-circle-exclamation"></i> Regressions: ${counts.REGRESSION || 0}</span>
                <span class="badge-warning"><i class="fa-solid fa-eye"></i> Human Review Needed: ${counts.REQUIRES_HUMAN_REVIEW || 0}</span>
                <span class="badge-positive"><i class="fa-solid fa-arrow-trend-up"></i> Improvements: ${counts.IMPROVEMENT || 0}</span>
                <span class="badge-status"><i class="fa-solid fa-equals"></i> Neutral: ${counts.NEUTRAL || 0}</span>
            </div>
        `;

        const items = classification.classifications || [];
        if (items.length === 0) {
            classTbody.innerHTML = `<tr><td colspan="4" class="empty-history"><p>No regression items flagged.</p></td></tr>`;
        } else {
            classTbody.innerHTML = items.map(it => {
                let badge = `<span class="badge-status">${it.category}</span>`;
                if (it.category === "REGRESSION") badge = `<span class="badge-negative">🔴 REGRESSION</span>`;
                else if (it.category === "IMPROVEMENT") badge = `<span class="badge-positive">🟢 IMPROVEMENT</span>`;
                else if (it.category === "REQUIRES_HUMAN_REVIEW") badge = `<span class="badge-warning">🟡 REQUIRES HUMAN REVIEW</span>`;
                else if (it.category === "NEUTRAL") badge = `<span class="badge-status">⚪ NEUTRAL</span>`;

                return `
                    <tr>
                        <td>${badge}</td>
                        <td style="font-weight:600; color:#ffffff;">${escapeHtml(it.title)}</td>
                        <td>${escapeHtml(it.details)}</td>
                        <td><strong style="color:${it.severity === 'CRITICAL' || it.severity === 'HIGH' ? '#f87171' : '#34e89a'};">${it.severity}</strong></td>
                    </tr>
                `;
            }).join("");
        }

        // Subtab 0.5: Financial Validation Rules Table
        const valBannerEl = document.getElementById("validationSummaryBanner");
        const valTbody = document.getElementById("validationTableBody");

        if (valB.rule_results) {
            valBannerEl.innerHTML = `
                <div style="font-size:0.9rem; color:#7affbf;">
                    <i class="fa-solid fa-shield-halved"></i> Validation Compliance: <strong>${valB.overall_compliance_rate}%</strong> | 
                    Passed Rules: <strong style="color:#34e89a;">${valB.passed_rules_count} / ${valB.total_rules_evaluated}</strong> | 
                    Total Violations: <strong style="color:${valB.total_violations > 0 ? '#f87171' : '#34e89a'};">${valB.total_violations}</strong>
                </div>
            `;

            valTbody.innerHTML = valB.rule_results.map(r => {
                const statusBadge = r.passed
                    ? `<span class="badge-positive"><i class="fa-solid fa-circle-check"></i> Passed</span>`
                    : `<span class="badge-negative"><i class="fa-solid fa-triangle-exclamation"></i> Failed</span>`;

                const detailsText = r.affected_columns && r.affected_columns.length > 0
                    ? r.affected_columns.map(ac => `<strong>${escapeHtml(ac.column)}</strong> (${ac.violation_count} failed - sample: ${ac.sample_violations.join(", ")})`).join(" | ")
                    : "No column violations";

                return `
                    <tr>
                        <td style="font-weight:600; color:#ffffff;">${escapeHtml(r.rule_name)}</td>
                        <td style="font-size:0.85rem; color:#cbd5e1;">${escapeHtml(r.description)}</td>
                        <td>${statusBadge}</td>
                        <td><strong style="color:${r.severity === 'CRITICAL' || r.severity === 'HIGH' ? '#f87171' : '#f59e0b'};">${r.severity}</strong></td>
                        <td><strong style="color:${r.total_violations > 0 ? '#f87171' : '#34e89a'};">${r.total_violations}</strong></td>
                        <td style="font-size:0.85rem;">${detailsText}</td>
                    </tr>
                `;
            }).join("");
        } else {
            valTbody.innerHTML = `<tr><td colspan="6" class="empty-history"><p>No validation rule evaluation data.</p></td></tr>`;
        }

        // Subtab 0.6: Row-Level Violation Inspector Table
        const rowValHeaderEl = document.getElementById("rowViolationInspectorHeader");
        const rowValTbody = document.getElementById("rowViolationTableBody");

        const rowViolations = valB.row_violations || [];
        if (rowValHeaderEl && rowValTbody) {
            rowValHeaderEl.innerHTML = `
                <div style="font-size:0.9rem; color:#7affbf;">
                    <i class="fa-solid fa-filter-circle-xmark"></i> Flagged Offending Rows (Showing Top ${rowViolations.length} Violations):
                </div>
            `;

            if (rowViolations.length === 0) {
                rowValTbody.innerHTML = `<tr><td colspan="6" class="empty-history"><i class="fa-solid fa-circle-check" style="font-size:2rem; color:#34e89a;"></i><p>No row-level validation rule violations found in target dataset!</p></td></tr>`;
            } else {
                rowValTbody.innerHTML = rowViolations.map(rv => `
                    <tr>
                        <td><strong style="color:#7affbf;">Row ${rv.row_number}</strong></td>
                        <td><code style="color:#ffffff;">${escapeHtml(rv.column)}</code></td>
                        <td><span class="badge-negative">${escapeHtml(String(rv.value))}</span></td>
                        <td style="font-weight:600; color:#ffffff;">${escapeHtml(rv.rule_name)}</td>
                        <td style="font-size:0.85rem; color:#cbd5e1;">${escapeHtml(rv.description)}</td>
                        <td><strong style="color:${rv.severity === 'CRITICAL' || rv.severity === 'HIGH' ? '#f87171' : '#f59e0b'};">${rv.severity}</strong></td>
                    </tr>
                `).join("");
            }
        }

        // Subtab 1: Numeric & Domain Metrics Table
        const finTbody = document.getElementById("financialTableBody");
        const dStr = String(data.domain || currentDomain).toLowerCase();
        const metricIcon = dStr.includes("health") ? "fa-heart-pulse" :
            (dStr.includes("acad") || dStr.includes("edu")) ? "fa-graduation-cap" :
            (dStr.includes("soft") || dStr.includes("it")) ? "fa-server" : "fa-coins";

        if (financial.length === 0) {
            finTbody.innerHTML = `<tr><td colspan="10" class="empty-history"><p>No numeric columns detected in common.</p></td></tr>`;
        } else {
            finTbody.innerHTML = financial.map(f => {
                const pctChangeBadge = f.sum_pct_change >= 0
                    ? `<span class="badge-positive">+${f.sum_pct_change}%</span>`
                    : `<span class="badge-negative">${f.sum_pct_change}%</span>`;

                const minMaxA = (f.min_a !== null && f.max_a !== null) ? `${formatNum(f.min_a)} to ${formatNum(f.max_a)}` : '-';
                const minMaxB = (f.min_b !== null && f.max_b !== null) ? `${formatNum(f.min_b)} to ${formatNum(f.max_b)}` : '-';

                return `
                    <tr>
                        <td style="font-weight:600; color:#ffffff;"><i class="fa-solid ${metricIcon}" style="color:#34e89a; margin-right:0.5rem;"></i>${escapeHtml(f.column)}</td>
                        <td>${formatNum(f.sum_a)}</td>
                        <td>${formatNum(f.sum_b)}</td>
                        <td style="font-weight:600; color:${f.sum_delta >= 0 ? '#34e89a' : '#f87171'};">${f.sum_delta >= 0 ? '+' : ''}${formatNum(f.sum_delta)}</td>
                        <td>${pctChangeBadge}</td>
                        <td><span style="opacity:0.85;">${formatNum(f.mean_a)}</span> / <strong>${formatNum(f.mean_b)}</strong></td>
                        <td><span style="opacity:0.85;">${formatNum(f.median_a)}</span> / <strong>${formatNum(f.median_b)}</strong></td>
                        <td style="font-size:0.82rem;"><span style="opacity:0.8;">[${minMaxA}]</span> / <strong style="color:#7affbf;">[${minMaxB}]</strong></td>
                        <td><span style="opacity:0.8;">${f.zero_count_a}</span> / <strong style="color:${f.zero_count_b > f.zero_count_a ? '#f59e0b' : '#34e89a'};">${f.zero_count_b}</strong></td>
                        <td><span style="opacity:0.8;">${f.negative_count_a}</span> / <strong style="color:${f.negative_count_b > f.negative_count_a ? '#f87171' : '#7affbf'};">${f.negative_count_b}</strong></td>
                    </tr>
                `;
            }).join("");
        }

        // Subtab 2: Column Profiling Table
        const colTbody = document.getElementById("columnProfileTableBody");
        colTbody.innerHTML = columns.map(c => {
            let statusBadge = `<span class="badge-status"><i class="fa-solid fa-check"></i> ${c.status}</span>`;
            if (c.status === "Added in B") statusBadge = `<span class="badge-positive">+ ${c.status}</span>`;
            else if (c.status === "Removed in B") statusBadge = `<span class="badge-negative">- ${c.status}</span>`;
            else if (c.status === "Type Mismatch") statusBadge = `<span class="badge-warning"><i class="fa-solid fa-exclamation"></i> ${c.status}</span>`;

            return `
                <tr>
                    <td style="font-weight:600; color:#ffffff;">${escapeHtml(c.column)}</td>
                    <td>${statusBadge}</td>
                    <td><code>${c.type_a}</code></td>
                    <td><code>${c.type_b}</code></td>
                    <td>${c.null_pct_a !== null ? c.null_pct_a + '%' : '-'}</td>
                    <td>${c.null_pct_b !== null ? c.null_pct_b + '%' : '-'}</td>
                    <td>${c.unique_a !== null ? c.unique_a.toLocaleString() : '-'} / ${c.unique_b !== null ? c.unique_b.toLocaleString() : '-'}</td>
                </tr>
            `;
        }).join("");

        // Subtab 3: Row Discrepancy Table
        const rowSummaryEl = document.getElementById("rowDiscrepancySummary");
        const rowTbody = document.getElementById("rowDiffTableBody");

        const keyText = rows.key_column_used ? `Key Column used: <strong>${escapeHtml(rows.key_column_used)}</strong>` : `Auto-matched key column`;
        rowSummaryEl.innerHTML = `<i class="fa-solid fa-link"></i> ${keyText} | Matched Rows: <strong>${rows.matched_keys_count.toLocaleString()}</strong> | Missing in B: <strong style="color:#f87171;">${rows.missing_in_b_count.toLocaleString()}</strong> | Added in B: <strong style="color:#34e89a;">${rows.added_in_b_count.toLocaleString()}</strong>`;

        if (rows.sample_value_diffs.length === 0) {
            rowTbody.innerHTML = `<tr><td colspan="4" class="empty-history"><i class="fa-solid fa-check-double"></i><p>No row-level value discrepancies detected among sampled matching records!</p></td></tr>`;
        } else {
            rowTbody.innerHTML = rows.sample_value_diffs.map(d => `
                <tr>
                    <td style="font-weight:600; color:#7affbf;">${escapeHtml(d.key)}</td>
                    <td style="font-weight:500; color:#ffffff;">${escapeHtml(d.column)}</td>
                    <td style="color:#f87171; text-decoration: line-through;">${escapeHtml(String(d.val_a ?? 'NULL'))}</td>
                    <td style="color:#34e89a; font-weight:600;">${escapeHtml(String(d.val_b ?? 'NULL'))}</td>
                </tr>
            `).join("");
        }
    }


    // 9. Export Report Handlers (JSON & CSV Downloads)
    const exportBtn = document.getElementById("exportReportBtn");
    if (exportBtn) {
        exportBtn.addEventListener("click", () => {
            if (!lastComparisonReport) return;

            const jsonStr = JSON.stringify(lastComparisonReport, null, 2);
            const blob = new Blob([jsonStr], { type: "application/json" });
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = `datadock_profiling_report_${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    const exportCsvBtn = document.getElementById("exportCsvBtn");
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener("click", () => {
            if (!lastComparisonReport) return;
            exportComparisonCSV(lastComparisonReport);
        });
    }

    function exportComparisonCSV(report) {
        const lines = [];
        const s = report.summary || {};
        const fList = report.financial_metrics || [];
        const cList = report.column_comparison || [];
        const r = report.row_discrepancies || {};

        lines.push("DATADOCK AI - FINANCIAL CSV COMPARISON & PROFILING REPORT");
        lines.push(`Generated At,${new Date().toISOString()}`);
        lines.push(`Baseline Dataset (A),${s.name_a || 'File A'},Rows,${s.rows_a || 0},Cols,${s.cols_a || 0},Quality Score,${s.quality_score_a || 0}%`);
        lines.push(`Comparison Dataset (B),${s.name_b || 'File B'},Rows,${s.rows_b || 0},Cols,${s.cols_b || 0},Quality Score,${s.quality_score_b || 0}%`);
        lines.push(`Row Variance,${s.row_delta || 0} (${s.row_delta_pct || 0}%)`);
        lines.push("");

        // Section 1: Financial Metrics
        lines.push("--- FINANCIAL METRICS SUMMARY ---");
        lines.push("Column,Sum A,Sum B,Sum Delta,% Change,Mean A,Mean B,Mean Delta,Median A,Median B,Median Delta,Min A,Max A,Min B,Max B,Zero Count A,Zero Count B,Negative Count A,Negative Count B");
        fList.forEach(f => {
            lines.push([
                `"${f.column}"`,
                f.sum_a,
                f.sum_b,
                f.sum_delta,
                `${f.sum_pct_change}%`,
                f.mean_a,
                f.mean_b,
                f.mean_delta,
                f.median_a,
                f.median_b,
                f.median_delta,
                f.min_a ?? '',
                f.max_a ?? '',
                f.min_b ?? '',
                f.max_b ?? '',
                f.zero_count_a,
                f.zero_count_b,
                f.negative_count_a,
                f.negative_count_b
            ].join(","));
        });
        lines.push("");

        // Section 2: Schema & Column Breakdown
        lines.push("--- SCHEMA & COLUMN PROFILING ---");
        lines.push("Column,Status,Type A,Type B,Null % A,Null % B,Unique A,Unique B");
        cList.forEach(c => {
            lines.push([
                `"${c.column}"`,
                `"${c.status}"`,
                c.type_a,
                c.type_b,
                c.null_pct_a ?? '',
                c.null_pct_b ?? '',
                c.unique_a ?? '',
                c.unique_b ?? ''
            ].join(","));
        });
        lines.push("");

        // Section 3: Sample Row Discrepancies
        lines.push("--- ROW DISCREPANCIES ---");
        lines.push(`Key Column Used,${r.key_column_used || 'N/A'}`);
        lines.push(`Matched Keys,${r.matched_keys_count || 0},Missing in B,${r.missing_in_b_count || 0},Added in B,${r.added_in_b_count || 0}`);
        lines.push("Key Identifier,Column Name,Baseline Value (A),Comparison Value (B)");
        (r.sample_value_diffs || []).forEach(d => {
            lines.push([
                `"${d.key}"`,
                `"${d.column}"`,
                `"${d.val_a ?? 'NULL'}"`,
                `"${d.val_b ?? 'NULL'}"`
            ].join(","));
        });

        const csvContent = lines.join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = `datadock_financial_profiling_report_${Date.now()}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // Helper alerts & formatters
    function showAlert(text, type) {
        if (messageEl) {
            messageEl.textContent = text;
            messageEl.className = `alert-msg ${type}`;
        }
    }

    function hideAlert() {
        if (messageEl) messageEl.style.display = "none";
    }

    function showCompareAlert(text, type) {
        if (compareMsg) {
            compareMsg.textContent = text;
            compareMsg.className = `alert-msg ${type}`;
            compareMsg.style.display = "block";
        }
    }

    function hideCompareAlert() {
        if (compareMsg) compareMsg.style.display = "none";
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function formatNum(val) {
        if (val === null || val === undefined) return '-';
        if (typeof val === 'number') {
            return val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        }
        return val;
    }

        function escapeHtml(text) {
        if (!text) return '';
        return String(text).replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
        });
    }

    // ========================================================
    // SQL WORKBENCH LOGIC
    // ========================================================
    // ========================================================
    // SQL WORKBENCH LOGIC
    // ========================================================
    let currentSqlResults = null;
    let currentSqlPage = 1;
    let currentSqlTotalPages = 1;

    async function loadWorkbenchDatasets() {
        try {
            const res = await fetch(`${API_URL}/api/datasets?user_email=${encodeURIComponent(userEmail)}`);
            const data = await res.json();
            if (!data.success) return;

            const wbSelect = document.getElementById("workbenchDatasetSelect");
            const visualSelect = document.getElementById("visualDatasetSelect");

            if (wbSelect) {
                wbSelect.innerHTML = '<option value="">-- Select Active Dataset --</option>';
                data.datasets.forEach(ds => {
                    const opt = document.createElement("option");
                    opt.value = ds.id;
                    opt.textContent = `${ds.name} (${ds.row_count || 0} rows) [${ds.domain || 'finance'}]`;
                    opt.dataset.tableName = ds.table_name;
                    opt.dataset.domain = ds.domain;
                    wbSelect.appendChild(opt);
                });
            }

            if (visualSelect) {
                visualSelect.innerHTML = '<option value="">-- Choose Dataset --</option>';
                data.datasets.forEach(ds => {
                    const opt = document.createElement("option");
                    opt.value = ds.id;
                    opt.textContent = `${ds.name} (${ds.row_count || 0} rows) [${ds.domain || 'finance'}]`;
                    opt.dataset.tableName = ds.table_name;
                    opt.dataset.domain = ds.domain;
                    visualSelect.appendChild(opt);
                });
            }
        } catch (e) {
            console.error("Failed to load workbench datasets:", e);
        }
    }

    const wbSelectEl = document.getElementById("workbenchDatasetSelect");
    if (wbSelectEl) {
        wbSelectEl.addEventListener("change", async () => {
            const dsId = wbSelectEl.value;
            const treeContainer = document.getElementById("tableSchemaTree");
            if (!dsId) {
                if (treeContainer) treeContainer.innerHTML = '<p style="font-size: 0.82rem; color: #94a3b8;">Select a dataset above to inspect its schema and columns.</p>';
                return;
            }

            try {
                if (treeContainer) treeContainer.innerHTML = '<p style="font-size: 0.82rem; color: #7affbf;"><i class="fa-solid fa-spinner fa-spin"></i> Inspecting schema...</p>';
                const res = await fetch(`${API_URL}/api/datasets/${encodeURIComponent(dsId)}/schema`);
                const data = await res.json();

                if (data.success && data.schema) {
                    const s = data.schema;
                    let colsHtml = s.columns.map(c => `
                        <div class="column-badge">
                            <span>${escapeHtml(c.name)}</span>
                            <span class="type-tag">${escapeHtml(c.type)}</span>
                        </div>
                    `).join("");

                    treeContainer.innerHTML = `
                        <div class="dataset-tree-item">
                            <div class="dataset-tree-header">
                                <span><i class="fa-solid fa-table"></i> ${escapeHtml(s.table_name)}</span>
                                <span style="font-size: 0.75rem; color: #7affbf;">${s.row_count} rows</span>
                            </div>
                            <div class="dataset-tree-columns">
                                <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Columns (${s.column_count}):</span>
                                ${colsHtml}
                            </div>
                        </div>
                    `;

                    // Pre-fill query input with sample query using real table name
                    const textarea = document.getElementById("sqlQueryTextarea");
                    if (textarea && (!textarea.value || textarea.value.includes("FROM dataset"))) {
                        textarea.value = `SELECT * FROM "${s.table_name}" LIMIT 25;`;
                    }
                }
            } catch (e) {
                if (treeContainer) treeContainer.innerHTML = `<p style="font-size: 0.82rem; color: #f87171;">Failed to inspect schema: ${escapeHtml(e.message)}</p>`;
            }
        });
    }

    // SQL Template chips
    document.querySelectorAll(".template-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const template = chip.dataset.template;
            const textarea = document.getElementById("sqlQueryTextarea");
            const activeOpt = wbSelectEl?.selectedOptions[0];
            const table = activeOpt?.dataset?.tableName || "dataset";

            let sql = "";
            switch (template) {
                case "select_all":
                    sql = `SELECT * FROM "${table}" LIMIT 50;`;
                    break;
                case "group_count":
                    sql = `SELECT * FROM "${table}" LIMIT 10;\n-- Replace column_name below:\n-- SELECT column_name, COUNT(*) AS count FROM "${table}" GROUP BY column_name ORDER BY count DESC;`;
                    break;
                case "aggregate_avg":
                    sql = `-- Replace metric_col and category_col below:\nSELECT category_col, ROUND(AVG(metric_col), 2) AS avg_value, ROUND(SUM(metric_col), 2) AS total_value FROM "${table}" GROUP BY category_col ORDER BY total_value DESC;`;
                    break;
                case "filter_where":
                    sql = `SELECT * FROM "${table}" WHERE column_name IS NOT NULL ORDER BY 1 DESC LIMIT 50;`;
                    break;
                case "join_example":
                    sql = `-- Multi-table analytical join:\nSELECT t1.*, t2.* \nFROM t1 \nJOIN t2 ON t1.id = t2.id \nLIMIT 50;`;
                    break;
                case "order_desc":
                    sql = `SELECT * FROM "${table}" ORDER BY 1 DESC LIMIT 50;`;
                    break;
            }
            if (textarea) textarea.value = sql;
        });
    });

    // Propose SQL via Gemini / Heuristic Fallback
    const genSqlBtn = document.getElementById("generateSqlBtn");
    if (genSqlBtn) {
        genSqlBtn.addEventListener("click", async () => {
            const promptInput = document.getElementById("aiQueryPromptInput");
            const prompt = promptInput?.value?.trim();
            if (!prompt) {
                alert("Please enter a question or instruction for Gemini (e.g. 'Show top 5 categories by average amount').");
                return;
            }

            const dsId = wbSelectEl?.value;
            if (!dsId) {
                alert("Please select an active dataset in the left panel first.");
                return;
            }

            const activeOpt = wbSelectEl.selectedOptions[0];
            const domain = activeOpt?.dataset?.domain || "finance";

            try {
                genSqlBtn.disabled = true;
                genSqlBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';

                const res = await fetch(`${API_URL}/api/query/generate`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt, dataset_id: dsId, domain })
                });

                const data = await res.json();
                if (data.success && data.data) {
                    const textarea = document.getElementById("sqlQueryTextarea");
                    if (textarea) textarea.value = data.data.sql;

                    const explanationText = document.getElementById("sqlAiExplanationText");
                    if (explanationText) {
                        explanationText.innerHTML = `<strong>✨ AI Plan (${escapeHtml(data.data.generator)}):</strong> ${escapeHtml(data.data.explanation)}`;
                    }

                    // Auto-execute the proposed query for immediate results preview
                    executeSqlQuery(1);
                } else {
                    alert(data.detail || "Failed to generate SQL query.");
                }
            } catch (e) {
                alert("Error calling AI query generator: " + e.message);
            } finally {
                genSqlBtn.disabled = false;
                genSqlBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Propose SQL';
            }
        });
    }

    // Execute SQL Query
    async function executeSqlQuery(page = 1) {
        const textarea = document.getElementById("sqlQueryTextarea");
        const query = textarea?.value?.trim();
        const errEl = document.getElementById("sqlErrorMsg");
        const statusBar = document.getElementById("sqlStatusBar");
        const statusPill = document.getElementById("sqlStatusPill");
        const timingBadge = document.getElementById("sqlTimingBadge");
        const rowsBadge = document.getElementById("sqlRowsBadge");
        const resultsCard = document.getElementById("sqlResultsCard");
        const exportBtn = document.getElementById("exportSqlCsvBtn");

        if (!query) {
            if (errEl) {
                errEl.textContent = "Please enter a SQL query to execute.";
                errEl.style.display = "block";
            }
            return;
        }

        if (errEl) errEl.style.display = "none";
        const execBtn = document.getElementById("executeSqlBtn");
        if (execBtn) {
            execBtn.disabled = true;
            execBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running...';
        }

        try {
            const dsId = wbSelectEl?.value;
            const res = await fetch(`${API_URL}/api/query/execute`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    dataset_id: dsId || null,
                    page,
                    page_size: 50
                })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Query execution failed.");
            }

            currentSqlResults = data;
            currentSqlPage = data.page;
            currentSqlTotalPages = data.total_pages;

            if (statusBar) statusBar.style.display = "flex";
            if (statusPill) {
                statusPill.className = "status-pill success";
                statusPill.textContent = "Success";
            }
            if (timingBadge) timingBadge.innerHTML = `<i class="fa-solid fa-bolt"></i> ${data.execution_time_ms} ms`;
            if (rowsBadge) rowsBadge.innerHTML = `<i class="fa-solid fa-table-cells"></i> ${data.total_rows >= 0 ? data.total_rows.toLocaleString() : data.row_count} rows`;

            if (resultsCard) resultsCard.style.display = "block";
            if (exportBtn) exportBtn.style.display = "inline-flex";

            renderSqlTable(data);
            populateChartSelectors(data);
            renderSqlChart(data);

            // Fetch AI explanation asynchronously
            explainQueryResultsAsync(query, data);

        } catch (e) {
            if (statusBar) statusBar.style.display = "flex";
            if (statusPill) {
                statusPill.className = "status-pill error";
                statusPill.textContent = "Error";
            }
            if (errEl) {
                errEl.textContent = e.message;
                errEl.style.display = "block";
            }
        } finally {
            if (execBtn) {
                execBtn.disabled = false;
                execBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run Query';
            }
        }
    }

    const execSqlBtn = document.getElementById("executeSqlBtn");
    if (execSqlBtn) {
        execSqlBtn.addEventListener("click", () => executeSqlQuery(1));
    }

    const clearSqlBtn = document.getElementById("clearSqlBtn");
    if (clearSqlBtn) {
        clearSqlBtn.addEventListener("click", () => {
            const textarea = document.getElementById("sqlQueryTextarea");
            if (textarea) textarea.value = "";
            const resultsCard = document.getElementById("sqlResultsCard");
            if (resultsCard) resultsCard.style.display = "none";
            const statusBar = document.getElementById("sqlStatusBar");
            if (statusBar) statusBar.style.display = "none";
            const errEl = document.getElementById("sqlErrorMsg");
            if (errEl) errEl.style.display = "none";
        });
    }

    // Save Query Handler
    const saveSqlBtn = document.getElementById("saveSqlBtn");
    if (saveSqlBtn) {
        saveSqlBtn.addEventListener("click", async () => {
            const textarea = document.getElementById("sqlQueryTextarea");
            const sql = textarea?.value?.trim();
            if (!sql) {
                alert("Cannot save an empty query.");
                return;
            }

            const queryName = prompt("Enter a descriptive name for this analytical query:", "Analytical Metric Analysis");
            if (!queryName) return;

            const dsId = wbSelectEl?.value;
            const activeOpt = wbSelectEl?.selectedOptions[0];
            const domain = activeOpt?.dataset?.domain || "finance";

            try {
                const res = await fetch(`${API_URL}/api/queries/save`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_email: userEmail,
                        query_name: queryName,
                        query_sql: sql,
                        dataset_id: dsId && !isNaN(dsId) ? parseInt(dsId) : null,
                        dataset_name: activeOpt?.textContent || "dataset",
                        domain
                    })
                });
                const data = await res.json();
                if (data.success) {
                    alert(`Query '${queryName}' saved successfully to Lineage and Query History.`);
                    loadSavedQueries();
                } else {
                    alert(data.detail || "Failed to save query.");
                }
            } catch (e) {
                alert("Error saving query: " + e.message);
            }
        });
    }

    // Render Tabular SQL Results
    function renderSqlTable(data) {
        const thead = document.getElementById("sqlResultsHead");
        const tbody = document.getElementById("sqlResultsBody");
        const countBadge = document.getElementById("sqlResultsCountBadge");
        const paginationInfo = document.getElementById("sqlPaginationInfo");
        const prevBtn = document.getElementById("sqlPrevPageBtn");
        const nextBtn = document.getElementById("sqlNextPageBtn");

        if (countBadge) {
            countBadge.textContent = `${data.total_rows >= 0 ? data.total_rows.toLocaleString() : data.row_count} total records`;
        }

        if (thead) {
            thead.innerHTML = `<tr>${data.columns.map(c => `<th>${escapeHtml(c)}</th>`).join("")}</tr>`;
        }

        if (tbody) {
            if (data.rows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="${data.columns.length || 1}" style="text-align: center; color: #94a3b8; padding: 1.5rem;">Query executed successfully with 0 matching rows.</td></tr>`;
            } else {
                tbody.innerHTML = data.rows.map(row => `
                    <tr>${row.map(val => `<td>${escapeHtml(val !== null ? val : 'NULL')}</td>`).join("")}</tr>
                `).join("");
            }
        }

        if (paginationInfo) {
            paginationInfo.textContent = `Page ${data.page} of ${data.total_pages || 1} (${data.rows.length} shown)`;
        }
        if (prevBtn) prevBtn.disabled = data.page <= 1;
        if (nextBtn) nextBtn.disabled = data.page >= data.total_pages;
    }

    const prevPageBtn = document.getElementById("sqlPrevPageBtn");
    if (prevPageBtn) {
        prevPageBtn.addEventListener("click", () => {
            if (currentSqlPage > 1) executeSqlQuery(currentSqlPage - 1);
        });
    }

    const nextPageBtn = document.getElementById("sqlNextPageBtn");
    if (nextPageBtn) {
        nextPageBtn.addEventListener("click", () => {
            if (currentSqlPage < currentSqlTotalPages) executeSqlQuery(currentSqlPage + 1);
        });
    }

    // View switcher (Table vs Chart)
    const viewTableBtn = document.getElementById("viewModeTableBtn");
    const viewChartBtn = document.getElementById("viewModeChartBtn");
    const sqlTableView = document.getElementById("sqlTableView");
    const sqlChartView = document.getElementById("sqlChartView");

    if (viewTableBtn && viewChartBtn) {
        viewTableBtn.addEventListener("click", () => {
            viewTableBtn.classList.add("active");
            viewChartBtn.classList.remove("active");
            if (sqlTableView) sqlTableView.style.display = "block";
            if (sqlChartView) sqlChartView.style.display = "none";
        });

        viewChartBtn.addEventListener("click", () => {
            viewChartBtn.classList.add("active");
            viewTableBtn.classList.remove("active");
            if (sqlTableView) sqlTableView.style.display = "none";
            if (sqlChartView) sqlChartView.style.display = "block";
            if (currentSqlResults) renderSqlChart(currentSqlResults);
        });
    }

    // Populate chart axis dropdowns
    function populateChartSelectors(data) {
        const xSelect = document.getElementById("chartXAxisSelect");
        const ySelect = document.getElementById("chartYAxisSelect");
        if (!xSelect || !ySelect) return;

        xSelect.innerHTML = "";
        ySelect.innerHTML = "";

        data.columns.forEach((c, idx) => {
            const optX = document.createElement("option");
            optX.value = idx;
            optX.textContent = c;
            xSelect.appendChild(optX);

            const optY = document.createElement("option");
            optY.value = idx;
            optY.textContent = c;
            ySelect.appendChild(optY);
        });

        if (data.columns.length > 1) {
            ySelect.selectedIndex = 1;
        }
    }

    // Render Bar Chart Visualization
    function renderSqlChart(data) {
        const grid = document.getElementById("sqlBarChartGrid");
        const xSelect = document.getElementById("chartXAxisSelect");
        const ySelect = document.getElementById("chartYAxisSelect");
        if (!grid || !data.rows || data.rows.length === 0) return;

        const xIdx = parseInt(xSelect?.value || 0);
        const yIdx = parseInt(ySelect?.value || 1);

        const chartRows = data.rows.slice(0, 20); // Top 20 bars
        const numericValues = chartRows.map(r => {
            const v = parseFloat(r[yIdx]);
            return isNaN(v) ? 0 : v;
        });

        const maxVal = Math.max(...numericValues, 1);

        grid.innerHTML = chartRows.map((r, i) => {
            const val = numericValues[i];
            const heightPct = Math.max(4, Math.round((val / maxVal) * 100));
            const label = r[xIdx] !== null ? String(r[xIdx]) : 'NULL';
            return `
                <div class="bar-item">
                    <span class="bar-val">${formatNum(val)}</span>
                    <div class="bar-fill" style="height: ${heightPct}%;"></div>
                    <span class="bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
                </div>
            `;
        }).join("");
    }

    const redrawChartBtn = document.getElementById("renderCustomChartBtn");
    if (redrawChartBtn) {
        redrawChartBtn.addEventListener("click", () => {
            if (currentSqlResults) renderSqlChart(currentSqlResults);
        });
    }

    // Explain Results asynchronously
    async function explainQueryResultsAsync(query, data) {
        const textEl = document.getElementById("sqlAiExplanationText");
        if (!textEl) return;

        textEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating evidence-grounded query insight...';

        try {
            const activeOpt = wbSelectEl?.selectedOptions[0];
            const domain = activeOpt?.dataset?.domain || "finance";

            const res = await fetch(`${API_URL}/api/query/explain`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    columns: data.columns,
                    rows: data.rows.slice(0, 5),
                    total_rows: data.total_rows >= 0 ? data.total_rows : data.row_count,
                    execution_time_ms: data.execution_time_ms,
                    domain
                })
            });

            const resData = await res.json();
            if (resData.success && resData.explanation) {
                textEl.innerHTML = `<strong>Insight:</strong> ${escapeHtml(resData.explanation.summary)}`;
            }
        } catch (e) {
            textEl.textContent = `Executed successfully in ${data.execution_time_ms}ms. Total matching rows: ${data.total_rows}.`;
        }
    }

    // Export query results to CSV
    const exportSqlCsvBtn = document.getElementById("exportSqlCsvBtn");
    if (exportSqlCsvBtn) {
        exportSqlCsvBtn.addEventListener("click", () => {
            if (!currentSqlResults || !currentSqlResults.rows) return;
            const rows = [currentSqlResults.columns, ...currentSqlResults.rows];
            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.map(val => `"${String(val !== null ? val : '').replace(/"/g, '""')}"`).join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `datadock_query_${Date.now()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    // ========================================================
    // VISUAL DATA EXPLORER LOGIC
    // ========================================================
    const visualDatasetSelect = document.getElementById("visualDatasetSelect");
    const visualColumnsList = document.getElementById("visualColumnsList");
    const visualGroupBySelect = document.getElementById("visualGroupBySelect");
    const visualAggColSelect = document.getElementById("visualAggColSelect");
    const visualAggFuncSelect = document.getElementById("visualAggFuncSelect");
    const visualOrderDirSelect = document.getElementById("visualOrderDirSelect");
    const visualLimitSelect = document.getElementById("visualLimitSelect");
    const visualSqlCode = document.getElementById("visualGeneratedSqlCode");
    const filtersContainer = document.getElementById("filtersContainer");

    let currentVisualSchema = null;

    if (visualDatasetSelect) {
        visualDatasetSelect.addEventListener("change", async () => {
            const dsId = visualDatasetSelect.value;
            if (!dsId) {
                if (visualColumnsList) visualColumnsList.innerHTML = '<span style="font-size: 0.82rem; color: #94a3b8;">Select a dataset first.</span>';
                return;
            }

            try {
                const res = await fetch(`${API_URL}/api/datasets/${encodeURIComponent(dsId)}/schema`);
                const data = await res.json();
                if (data.success && data.schema) {
                    currentVisualSchema = data.schema;
                    renderVisualColumns(data.schema.columns);
                    populateVisualSelects(data.schema.columns);
                    updateVisualSqlPreview();
                }
            } catch (e) {
                console.error("Failed to load visual explorer schema:", e);
            }
        });
    }

    function renderVisualColumns(columns) {
        if (!visualColumnsList) return;
        visualColumnsList.innerHTML = columns.map(c => `
            <label style="display: flex; align-items: center; gap: 0.35rem; font-size: 0.82rem; background: rgba(52,232,154,0.1); border: 1px solid rgba(52,232,154,0.25); padding: 0.25rem 0.6rem; border-radius: 6px; cursor: pointer;">
                <input type="checkbox" class="visual-col-check" value="${escapeHtml(c.name)}" checked>
                <span>${escapeHtml(c.name)}</span>
            </label>
        `).join("");

        document.querySelectorAll(".visual-col-check").forEach(chk => {
            chk.addEventListener("change", updateVisualSqlPreview);
        });
    }

    function populateVisualSelects(columns) {
        if (visualGroupBySelect) {
            visualGroupBySelect.innerHTML = '<option value="">-- No Grouping --</option>' +
                columns.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join("");
            visualGroupBySelect.addEventListener("change", updateVisualSqlPreview);
        }
        if (visualAggColSelect) {
            visualAggColSelect.innerHTML = '<option value="">-- Target Column --</option>' +
                columns.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join("");
            visualAggColSelect.addEventListener("change", updateVisualSqlPreview);
        }
        if (visualAggFuncSelect) {
            visualAggFuncSelect.addEventListener("change", updateVisualSqlPreview);
        }
        if (visualOrderDirSelect) {
            visualOrderDirSelect.addEventListener("change", updateVisualSqlPreview);
        }
        if (visualLimitSelect) {
            visualLimitSelect.addEventListener("change", updateVisualSqlPreview);
        }
    }

    const addFilterBtn = document.getElementById("addFilterRowBtn");
    if (addFilterBtn) {
        addFilterBtn.addEventListener("click", () => {
            if (!currentVisualSchema || !filtersContainer) return;
            const filterDiv = document.createElement("div");
            filterDiv.className = "filter-row";

            const colOptions = currentVisualSchema.columns.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join("");

            filterDiv.innerHTML = `
                <select class="filter-col" style="padding: 0.45rem; background: #032012; border: 1px solid rgba(52,232,154,0.3); border-radius: 6px; color: #fff;">
                    ${colOptions}
                </select>
                <select class="filter-op" style="padding: 0.45rem; background: #032012; border: 1px solid rgba(52,232,154,0.3); border-radius: 6px; color: #fff;">
                    <option value="=">=</option>
                    <option value="!=">!=</option>
                    <option value=">">&gt;</option>
                    <option value="<">&lt;</option>
                    <option value=">=">&gt;=</option>
                    <option value="<=">&lt;=</option>
                    <option value="LIKE">CONTAINS (LIKE)</option>
                    <option value="IS NULL">IS NULL</option>
                    <option value="IS NOT NULL">IS NOT NULL</option>
                </select>
                <input type="text" class="filter-val" placeholder="Value..." style="padding: 0.45rem; background: #032012; border: 1px solid rgba(52,232,154,0.3); border-radius: 6px; color: #fff;">
                <button type="button" class="btn-action remove-filter-btn" style="color: #f87171; border-color: rgba(239,68,68,0.4);"><i class="fa-solid fa-trash"></i></button>
            `;

            filtersContainer.appendChild(filterDiv);

            filterDiv.querySelector(".remove-filter-btn").addEventListener("click", () => {
                filterDiv.remove();
                updateVisualSqlPreview();
            });

            filterDiv.querySelectorAll("select, input").forEach(el => {
                el.addEventListener("input", updateVisualSqlPreview);
            });

            updateVisualSqlPreview();
        });
    }

    function updateVisualSqlPreview() {
        if (!visualSqlCode) return;
        const activeOpt = visualDatasetSelect?.selectedOptions[0];
        const tableName = activeOpt?.dataset?.tableName || "dataset";

        const checkedCols = Array.from(document.querySelectorAll(".visual-col-check:checked")).map(c => `"${c.value}"`);
        const groupByCol = visualGroupBySelect?.value;
        const aggFunc = visualAggFuncSelect?.value;
        const aggCol = visualAggColSelect?.value;
        const orderDir = visualOrderDirSelect?.value || "DESC";
        const limitVal = visualLimitSelect?.value || "50";

        let selectClause = "";
        let groupClause = "";

        if (groupByCol) {
            selectClause = `"${groupByCol}"`;
            if (aggFunc && aggCol) {
                selectClause += `, ${aggFunc}("${aggCol}") AS ${aggFunc.toLowerCase()}_${aggCol}`;
            } else if (aggFunc === "COUNT") {
                selectClause += `, COUNT(*) AS count`;
            }
            groupClause = ` GROUP BY "${groupByCol}"`;
        } else if (aggFunc && aggCol) {
            selectClause = `${aggFunc}("${aggCol}") AS ${aggFunc.toLowerCase()}_${aggCol}`;
        } else if (checkedCols.length > 0) {
            selectClause = checkedCols.join(", ");
        } else {
            selectClause = "*";
        }

        // Parse filters
        const filterRows = document.querySelectorAll(".filter-row");
        const whereClauses = [];
        filterRows.forEach(row => {
            const col = row.querySelector(".filter-col")?.value;
            const op = row.querySelector(".filter-op")?.value;
            const val = row.querySelector(".filter-val")?.value?.trim();

            if (col && op) {
                if (op === "IS NULL" || op === "IS NOT NULL") {
                    whereClauses.push(`"${col}" ${op}`);
                } else if (val) {
                    if (op === "LIKE") {
                        whereClauses.push(`"${col}" ILIKE '%${val.replace(/'/g, "''")}%'`);
                    } else if (!isNaN(val)) {
                        whereClauses.push(`"${col}" ${op} ${val}`);
                    } else {
                        whereClauses.push(`"${col}" ${op} '${val.replace(/'/g, "''")}'`);
                    }
                }
            }
        });

        const whereSql = whereClauses.length > 0 ? ` WHERE ${whereClauses.join(" AND ")}` : "";
        const orderSql = groupByCol ? ` ORDER BY 2 ${orderDir}` : ` ORDER BY 1 ${orderDir}`;
        const finalSql = `SELECT ${selectClause} FROM "${tableName}"${whereSql}${groupClause}${orderSql} LIMIT ${limitVal};`;

        visualSqlCode.textContent = finalSql;
        return finalSql;
    }

    // Open Visual SQL in SQL Workbench
    const openInWbBtn = document.getElementById("openVisualSqlInWorkbenchBtn");
    if (openInWbBtn) {
        openInWbBtn.addEventListener("click", () => {
            const sql = visualSqlCode?.textContent?.trim();
            const textarea = document.getElementById("sqlQueryTextarea");
            if (textarea && sql) textarea.value = sql;

            // Sync active dataset dropdown
            const dsId = visualDatasetSelect?.value;
            if (wbSelectEl && dsId) {
                wbSelectEl.value = dsId;
                wbSelectEl.dispatchEvent(new Event("change"));
            }

            activateTab("tab-sql", true);
        });
    }

    // Execute Visual Query directly
    const runVisualBtn = document.getElementById("runVisualQueryBtn");
    if (runVisualBtn) {
        runVisualBtn.addEventListener("click", async () => {
            const sql = updateVisualSqlPreview();
            const container = document.getElementById("visualResultsContainer");
            const thead = document.getElementById("visualResultsHead");
            const tbody = document.getElementById("visualResultsBody");
            const countBadge = document.getElementById("visualResultsCountBadge");

            if (!sql) return;

            try {
                runVisualBtn.disabled = true;
                runVisualBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Executing...';

                const dsId = visualDatasetSelect?.value;
                const res = await fetch(`${API_URL}/api/query/execute`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: sql, dataset_id: dsId || null, page: 1, page_size: 50 })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Query failed");

                if (container) container.style.display = "block";
                if (countBadge) countBadge.textContent = `${data.total_rows >= 0 ? data.total_rows : data.row_count} rows in ${data.execution_time_ms}ms`;

                if (thead) thead.innerHTML = `<tr>${data.columns.map(c => `<th>${escapeHtml(c)}</th>`).join("")}</tr>`;
                if (tbody) {
                    tbody.innerHTML = data.rows.map(row => `
                        <tr>${row.map(v => `<td>${escapeHtml(v !== null ? v : 'NULL')}</td>`).join("")}</tr>
                    `).join("");
                }
            } catch (e) {
                alert("Visual query error: " + e.message);
            } finally {
                runVisualBtn.disabled = false;
                runVisualBtn.innerHTML = '<i class="fa-solid fa-play"></i> Execute Visual Query';
            }
        });
    }

    // ========================================================
    // EXTERNAL DATASET DISCOVERY LOGIC
    // ========================================================
    let allDiscoveryCatalog = [];

    async function loadDiscoveryCatalogue(query = "", domain = "") {
        const grid = document.getElementById("discoveryCatalogueGrid");
        if (!grid) return;

        grid.innerHTML = '<p style="color: #7affbf;"><i class="fa-solid fa-spinner fa-spin"></i> Loading external catalogues...</p>';

        try {
            const res = await fetch(`${API_URL}/api/external-sources/search?query=${encodeURIComponent(query)}&domain=${encodeURIComponent(domain)}`);
            const data = await res.json();

            if (data.success && data.results) {
                allDiscoveryCatalog = data.results;
                renderDiscoveryCards(data.results);
            }
        } catch (e) {
            grid.innerHTML = `<p style="color: #f87171;">Failed to fetch external catalogues: ${escapeHtml(e.message)}</p>`;
        }
    }

    function renderDiscoveryCards(catalogue) {
        const grid = document.getElementById("discoveryCatalogueGrid");
        if (!grid) return;

        if (catalogue.length === 0) {
            grid.innerHTML = '<p style="color: #94a3b8; grid-column: 1/-1;">No external datasets match your search filter.</p>';
            return;
        }

        grid.innerHTML = catalogue.map(item => `
            <div class="discovery-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem;">
                    <span class="discovery-badge"><i class="fa-solid fa-cloud"></i> ${escapeHtml(item.domain)}</span>
                    <span style="font-size: 0.72rem; color: #94a3b8;"><i class="fa-solid fa-scale-balanced"></i> ${escapeHtml(item.license.split('(')[0])}</span>
                </div>

                <div>
                    <h3 style="font-size: 1rem; color: #ffffff; margin-bottom: 0.4rem; font-family: 'Space Grotesk', sans-serif;">
                        ${escapeHtml(item.title)}
                    </h3>
                    <p style="font-size: 0.82rem; color: #94a3b8; line-height: 1.4;">
                        ${escapeHtml(item.description)}
                    </p>
                </div>

                <div style="font-size: 0.78rem; color: #7affbf; background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 8px;">
                    <div><strong>Source:</strong> ${escapeHtml(item.source)}</div>
                    <div><strong>Columns:</strong> ${escapeHtml(item.sample_columns.join(", "))}</div>
                    <div><strong>Est. Rows:</strong> ~${item.row_count_estimate}</div>
                </div>

                <div style="display: flex; gap: 0.5rem;">
                    <button type="button" class="btn-primary import-external-btn" data-id="${escapeHtml(item.id)}" style="flex: 1; padding: 0.5rem; font-size: 0.82rem;">
                        <i class="fa-solid fa-cloud-arrow-down"></i> Import to Workspace
                    </button>
                </div>
            </div>
        `).join("");

        document.querySelectorAll(".import-external-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const datasetId = btn.dataset.id;
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...';

                try {
                    const res = await fetch(`${API_URL}/api/external-sources/import`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ dataset_id: datasetId, user_email: userEmail })
                    });
                    const data = await res.json();
                    if (data.success) {
                        alert(data.message);
                        loadHistory();
                        loadWorkbenchDatasets();
                        btn.innerHTML = '<i class="fa-solid fa-check"></i> Imported';
                    } else {
                        alert(data.detail || "Import failed.");
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Import to Workspace';
                    }
                } catch (e) {
                    alert("Import error: " + e.message);
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Import to Workspace';
                }
            });
        });
    }

    const discoverySearch = document.getElementById("discoverySearchInput");
    if (discoverySearch) {
        discoverySearch.addEventListener("input", () => {
            const q = discoverySearch.value.trim().toLowerCase();
            const filtered = allDiscoveryCatalog.filter(c =>
                c.title.toLowerCase().includes(q) || c.description.toLowerCase().includes(q)
            );
            renderDiscoveryCards(filtered);
        });
    }

    document.querySelectorAll("[data-discovery-domain]").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("[data-discovery-domain]").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const domain = btn.dataset.discoveryDomain;
            loadDiscoveryCatalogue(discoverySearch?.value || "", domain === "all" ? "" : domain);
        });
    });

    // ========================================================
    // REPRODUCIBLE ANALYSIS & QUERY LINEAGE LOGIC
    // ========================================================
    async function loadSavedQueries() {
        const listContainer = document.getElementById("savedQueriesList");
        if (!listContainer) return;

        try {
            const res = await fetch(`${API_URL}/api/queries?user_email=${encodeURIComponent(userEmail)}`);
            const data = await res.json();

            if (data.success && data.queries.length > 0) {
                listContainer.innerHTML = data.queries.map(q => `
                    <div class="lineage-card">
                        <div>
                            <strong style="color: #ffffff; font-size: 0.95rem;">${escapeHtml(q.query_name)}</strong>
                            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem;">
                                <span><i class="fa-solid fa-database"></i> ${escapeHtml(q.dataset_name || 'dataset')} (v${escapeHtml(q.dataset_version || '1')})</span> • 
                                <span><i class="fa-regular fa-clock"></i> Saved: ${escapeHtml(q.created_at)}</span>
                            </div>
                            <code style="display: block; font-size: 0.78rem; color: #7affbf; margin-top: 0.4rem; font-family: monospace;">${escapeHtml(q.query_sql)}</code>
                        </div>

                        <div style="display: flex; gap: 0.5rem;">
                            <button type="button" class="btn-action run-saved-wb-btn" data-sql="${escapeHtml(q.query_sql)}" data-ds="${escapeHtml(q.dataset_id || '')}">
                                <i class="fa-solid fa-terminal"></i> Edit in Workbench
                            </button>
                            <button type="button" class="btn-primary rerun-saved-btn" data-id="${q.id}">
                                <i class="fa-solid fa-rotate-right"></i> Rerun Analysis
                            </button>
                        </div>
                    </div>
                `).join("");

                document.querySelectorAll(".run-saved-wb-btn").forEach(btn => {
                    btn.addEventListener("click", () => {
                        const sql = btn.dataset.sql;
                        const dsId = btn.dataset.ds;
                        const textarea = document.getElementById("sqlQueryTextarea");
                        if (textarea) textarea.value = sql;
                        if (wbSelectEl && dsId) {
                            wbSelectEl.value = dsId;
                            wbSelectEl.dispatchEvent(new Event("change"));
                        }
                        activateTab("tab-sql", true);
                    });
                });

                document.querySelectorAll(".rerun-saved-btn").forEach(btn => {
                    btn.addEventListener("click", async () => {
                        const queryId = btn.dataset.id;
                        btn.disabled = true;
                        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Rerunning...';

                        try {
                            const res = await fetch(`${API_URL}/api/queries/${queryId}/rerun`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ user_email: userEmail })
                            });
                            const data = await res.json();
                            if (data.success) {
                                alert(`Query '${data.query_name}' reran successfully on '${data.target_dataset}'!\nResult Count: ${data.execution.total_rows} rows.\nRow Delta vs Previous: ${data.lineage.row_delta_vs_previous} rows.`);
                                loadLineageHistory();
                            } else {
                                alert(data.detail || "Rerun failed.");
                            }
                        } catch (e) {
                            alert("Rerun error: " + e.message);
                        } finally {
                            btn.disabled = false;
                            btn.innerHTML = '<i class="fa-solid fa-rotate-right"></i> Rerun Analysis';
                        }
                    });
                });
            } else {
                listContainer.innerHTML = '<p style="font-size: 0.85rem; color: #94a3b8;">No saved queries yet. Save a query in the SQL Workbench to rerun or track lineage.</p>';
            }
        } catch (e) {
            console.error("Failed to load saved queries:", e);
        }
    }

    async function loadLineageHistory() {
        const listContainer = document.getElementById("lineageHistoryList");
        if (!listContainer) return;

        try {
            const res = await fetch(`${API_URL}/api/analysis/history?user_email=${encodeURIComponent(userEmail)}`);
            const data = await res.json();

            if (data.success && data.history.length > 0) {
                listContainer.innerHTML = data.history.map(item => `
                    <div style="padding: 0.9rem 1.2rem; background: rgba(0,0,0,0.3); border: 1px solid rgba(52,232,154,0.15); border-radius: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.6rem;">
                        <div>
                            <strong style="color: #ffffff; font-size: 0.9rem;">${escapeHtml(item.query_name)}</strong>
                            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem;">
                                <span>Dataset: <strong>${escapeHtml(item.dataset_name)}</strong> (v${escapeHtml(item.dataset_version)})</span> • 
                                <span>Executed: ${escapeHtml(item.executed_at)}</span>
                            </div>
                        </div>
                        <div style="display: flex; gap: 1rem; align-items: center; font-size: 0.82rem;">
                            <span style="color: #7affbf;"><i class="fa-solid fa-table-cells"></i> ${item.row_count.toLocaleString()} rows</span>
                            <span style="color: #cbd5e1;"><i class="fa-solid fa-bolt"></i> ${item.execution_time_ms} ms</span>
                        </div>
                    </div>
                `).join("");
            } else {
                listContainer.innerHTML = '<p style="font-size: 0.85rem; color: #94a3b8;">Execution logs will appear here when you run or rerun queries.</p>';
            }
        } catch (e) {
            console.error("Failed to load lineage history:", e);
        }
    }

    // Initial load of new features
    loadHistory();
    loadWorkbenchDatasets();
    loadDiscoveryCatalogue();
    loadSavedQueries();
    loadLineageHistory();


});
