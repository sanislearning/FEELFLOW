document.addEventListener("DOMContentLoaded", function () {
    const body = document.body;
    const colors = ["#1e1e2e", "#89b4fa", "#cba6f7", "#f5e0dc"]; // Catppuccin Mocha shades
    let index = 0;

    function changeBackground() {
        index = (index + 1) % colors.length;
        const nextIndex = (index + 1) % colors.length;
        body.style.background = `linear-gradient(45deg, ${colors[index]}, ${colors[nextIndex]})`;
    }

    setInterval(changeBackground, 5000); // Change color every 5 seconds
});
