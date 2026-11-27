
document.addEventListener("DOMContentLoaded", () => {

    const forms = document.querySelectorAll(
        "form[data-confirm]"
    );

    forms.forEach((form) => {

        form.addEventListener("submit", (event) => {

            const message =
                form.dataset.confirm || "Are you sure?";

            const confirmed = window.confirm(message);

            if (!confirmed) {
                event.preventDefault();
            }

        });

    });

});
