function toggleMenu() {
    var dropdown = document.getElementById("userDropdown");
    if (dropdown.style.display === "block") {
        dropdown.style.display = "none";
    } else {
        dropdown.style.display = "block";
    }
}

// Cierra el menú si se hace clic fuera
window.onclick = function (event) {
    if (!event.target.closest(".user-menu")) {
        document.getElementById("userDropdown").style.display = "none";
    }
};
