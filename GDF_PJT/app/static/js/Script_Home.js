function toggleDropdown(codigo) {
  // Obtemos o dropdown e o botão correspondente pelo ID
  const dropdown = document.getElementById(`dropdown-${codigo}`);
  const button = document.querySelector(
    `button[name="codigo"][value="${codigo}"]`
  );

  // Alterna a classe 'active' no dropdown
  dropdown.classList.toggle("active");

  // Alterna a classe 'active' no botão
  button.classList.toggle("active");

  // Fecha outros dropdowns e remove a classe 'active' dos outros botões
  const allDropdowns = document.querySelectorAll(".dropdown-content");
  const allButtons = document.querySelectorAll(".btn_home");

  allDropdowns.forEach(function (dropdownItem) {
    if (dropdownItem !== dropdown) {
      dropdownItem.classList.remove("active");
    }
  });

  allButtons.forEach(function (buttonItem) {
    if (buttonItem !== button) {
      buttonItem.classList.remove("active");
    }
  });
}

// Função para fechar outros dropdowns quando um novo for aberto
document.addEventListener("click", function (event) {
  // Verifica se o clique foi fora de qualquer dropdown
  if (!event.target.closest(".dropdown")) {
    const dropdowns = document.querySelectorAll(".dropdown-content");
    dropdowns.forEach(function (dropdown) {
      dropdown.classList.remove("active");
    });
    const buttons = document.querySelectorAll(".btn_home");
    buttons.forEach(function (button) {
      button.classList.remove("active");
    });
  }
});
