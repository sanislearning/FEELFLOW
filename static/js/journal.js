document.addEventListener("DOMContentLoaded", function () {
    const calendar = document.getElementById("calendar");
    const currentMonthText = document.getElementById("current-month");
    const prevBtn = document.getElementById("prev-month");
    const nextBtn = document.getElementById("next-month");
    const themeToggle = document.getElementById("theme-toggle");
    const root = document.documentElement;

    let currentDate = new Date();

    function renderCalendar() {
        calendar.innerHTML = ""; // Clear previous month
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        currentMonthText.innerText = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });

        // Add empty placeholders for first week
        for (let i = 0; i < firstDay; i++) {
            let emptyDiv = document.createElement("div");
            emptyDiv.classList.add("calendar-day");
            emptyDiv.style.visibility = "hidden"; // Hide empty spaces
            calendar.appendChild(emptyDiv);
        }

        // Fill in actual days
        for (let day = 1; day <= daysInMonth; day++) {
            let dayDiv = document.createElement("div");
            dayDiv.classList.add("calendar-day");
            dayDiv.innerText = day;

            // Format date as YYYY-MM-DD
            const dateString = `${year}-${(month + 1).toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;

            // Mark logged-in days (assuming loggedInDates is defined somewhere)
            if (typeof loggedInDates !== "undefined" && loggedInDates.includes(dateString)) {
                dayDiv.classList.add("logged-in");
            }

            calendar.appendChild(dayDiv);
        }
    }

    // Ensure year changes correctly when moving across months
    prevBtn.addEventListener("click", function () {
        if (currentDate.getMonth() === 0) {
            currentDate.setFullYear(currentDate.getFullYear() - 1);
            currentDate.setMonth(11);
        } else {
            currentDate.setMonth(currentDate.getMonth() - 1);
        }
        renderCalendar();
    });

    nextBtn.addEventListener("click", function () {
        if (currentDate.getMonth() === 11) {
            currentDate.setFullYear(currentDate.getFullYear() + 1);
            currentDate.setMonth(0);
        } else {
            currentDate.setMonth(currentDate.getMonth() + 1);
        }
        renderCalendar();
    });

    // Theme Toggle Functionality
    function toggleTheme() {
        if (root.classList.contains("light-mode")) {
            root.classList.remove("light-mode");
            localStorage.setItem("theme", "dark");
        } else {
            root.classList.add("light-mode");
            localStorage.setItem("theme", "light");
        }
    }

    // Load theme from localStorage
    if (localStorage.getItem("theme") === "light") {
        root.classList.add("light-mode");
    }

    themeToggle.addEventListener("click", toggleTheme);

    renderCalendar();
});
