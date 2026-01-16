    // Ajusta iframe quando o sidebar abre ou fecha
    const sidebar = document.getElementById('sidebar');
    const iframeWrapper = document.getElementById('iframeWrapper');

    sidebar.addEventListener('show.bs.offcanvas', function () {
        // Opcional: reduzir o iframe se quiser que o offcanvas "sobreponha" ou ajuste o conteúdo
        iframeWrapper.style.marginLeft = '250px'; // largura aproximada do offcanvas
    });

    sidebar.addEventListener('hide.bs.offcanvas', function () {
        iframeWrapper.style.marginLeft = '0';
    });