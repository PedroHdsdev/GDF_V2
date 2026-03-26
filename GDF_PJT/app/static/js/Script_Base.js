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

  initSidebarHoverAndSubmenus();
});

/**
 * Sidebar (offcanvas): abre ao passar o mouse no botão hambúrguer; fecha ao sair do botão/painel.
 * Itens com submenus abrem ao passar o mouse na linha; clique continua funcionando (toque/teclado).
 */
function initSidebarHoverAndSubmenus() {
  if (typeof bootstrap === "undefined") return;

  var sidebarEl = document.getElementById("sidebar");
  var toggleBtn = document.querySelector(".sidebar-toggle-btn");
  if (!sidebarEl || !toggleBtn) return;

  var offcanvas = bootstrap.Offcanvas.getOrCreateInstance(sidebarEl);
  var closeSidebarTimer = null;
  var closeSubTimer = null;
  var hoverSidebarDelay = 220;
  var hoverSubDelay = 180;
  var prefersHover =
    typeof window.matchMedia === "function" &&
    window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  function cancelSidebarClose() {
    if (closeSidebarTimer) {
      clearTimeout(closeSidebarTimer);
      closeSidebarTimer = null;
    }
  }

  function scheduleSidebarClose() {
    cancelSidebarClose();
    closeSidebarTimer = setTimeout(function () {
      offcanvas.hide();
    }, hoverSidebarDelay);
  }

  function openSidebar() {
    cancelSidebarClose();
    offcanvas.show();
  }

  toggleBtn.addEventListener("click", function () {
    offcanvas.toggle();
  });

  if (prefersHover) {
    toggleBtn.addEventListener("mouseenter", openSidebar);
    toggleBtn.addEventListener("mouseleave", function (ev) {
      var to = ev.relatedTarget;
      if (to && (sidebarEl.contains(to) || toggleBtn.contains(to))) return;
      scheduleSidebarClose();
    });
    sidebarEl.addEventListener("mouseenter", cancelSidebarClose);
    sidebarEl.addEventListener("mouseleave", function (ev) {
      var to = ev.relatedTarget;
      if (to && (sidebarEl.contains(to) || toggleBtn.contains(to))) return;
      scheduleSidebarClose();
    });
  }

  function resetSubmenus() {
    if (closeSubTimer) {
      clearTimeout(closeSubTimer);
      closeSubTimer = null;
    }
    document.querySelectorAll(".sidebar-item--expandable .sidebar-submenu.collapse").forEach(function (el) {
      if (!el.classList.contains("show")) return;
      try {
        bootstrap.Collapse.getOrCreateInstance(el, { toggle: false }).hide();
      } catch (e) {}
    });
    document.querySelectorAll(".sidebar-item--expandable .sidebar-link[aria-expanded]").forEach(function (t) {
      t.setAttribute("aria-expanded", "false");
    });
  }

  sidebarEl.addEventListener("hide.bs.offcanvas", resetSubmenus);

  var expandableItems = document.querySelectorAll(".sidebar-item--expandable");
  expandableItems.forEach(function (li) {
    var collapseEl = li.querySelector(".sidebar-submenu.collapse");
    var trigger = li.querySelector(".sidebar-link");
    if (!collapseEl || !trigger) return;

    var col = bootstrap.Collapse.getOrCreateInstance(collapseEl, { toggle: false });

    function hideOthers() {
      expandableItems.forEach(function (other) {
        if (other === li) return;
        var ce = other.querySelector(".sidebar-submenu.collapse");
        var tr = other.querySelector(".sidebar-link");
        if (ce && ce.classList.contains("show")) {
          try {
            bootstrap.Collapse.getOrCreateInstance(ce, { toggle: false }).hide();
          } catch (e) {}
        }
        if (tr) tr.setAttribute("aria-expanded", "false");
      });
    }

    function showSubmenu() {
      if (closeSubTimer) {
        clearTimeout(closeSubTimer);
        closeSubTimer = null;
      }
      hideOthers();
      col.show();
      trigger.setAttribute("aria-expanded", "true");
    }

    function scheduleHideSubmenu() {
      if (closeSubTimer) clearTimeout(closeSubTimer);
      closeSubTimer = setTimeout(function () {
        col.hide();
        trigger.setAttribute("aria-expanded", "false");
      }, hoverSubDelay);
    }

    if (prefersHover) {
      li.addEventListener("mouseenter", showSubmenu);
      li.addEventListener("mouseleave", function (ev) {
        var to = ev.relatedTarget;
        if (to && li.contains(to)) return;
        scheduleHideSubmenu();
      });
    }

    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      if (collapseEl.classList.contains("show")) {
        col.hide();
        trigger.setAttribute("aria-expanded", "false");
      } else {
        showSubmenu();
      }
    });
  });
}
