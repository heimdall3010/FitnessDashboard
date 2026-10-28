let accordionArray = [];

function setAccordionId() {
  let i = 0;
  const accordions = document.querySelectorAll(".accordion-component");
  if (accordions) {

    accordions.forEach((accordion) => {
      accordion.setAttribute("id", "accordion-component-" + i);
      accordionArray.push("accordion-component-" + i);
      i++;
    });
  }
}

function accordionToggler(item) {
  const accordionHeadlines = item.querySelectorAll(".accordion-headline");

  accordionHeadlines.forEach((accordionHeadline) => {
    accordionHeadline.addEventListener("click", function () {

      const isActive = accordionHeadline.classList.contains("accordion-active");

      accordionHeadlines.forEach((accordionHeadline) => {
        accordionHeadline.classList.remove("accordion-active");
        const accordionContent = accordionHeadline.nextElementSibling;
        accordionContent.classList.remove("accordion-active");
      });

      accordionHeadline.classList.toggle("accordion-active", !isActive);
      const accordionContent = accordionHeadline.nextElementSibling;
      accordionContent.classList.toggle("accordion-active", !isActive);

    });
  });

}


function accordion() {
  setAccordionId();

  if (accordionArray.length) {
    accordionArray.forEach((item) => {
      let currentItem = document.querySelector("#" + item);
      accordionToggler(currentItem);
    });
  }
}

export { accordion }
