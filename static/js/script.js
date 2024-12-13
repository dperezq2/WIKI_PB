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

    // Reset file and image uploads
    resetFileUploads();
}

// Function to reset file and image uploads
function resetFileUploads() {
    const imageUpload = document.getElementById('image-upload');
    const imagePreviewList = document.getElementById('image-preview-list');
    const fileUpload = document.getElementById('file-upload');
    const fileList = document.getElementById('file-list');

    if (imageUpload) imageUpload.value = '';
    if (imagePreviewList) imagePreviewList.innerHTML = '';
    if (fileUpload) fileUpload.value = '';
    if (fileList) fileList.innerHTML = '';
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

    // Reset file and image uploads
    resetFileUploads();
}

// Handling file and image uploads
document.addEventListener('DOMContentLoaded', function() {
    const imageUpload = document.getElementById('image-upload');
    const imagePreviewList = document.getElementById('image-preview-list');
    const fileUpload = document.getElementById('file-upload');
    const fileList = document.getElementById('file-list');

    // Image Upload Handling
    if (imageUpload && imagePreviewList) {
        imageUpload.addEventListener('change', function(event) {
            imagePreviewList.innerHTML = ''; // Clear previous previews
            
            Array.from(this.files).forEach(file => {
                if (file.type.match('image.*')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const previewItem = document.createElement('div');
                        previewItem.classList.add('image-preview-item');
                        
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        
                        const removeBtn = document.createElement('button');
                        removeBtn.innerHTML = '×';
                        removeBtn.classList.add('image-remove-btn');
                        removeBtn.onclick = function() {
                            previewItem.remove();
                            // Remove the corresponding file from the input
                            const dt = new DataTransfer();
                            Array.from(imageUpload.files).forEach(existingFile => {
                                if (existingFile !== file) dt.items.add(existingFile);
                            });
                            imageUpload.files = dt.files;
                        };
                        
                        previewItem.appendChild(img);
                        previewItem.appendChild(removeBtn);
                        imagePreviewList.appendChild(previewItem);
                    };
                    
                    reader.readAsDataURL(file);
                }
            });
        });
    }

    // File Upload Handling
    if (fileUpload && fileList) {
        fileUpload.addEventListener('change', function(event) {
            fileList.innerHTML = ''; // Clear previous file list
            
            Array.from(this.files).forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.classList.add('file-item');
                
                const fileName = document.createElement('span');
                fileName.classList.add('file-item-name');
                fileName.textContent = file.name;
                
                const removeBtn = document.createElement('button');
                removeBtn.innerHTML = '×';
                removeBtn.classList.add('file-remove-btn');
                removeBtn.onclick = function() {
                    fileItem.remove();
                    // Remove the corresponding file from the input
                    const dt = new DataTransfer();
                    Array.from(fileUpload.files).forEach(existingFile => {
                        if (existingFile !== file) dt.items.add(existingFile);
                    });
                    fileUpload.files = dt.files;
                };
                
                fileItem.appendChild(fileName);
                fileItem.appendChild(removeBtn);
                fileList.appendChild(fileItem);
            });
        });
    }

    // Add entry form submission
    var addEntryForm = document.getElementById('add-entry-form');
    if (addEntryForm) {
        addEntryForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Collect form data
            const formData = new FormData(this);

            // Validate required fields
            const requiredFields = ['entry-title', 'entry-date', 'entry-subject', 'entry-problem', 'entry-solution', 'entry-authors'];
            let isValid = true;

            requiredFields.forEach(fieldId => {
                const field = document.getElementById(fieldId);
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            // Check if files are within size limits
            const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB
            const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
            const MAX_TOTAL_FILES = 5;

            const imageFiles = document.getElementById('image-upload').files;
            const docFiles = document.getElementById('file-upload').files;

            // Validate image files
            for (let file of imageFiles) {
                if (file.size > MAX_IMAGE_SIZE) {
                    alert(`La imagen ${file.name} excede el tamaño máximo de 5MB.`);
                    isValid = false;
                }
            }

            // Validate document files
            for (let file of docFiles) {
                if (file.size > MAX_FILE_SIZE) {
                    alert(`El archivo ${file.name} excede el tamaño máximo de 10MB.`);
                    isValid = false;
                }
            }

            // Check total number of files
            if (imageFiles.length + docFiles.length > MAX_TOTAL_FILES) {
                alert(`No puedes subir más de ${MAX_TOTAL_FILES} archivos en total.`);
                isValid = false;
            }

            if (!isValid) {
                return;
            }

            // If validation passes, simulate form submission
            alert('Formulario válido. Los archivos serán procesados.');

            // In a real implementation, you would send this FormData to the server
            // For now, we'll just log the data
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }

            // Reset the form and hide it
            this.reset();
            resetFileUploads();
            hideAddEntryForm();
        });
    }
});