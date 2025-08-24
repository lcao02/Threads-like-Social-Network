document.addEventListener("DOMContentLoaded", () => {

    // --- Handle Like/Unlike ---
    document.querySelectorAll(".like-btn").forEach(button => {
        button.addEventListener("click", () => {
            const postId = button.dataset.id;

            fetch(`/like/${postId}`, {
                method: "PUT",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
            })
            .then(response => response.json())
            .then(data => {
                // Update like count in DOM
                button.closest(".post").querySelector(".like-count").innerText = data.likes;

                // Toggle button text
                button.innerText = data.liked ? "Unlike" : "Like";
            })
            .catch(err => console.error("Like error:", err));
        });
    });

    // --- Handle Edit ---
    document.querySelectorAll(".edit-btn").forEach(button => {
        button.addEventListener("click", () => {
            const postId = button.dataset.id;
            const postDiv = document.querySelector(`#post-${postId}`);
            const contentP = postDiv.querySelector(".content");
            const originalContent = contentP.innerText;

            // Replace text with textarea
            const textarea = document.createElement("textarea");
            textarea.classList.add("edit-textarea");
            textarea.value = originalContent;
            contentP.replaceWith(textarea);

            // Replace Edit button with Save button
            const saveBtn = document.createElement("button");
            saveBtn.innerText = "Save";
            button.replaceWith(saveBtn);

            saveBtn.addEventListener("click", () => {
                fetch(`/edit/${postId}`, {
                    method: "PUT",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ content: textarea.value })
                })
                .then(response => response.json())
                .then(data => {
                    // Restore content + Edit button
                    const newContent = document.createElement("p");
                    newContent.classList.add("content");
                    newContent.innerText = data.content;
                    textarea.replaceWith(newContent);

                    button.innerText = "Edit";
                    saveBtn.replaceWith(button);
                })
                .catch(err => console.error("Edit error:", err));
            });
        });
    });

});

// --- Helper to get CSRF Token ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
