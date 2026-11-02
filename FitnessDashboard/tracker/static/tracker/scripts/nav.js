function nav() {
  const currentUrl = window.location.pathname;
  const navbarItems = document.querySelectorAll("#nav-navbar .nav-navbar-item");
  const navbarStart = document.querySelector("#nav-navbar .nav-navbar-item");

  let matchFound = false;

  navbarItems.forEach((item) => {
    item.classList.remove("nav-navbar-item-active");

    const itemId = item.id;

    if (itemId && currentUrl.includes(itemId)) {
      item.classList.add("nav-navbar-item-active");
      matchFound = true;
    }
  });

  if (!matchFound && navbarStart) {
    navbarStart.classList.add("nav-navbar-item-active");
  }
}

export { nav };
