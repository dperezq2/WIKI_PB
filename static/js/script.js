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
        if (event.target.tagName.toLowerCase() === 'img' && event.target.classList.contains('img-adjunta')) {
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
        
        
        document.getElementById('wiki-container').style.display = 'none'; // Ocultar solo la lista de entradas
        /*     
        // Ocultar todos los elementos de búsqueda (inputs y selects)
        const searchOptions = document.querySelectorAll('.search-options');
        searchOptions.forEach(function(option) {
            option.style.display = 'none'; // Ocultar cada uno de los elementos de búsqueda
        });
        */   
        entryDetailsContainer.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' }); // Volver al inicio
    };

    // Función para regresar al listado principal
    window.goBack = function () {
        
        document.getElementById('wiki-container').style.display = 'block'; // Mostrar la lista
        /*
        // Mostrar todos los elementos de búsqueda nuevamente
        const searchOptions = document.querySelectorAll('.search-options');
            searchOptions.forEach(function(option) {
            option.style.display = 'flex'; // Mostrar cada uno de los elementos de búsqueda
        });
        */
        document.getElementById('entry-details-container').classList.add('hidden');
    };

    const scrollToTopButton = document.getElementById('scroll-to-top');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 200) {
            scrollToTopButton.style.display = 'flex';
        } else {
            scrollToTopButton.style.display = 'none';
        }
    });

    scrollToTopButton.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Manejar el clic en el botón "Limpiar"
    document.getElementById('clear-button').addEventListener('click', function () {
        console.log("🔄 Limpiando el formulario y los resultados.");

        // Limpiar los campos de texto y reiniciar los selectores
        document.querySelector('input[name="query1"]').value = "";
        document.querySelector('select[name="search_type1"]').value = "title";

        document.querySelector('input[name="query2"]').value = "";
        document.querySelector('select[name="search_type2"]').value = "";

        document.querySelector('input[name="query3"]').value = "";
        document.querySelector('select[name="search_type3"]').value = "";

        // Opcional: recargar la página sin parámetros para eliminar los resultados filtrados
        window.location.href = "/";
    });
});
