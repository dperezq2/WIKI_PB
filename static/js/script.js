function toggleEntry(entryId) {
    console.log("Entrando a toggleEntry con entryId:", entryId);  // Depuración

    // Buscar la entrada con el id proporcionado
    var entry = document.getElementById(entryId);

    if (!entry) {
        console.error("Elemento con ID " + entryId + " no encontrado.");
        return;  // Si el elemento no se encuentra, no continuar
    }

    // Ocultar todos los resúmenes de entradas
    var entries = document.querySelectorAll('.entry-summary');
    entries.forEach(function(entry) {
        entry.classList.add('hidden');
    });

    // Ocultar la lista completa de entradas
    var entryList = document.querySelector('.entry-list');
    if (entryList) {
        entryList.style.display = 'none';  // Esto asegura que la lista completa se colapse
    }

    // Obtener el contenido completo de la entrada desde el atributo data-content
    var entryContent = entry.getAttribute('data-content');
    
    // Crear el contenido detallado
    var entryDetails = '';
    var titleElement = entry.querySelector('h3');
    var authorElement = entry.querySelector('small');

    if (titleElement && authorElement) {
        entryDetails = `
            <div class="modal-section">
                <h3>${titleElement.innerText}</h3>
                <p>${entryContent}</p>  <!-- Mostrar contenido completo -->
                <small>${authorElement.innerText}</small>
            </div>
        `;
    } else {
        console.error("No se encontraron los elementos 'h3' o 'small' en la entrada.");
        return; // Si no se encuentran los elementos necesarios, no continuar
    }

    // Asegurarse de que el contenedor 'entry-details-content' exista
    var entryDetailsContent = document.getElementById('entry-details-content');
    if (!entryDetailsContent) {
        console.error("No se encontró el contenedor 'entry-details-content'.");
        return;
    }

    // Insertar el contenido detallado en el contenedor
    entryDetailsContent.innerHTML = entryDetails;

    // Asegurar que el contenedor de detalles sea visible
    var entryDetailsContainer = document.getElementById('entry-details-container');
    if (entryDetailsContainer) {
        entryDetailsContainer.classList.remove('hidden');
    }
}

function goBack() {
    // Mostrar nuevamente la lista de entradas
    var entryList = document.querySelector('.entry-list');
    if (entryList) {
        entryList.style.display = 'block';  // Hacer visible la lista
    }

    // Ocultar el contenedor de detalles
    var entryDetailsContainer = document.getElementById('entry-details-container');
    if (entryDetailsContainer) {
        entryDetailsContainer.classList.add('hidden');
    }

    // Mostrar nuevamente los resúmenes de las entradas
    var entries = document.querySelectorAll('.entry-summary');
    entries.forEach(function(entry) {
        entry.classList.remove('hidden');
    });
}
