/** Prefixo da aplicação (ex: '' ou '/gdf') para URLs quando o app está em subpath. */
function getUrlPrefix() {
  var el = document.querySelector('.layout-page[data-url-prefix], [data-url-prefix]');
  var prefix = (el && el.getAttribute('data-url-prefix')) || '';
  if (!prefix && typeof window !== 'undefined' && window.location && window.location.pathname) {
    var p = window.location.pathname;
    if (p === '/gdf' || (p.length > 4 && p.indexOf('/gdf/') === 0)) return '/gdf';
  }
  return prefix || '';
}

document.addEventListener("DOMContentLoaded", function () {
  const menuButton = document.querySelector(".btn_menu");
  const sidebar = document.getElementById("sidebar");
  const menuItems = document.querySelectorAll(".menu-item");

  if (menuButton && sidebar) {
    menuButton.addEventListener("click", function () {
      sidebar.classList.toggle("hidden");
      sidebar.classList.toggle("visible");
    });
  }

  // Gerenciar submenus
  menuItems.forEach((item) => {
    if (!item) return;
    item.addEventListener("click", function (event) {
      event.preventDefault(); // Evita comportamento padrão de links

      const targetSubmenuId = this.dataset.target; // Obtém o ID do submenu associado
      if (targetSubmenuId) {
        const targetSubmenu = document.getElementById(targetSubmenuId);

        // Fecha outros submenus antes de abrir o atual
        document.querySelectorAll(".submenu.visible").forEach((submenu) => {
          if (submenu !== targetSubmenu) {
            submenu.classList.remove("visible");
            submenu.classList.add("hidden");
          }
        });

        // Alterna visibilidade do submenu
        if (targetSubmenu.classList.contains("hidden")) {
          targetSubmenu.classList.remove("hidden");
          targetSubmenu.classList.add("visible");
        }
         else {
          targetSubmenu.classList.remove("visible");
          targetSubmenu.classList.add("hidden");
        }
      }
    });
  });
});
