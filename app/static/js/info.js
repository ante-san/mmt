const btn_info_help = document.querySelector(".btn-info-help");
const btn_info_close = document.querySelector(".btn-info-close");
const info_window = document.querySelector(".info-window");

const window_toggle = function () {
  if (info_window.style.display != "flex") {
    info_window.style.display = "flex";
  } else {
    info_window.style.display = "none";
  }
};

btn_info_help.addEventListener("click", window_toggle);

btn_info_close.addEventListener("click", window_toggle);
