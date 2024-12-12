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

// Function to validate access key
function validateAccessKey(key) {
    // Define an array of valid access keys
    const validKeys = ['admin123', 'wiki2024', 'paloBlanco'];
    return validKeys.includes(key);
}

// Function to show the add entry form after validating access key
function showAddEntryFormWithValidation() {
    // Prompt for access key
    var accessKey = prompt("Por favor, ingrese la clave de acceso:");
    
    // If user cancels the prompt
    if (accessKey === null) {
        return;
    }

    // Validate the access key
    if (!validateAccessKey(accessKey)) {
        alert('Clave de acceso inválida');
        return;
    }

    // If key is valid, proceed to show the form
    // Ocultar detalles de entrada si están visibles
    var entryDetailsContainer = document.getElementById('entry-details-container');
    if (entryDetailsContainer) {
        entryDetailsContainer.classList.add('hidden');
    }

    // Ocultar lista de entradas
    var entryList = document.querySelector('.entry-list');
    if (entryList) {
        entryList.style.display = 'none';
    }

    // Mostrar formulario de agregar entrada
    var addEntryFormContainer = document.getElementById('add-entry-form-container');
    if (addEntryFormContainer) {
        addEntryFormContainer.classList.remove('hidden');
    }

    // Establecer fecha actual por defecto
    var currentDate = new Date().toISOString().split('T')[0];
    var entryDateInput = document.getElementById('entry-date');
    if (entryDateInput) {
        entryDateInput.value = currentDate;
    }
}

// Function to hide the add entry form and restore original view
function hideAddEntryForm() {
    // Ocultar formulario de agregar entrada
    var addEntryFormContainer = document.getElementById('add-entry-form-container');
    if (addEntryFormContainer) {
        addEntryFormContainer.classList.add('hidden');
    }

    // Restaurar vista de entradas
    var entryList = document.querySelector('.entry-list');
    if (entryList) {
        entryList.style.display = 'block';
    }
}

// Añadir event listener al formulario de agregar entrada
document.addEventListener('DOMContentLoaded', function() {
    var addEntryForm = document.getElementById('add-entry-form');
    if (addEntryForm) {
        addEntryForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Si la clave es válida, próximamente se implementará el guardado
            alert('Formulario válido. Próximamente se implementará el guardado.');
        });
    }
});
