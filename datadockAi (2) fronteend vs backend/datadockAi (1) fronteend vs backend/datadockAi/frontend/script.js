// ========================================
// DATADOCK AI - SCRIPT.JS
// General Frontend Script
// ========================================


// ========================================
// PAGE LOAD
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("DataDock AI frontend loaded.");

});


// ========================================
// CHECK LOGIN STATUS
// ========================================

function isUserLoggedIn() {

    return localStorage.getItem("isLoggedIn") === "true";

}


// ========================================
// GET LOGGED-IN USER EMAIL
// ========================================

function getUserEmail() {

    return localStorage.getItem("userEmail");

}


// ========================================
// LOGOUT
// ========================================

function logout() {

    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("userEmail");

    window.location.href = "index.html";

}


// ========================================
// PROTECT DASHBOARD
// ========================================

function protectDashboard() {

    if (!isUserLoggedIn()) {

        window.location.href = "index.html";

    }

}


// ========================================
// DISPLAY USER EMAIL
// ========================================

function displayUserEmail(elementId) {

    const element =
        document.getElementById(elementId);

    if (element) {

        const email = getUserEmail();

        if (email) {

            element.textContent = email;

        }

    }

}