document.addEventListener('DOMContentLoaded', function () {
    console.log("✅ Script de wiki cargado completamente");

    // Actualizar el año en el footer
    const currentYear = new Date().getFullYear();
    document.getElementById('current-year').textContent = currentYear;

    // Delegación de eventos para manejar botones dinámicos
    document.addEventListener('click', function (event) {
        // Detectar el clic en los botones PDF
        if (event.target.classList.contains('view-pdf')) {
            console.log("🖱️ Click detectado en un botón PDF.");
            const button = event.target;

            // Depurar el atributo `data-pdf`
            const pdfBase64 = button.getAttribute('data-pdf');
            if (!pdfBase64) {
                console.error("❌ No se encontró el atributo 'data-pdf' en el botón:", button);
                return;
            }

            // Validar si el contenido es Base64
            if (!/^([A-Za-z0-9+/=]+)$/.test(pdfBase64)) {
                console.error("❌ Base64 no válido detectado:", pdfBase64);
                return;
            }

            console.log("🔍 PDF Base64 detectado correctamente. Procesando...");

            try {
                // Convertir Base64 a Blob
                const pdfBlob = new Blob(
                    [Uint8Array.from(atob(pdfBase64), c => c.charCodeAt(0))],
                    { type: 'application/pdf' }
                );

                console.log("✅ PDF convertido a Blob exitosamente:", pdfBlob);

                // Generar una URL temporal para el Blob
                const pdfUrl = URL.createObjectURL(pdfBlob);
                console.log("🌐 URL del PDF generada:", pdfUrl);

                // Abrir el PDF en una nueva ventana/tab
                const newWindow = window.open(pdfUrl, '_blank');
                if (newWindow) {
                    newWindow.focus();
                    console.log("✅ PDF abierto en nueva ventana correctamente.");
                } else {
                    console.error("❌ No se pudo abrir una nueva ventana. Verifica las configuraciones del navegador.");
                }
            } catch (error) {
                console.error("❌ Error al procesar el PDF:", error.message);
            }
        }

        // Detectar el clic en el botón "Ver más"
        else if (event.target.classList.contains('view-more')) {
            const entryId = event.target.getAttribute('data-entry-id');
            console.log(`🔍 Intentando mostrar detalles para la entrada: ${entryId}`);
            toggleEntryDetails(entryId);
        }

        // Detectar el clic en una imagen para ampliarla o reducirla
        else if (event.target.tagName.toLowerCase() === 'img') {
            const image = event.target;
            // Alternar la clase 'enlarged' para ampliar o reducir la imagen
            image.classList.toggle('enlarged');
        }
    });

    // Función para mostrar detalles de una entrada
    window.toggleEntryDetails = function (entryId) {
        const entry = document.getElementById(entryId);
        const entryDetails = entry.querySelector('.entry-details');
        const entryDetailsContainer = document.getElementById('entry-details-container');
        const entryDetailsContent = document.getElementById('entry-details-content');
        
        entryDetailsContent.innerHTML = entryDetails.innerHTML;
        document.getElementById('wiki-container').style.display = 'none';
        entryDetailsContainer.classList.remove('hidden');
    };

    // Función para regresar al listado principal
    window.goBack = function () {
        document.getElementById('wiki-container').style.display = 'block';
        document.getElementById('entry-details-container').classList.add('hidden');
    };
});
