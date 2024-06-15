// Improved JavaScript with better naming conventions and organization
const spinner = document.getElementById("progress");

function showSpinner() {
    spinner.style.display = "block";
}

function hideSpinner() {
    spinner.style.display = "none";
}

window.addEventListener("load", showSpinner);
window.addEventListener("DOMContentLoaded", hideSpinner);