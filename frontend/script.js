    const token = localStorage.getItem('token');
    console.log(`here is ur token ${token}`)
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    console.log(`here is ur user ${user}`)

    // ==============================
    // AUTH CHECK
    // ==============================
    if (!token || !user) {
        window.location.href = 'login.html';
    }

    // Show admin link if admin
    if (user.is_admin) {
        document.getElementById('nav-links').innerHTML = `
            <span class="navbar-text">Hello, ${user.username}</span>
            <a class="nav-link" href="admin.html">Admin</a>
            <a class="nav-link" href="login.html" onclick="logout()">Logout</a>
        `;
    console.log(`your code is inside the user.is_admin`)

    } else {
        document.getElementById('user-info').textContent =
            `Hello, ${user.username}`;
    console.log(`your code is inside the else`)

    }
        
async function uploadPDF() {
    const button = document.getElementById("uploadBtn");
    const fileInput = document.getElementById("pdfFile");
    const loader = document.getElementById("loader");
    const result = document.getElementById("result");
    const progress = document.getElementById("progress");
    const actionButtons = document.getElementById('action-buttons');
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || 'null');

    if (!fileInput.files.length) {
        alert("Please select a PDF file");
        return;
    }

    const formData = new FormData();       // Prepares the file for a POST request (multipart/form-data)
    formData.append("file", fileInput.files[0]);

    // UI state
    button.disabled = true;
    loader.classList.remove("hidden");
    result.textContent = "";
    progress.style.width = "0%";

    // Simulates a loading bar that climbs to 90% while waiting for the server
    // Fake progress animation
    let percent = 0;
    const interval = setInterval(() => {
        if (percent < 90) {
            percent += 5;
            progress.style.width = percent + "%";
        }
    }, 300);

    try {           // Sends the file to the server
        const response = await fetch("http://127.0.0.1:5000/upload-report", {
            method: "POST",
            headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
  body: formData
        });

        const data = await response.json();   //converts the raw computer data into a readable JavaScript object (usually containing the AI's answer).
        clearInterval(interval);
        progress.style.width = "100%";

        if (data.error) {
            result.textContent = data.error;
        } else {
            // result.innerHTML = markdownToHtml(data.ai_response);
            result.innerHTML = marked.parse(data.ai_response);
        }

    } catch (error) {
        clearInterval(interval);
        result.textContent = "Server error. Please try again.";
    }

    // Reset UI
    setTimeout(() => {
        loader.classList.add("hidden");
        button.disabled = false;
        progress.style.width = "0%";
    }, 600);


//     function markdownToHtml(text) {
//     return text
//         // Headings
//         .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
//         // Bullet points
//         .replace(/^\* (.*)$/gm, "<li>$1</li>")
//         // Wrap lists
//         .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
//         // Line breaks
//         .replace(/\n/g, "<br>");
// }
function logout() {
        localStorage.clear();
        window.location.href = 'login.html';
    }

 function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
