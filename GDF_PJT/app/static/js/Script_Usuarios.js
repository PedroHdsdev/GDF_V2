document.addEventListener("DOMContentLoaded", () => {
    initUsuarioIns();
    initUsuarioUpd();
});

/* ===============================
   INS – iNSERT USER
================================ */
function initUsuarioIns() {
    const btnCadastrar = document.querySelector(
        'button[data-bs-target="#modalUsuarioIns"]'
    );

    if (!btnCadastrar) return;

    btnCadastrar.addEventListener("click", () => {
        const modalEl = document.getElementById("modalUsuarioIns");
        if (!modalEl) return;

        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    });
}

/* ===============================
   UPD – UPDATE USER
================================ */
function initUsuarioUpd() {
    const rows = document.querySelectorAll(".user-row");
    const modalEl = document.getElementById("modalUsuarioUpd");

    if (!rows.length || !modalEl) return;

    rows.forEach(row => {
        row.addEventListener("click", () => {
            const userId = row.dataset.userId;
            if (!userId) return;

            /**
             * AQUI AINDA NÃO TEM FETCH
             * Apenas abre o modal.
             * No próximo passo vamos buscar os dados do usuário.
             */
            document.getElementById("upd_user_id").value = userId;

            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        });
    });
}
