// const output = document.getElementById("output");

// console.log("script loaded ✅");

// document.getElementById("getBtn").addEventListener("click", () => {
//     console.log("Get button clicked");

//     fetch("http://127.0.0.1:5000/api/hello")
//         .then(res => {
//             console.log("Response received");
//             return res.json();
//         })
//         .then(data => {
//             console.log(data);
//             output.innerText = data.message;
//         })
//         .catch(err => console.error("Error:", err));
// });


// // POST request
// document.getElementById("sendBtn").addEventListener("click", () => {
//     fetch("http://127.0.0.1:5000/api/send", {
//         method: "POST",
//         headers: {
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify({
//             name: "Durgesh",
//             project: "Flask Frontend Backend"
//         })
//     })
//     .then(res => res.json())
//     .then(data => {
//         console.log(data);
//         alert("Data sent successfully ✅");
//     });
// });


async function uploadPDF() {
    const button = document.getElementById("uploadBtn");
    const fileInput = document.getElementById("pdfFile");
    const loader = document.getElementById("loader");
    const result = document.getElementById("result");
    const progress = document.getElementById("progress");

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
            body: formData
        });

        const data = await response.json();   //converts the raw computer data into a readable JavaScript object (usually containing the AI's answer).
        clearInterval(interval);
        progress.style.width = "100%";

        if (data.error) {
            result.textContent = data.error;
        } else {
            result.innerHTML = markdownToHtml(data.ai_response);
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


    function markdownToHtml(text) {
    return text
        // Headings
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        // Bullet points
        .replace(/^\* (.*)$/gm, "<li>$1</li>")
        // Wrap lists
        .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
        // Line breaks
        .replace(/\n/g, "<br>");
}

}
