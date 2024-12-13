document.addEventListener('DOMContentLoaded', function () {
    // Función para mostrar u ocultar los detalles de una entrada
    function toggleEntryDetails(entryId) {
        var entry = document.getElementById(entryId);

        if (!entry) {
            console.error("Elemento con ID " + entryId + " no encontrado.");
            return;
        }

        var entryDetails = entry.querySelector('.entry-details');
        if (!entryDetails) {
            console.error("Detalles de la entrada no encontrados.");
            return;
        }

        var entryDetailsContainer = document.getElementById('entry-details-container');
        var entryDetailsContent = document.getElementById('entry-details-content');
        
        entryDetailsContent.innerHTML = entryDetails.innerHTML;
        document.getElementById('wiki-container').style.display = 'none';
        entryDetailsContainer.classList.remove('hidden');
    }

    // Función para volver a la vista de todas las entradas
    function goBack() {
        document.getElementById('wiki-container').style.display = 'block';
        document.getElementById('entry-details-container').classList.add('hidden');
    }

    // Exponer las funciones globalmente para que estén disponibles en el HTML
    window.toggleEntryDetails = toggleEntryDetails;
    window.goBack = goBack;

    const pdfButtons = document.querySelectorAll('.view-pdf');
    
    pdfButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const pdfBase64 = button.getAttribute('data-pdf');
            
            if (pdfBase64) {
                // Convertir el base64 en un Blob y crear la URL
                const pdfBlob = new Blob([Uint8Array.from(atob(pdfBase64), c => c.charCodeAt(0))], { type: 'application/pdf' });
                const pdfUrl = URL.createObjectURL(pdfBlob);

                // Intentar abrir el PDF en una nueva ventana
                const newWindow = window.open(pdfUrl, '_blank');
                
                if (newWindow) {
                    newWindow.focus();
                } else {
                    console.log("No se pudo abrir la nueva ventana.");
                }
            } else {
                console.log("No se encontró el PDF.");
            }
        });
    });
});
