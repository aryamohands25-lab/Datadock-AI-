const API_URL = window.DATADOCK_API_URL;

document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("registerForm");
    const message = document.getElementById("registerMessage");
    const button = document.getElementById("registerButton");

    form.addEventListener("submit", async (event) => {

        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword =
            document.getElementById("confirmPassword").value;

        // Check passwords
        if (password !== confirmPassword) {
            message.textContent = "Passwords do not match.";
            message.style.color = "red";
            return;
        }

        button.disabled = true;
        button.textContent = "Creating Account...";
        message.textContent = "";

        try {

            const response = await fetch(`${API_URL}/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {

                message.textContent =
                    "Registration successful! Redirecting to login...";

                message.style.color = "green";

                // Go to login page after 1.5 seconds
                setTimeout(() => {
                    window.location.href = "index.html";
                }, 1500);

            } else {

                message.textContent =
                    data.detail || "Registration failed.";

                message.style.color = "red";

            }

        } catch (error) {

            console.error("Registration error:", error);

            message.textContent =
                "Cannot connect to backend. Make sure FastAPI is running.";

            message.style.color = "red";

        } finally {

            button.disabled = false;
            button.textContent = "Create Account";

        }

    });

});