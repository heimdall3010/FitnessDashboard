function hamburger() {


  const hamburger = document.querySelector("#hamburger");

  if (hamburger) {
    const navContainer = document.querySelector("#nav-component");
    const backdrop = document.querySelector('.backdrop');

    function openNav() {
      hamburger.classList.add("is-active");
      navContainer.classList.add("nav-component-active");
      backdrop.classList.add("backdrop-active");
    }

    function closeNav() {
      hamburger.classList.remove("is-active");
      navContainer.classList.remove("nav-component-active");
      backdrop.classList.remove("backdrop-active");
    }


    hamburger.addEventListener("click", () => {

      if (hamburger.classList.contains("is-active")) {
        closeNav();
      }
      else {
        openNav();
      }
    });

    backdrop.addEventListener("click", () => {

      if (backdrop.classList.contains("backdrop-active")) {
        closeNav();
      }
    });

  }
}


export { hamburger }
