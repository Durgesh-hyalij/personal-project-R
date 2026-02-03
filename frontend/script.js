const API_BASE = "http://127.0.0.1:5000";

// --- GLOBAL AUTH UTILS ---
function getToken() { return localStorage.getItem('token'); }

function requireAuth() {
    if (!getToken()) { window.location.href = "login.html"; }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = "login.html";
}

// ==========================================
//  PAGE: REGISTER (Debug Version)
// ==========================================
const registerForm = document.getElementById("registerForm");
if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        console.log("Register button clicked..."); // DEBUG

        const name = document.getElementById("name").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        // Visual Feedback
        const btn = e.target.querySelector("button");
        const originalText = btn.innerText;
        btn.innerText = "Creating Account...";
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();

            if (data.success) {
                alert("Success! Account created. Please log in.");
                window.location.href = "login.html";
            } else {
                alert("Error: " + data.error);
                btn.innerText = originalText;
                btn.disabled = false;
            }
        } catch (err) {
            console.error(err);
            alert("Connection Failed. Is the backend server running?");
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });
}

// ==========================================
//  PAGE: LOGIN
// ==========================================
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (data.success) {
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                window.location.href = "dashboard.html"; 
            } else {
                alert(data.error);
            }
        } catch (err) {
            alert("Login failed. Check console for details.");
        }
    });
}

// ==========================================
//  PAGE: UPLOAD & HISTORY (Existing Code)
// ==========================================
// ... (Keep the rest of your script.js logic for upload and history same as before) ...
const fileInput = document.getElementById("pdfFile");
if (fileInput) {
    requireAuth();
    fileInput.addEventListener("change", async (e) => {
        // ... (Paste your existing upload logic here) ...
        const file = e.target.files[0];
        if (!file) return;

        const loader = document.getElementById("loader");
        const progress = document.getElementById("progress");
        const uploadBox = document.querySelector(".upload-box");
        
        loader.classList.add("active");
        uploadBox.style.pointerEvents = "none"; 
        uploadBox.style.opacity = "0.6";

        let percent = 0;
        progress.style.width = "0%";
        const interval = setInterval(() => {
            if (percent < 90) { percent += 10; progress.style.width = percent + "%"; }
        }, 200);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch(`${API_BASE}/upload-report`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${getToken()}` },
                body: formData
            });
            const data = await res.json();

            clearInterval(interval);
            progress.style.width = "100%";

            if (data.success) {
                document.getElementById("uploadSection").style.display = "none";
                document.getElementById("resultSection").style.display = "block";
                document.getElementById("aiOutput").innerHTML = marked.parse(data.ai_response);
                const dlBtn = document.getElementById("dlBtn");
                if(dlBtn) dlBtn.onclick = () => downloadFile(data.report_id);
            } else {
                alert(data.error || "Upload failed");
                resetUI(); 
            }
        } catch (err) {
            console.error(err);
            alert("Server connection failed.");
            resetUI();
        }
        function resetUI() {
            clearInterval(interval);
            loader.classList.remove("active");
            progress.style.width = "0%";
            uploadBox.style.pointerEvents = "auto";
            uploadBox.style.opacity = "1";
            fileInput.value = "";
        }
    });
}

async function downloadFile(id) {
    try {
        const res = await fetch(`${API_BASE}/download-pdf/${id}`, {
            headers: { "Authorization": `Bearer ${getToken()}` }
        });
        if(res.status === 401) { logout(); return; }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = "Medical_Summary.pdf";
        document.body.appendChild(a); a.click(); a.remove();
    } catch(err) { alert("Download failed"); }
}

async function loadHistory() {
    requireAuth();
    const listContainer = document.getElementById("historyList");
    if (!listContainer) return;
    try {
        const res = await fetch(`${API_BASE}/history`, { headers: { "Authorization": `Bearer ${getToken()}` } });
        if(res.status === 401) { logout(); return; }
        const data = await res.json();
        listContainer.innerHTML = ""; 
        const header = document.querySelector(".sidebar-header");
        if(header && !document.getElementById("logoutBtn")) {
             header.innerHTML += ` <span id="logoutBtn" style="float:right; cursor:pointer; color: #ef4444;">(Logout)</span>`;
             document.getElementById("logoutBtn").onclick = logout;
        }
        if (data.data.length === 0) { listContainer.innerHTML = `<div style="padding:20px; text-align:center; color:#94a3b8; font-size:0.9rem;">No reports found.</div>`; return; }
        data.data.forEach(report => {
            const div = document.createElement("div"); div.className = "report-item";
            div.innerHTML = `<h4>${report.pdf_name}</h4><span>📅 ${report.date}</span>`;
            div.onclick = () => viewReport(report.id, div);
            listContainer.appendChild(div);
        });
    } catch (err) { listContainer.innerHTML = `<p style="color:red; padding:10px;">Server Error</p>`; }
}

async function viewReport(id, element) {
    document.querySelectorAll(".report-item").forEach(el => el.classList.remove("active"));
    element.classList.add("active");
    try {
        const res = await fetch(`${API_BASE}/history/${id}`, { headers: { "Authorization": `Bearer ${getToken()}` } });
        const data = await res.json();
        if (data.success) {
            const r = data.data;
            document.getElementById("emptyState").style.display = "none";
            document.getElementById("contentState").style.display = "block";
            document.getElementById("reportTitle").innerText = r.pdf_name;
            document.getElementById("reportBody").innerHTML = marked.parse(r.ai_summary);
            document.getElementById("btnDownload").onclick = () => downloadFile(r.id);
            document.getElementById("btnDelete").onclick = async () => {
                if (confirm("Permanently delete this report?")) {
                    await fetch(`${API_BASE}/history/${r.id}`, { method: "DELETE", headers: { "Authorization": `Bearer ${getToken()}` } });
                    document.getElementById("contentState").style.display = "none";
                    document.getElementById("emptyState").style.display = "block";
                    loadHistory();
                }
            };
        }
    } catch (err) { alert("Failed to load report details."); }
}