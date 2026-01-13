window.addEventListener("load", function () {
  setTimeout(function () {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) {
      overlay.style.display = "none";
    }
  }, 1000); // 1 segundo
});
