function exportButtons() {
  const buttons = document.querySelectorAll(".btn-export");

  buttons.forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.preventDefault();

      if (button.classList.contains("is-loading")) {
        return;
      }

      const originalText = button.textContent;
      const filename = button.download;

      button.textContent = "Wait... PDF is generated";
      button.classList.add("is-loading");

      try {
        const response = await fetch(button.href);

        if (!response.ok) {
          throw new Error(
            `PDF generation failed: ${response.status} ${response.statusText}`
          );
        }

        const blob = await response.blob();

        downloadPdf(blob, filename);
      } catch (error) {
        console.error("PDF export failed:", error);
        alert("The PDF could not be generated.");
      } finally {
        button.textContent = originalText;
        button.classList.remove("is-loading");
      }
    });
  });
}


function downloadPdf(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}


export { exportButtons };

