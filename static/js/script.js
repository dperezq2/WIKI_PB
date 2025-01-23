document.addEventListener('DOMContentLoaded', function () {
    console.log("✅ Script de wiki cargado completamente");


const addEntryButton = document.getElementById('add-entry-button');

/*------------LAS PARTES COMENTADAS ES PORQUE QUITÉ LO DEL FORMULARIO PROPIO EN LA PÁGINA------------------ */
/*------------AHORA SE ABRE EN UNA NUEVA PESTAÑA EL FORMULARIO DE ODK------------------ */

/*
const cueModal = document.getElementById('cue-modal');
const cueInput = document.getElementById('cue-input');
const submitCueButton = document.getElementById('submit-cue');
const closeModalButton = document.getElementById('close-cue-modal');
const cueError = document.getElementById('cue-error');
const addEntryFormContainer = document.getElementById('add-entry-form-container');
const wikiContainer = document.getElementById('wiki-container');
const authorInput = document.getElementById('entry-authors');  // Mantener esta referencia
const addEntryForm = document.getElementById('add-entry-form');
*/

/*
// Mantener formulario oculto inicialmente
addEntryFormContainer.classList.add('hidden');

// Mostrar el modal cuando se haga clic en el botón "Agregar Entrada"
addEntryButton.addEventListener('click', () => {
    cueModal.classList.remove('hidden');
    cueModal.classList.add('show');  // Asegúrate de que el modal se muestre
});

// Cerrar el modal cuando se haga clic en "Cancelar"
closeModalButton.addEventListener('click', () => {
    cueModal.classList.remove('show');
    cueModal.classList.add('hidden');
    cueInput.value = '';  // Limpiar el campo de entrada
    cueError.style.display = 'none';  // Ocultar mensaje de error
}); */


addEntryButton.addEventListener('click', async () => {
    try {
        // Hacer la solicitud al endpoint para obtener la URL
        const response = await fetch('/get_form_url');
        
        if (!response.ok) {
            throw new Error(`Error al obtener la URL: ${response.statusText}`);
        }
        
        const data = await response.json();
        const odkFormularioUrl = data.url; // Extraer la URL del JSON

        // Verificar si la URL está configurada
        if (odkFormularioUrl && odkFormularioUrl !== '#') {
            // Intentar abrir la URL en una nueva pestaña
            const odkWindow = window.open(odkFormularioUrl, '_blank');
            
            // Si window.open() devuelve null, significa que la ventana fue bloqueada
            if (!odkWindow) {
                console.error('La ventana emergente fue bloqueada. Intentando redirigir...');
                // Intentar redirigir a la misma pestaña si no se puede abrir una nueva
                window.location.href = odkFormularioUrl;
            } else {
                // Si la ventana se abrió correctamente, monitoreamos su estado
                const checkWindowInterval = setInterval(async () => {
                    if (odkWindow.closed) {
                        clearInterval(checkWindowInterval);
                        console.log('Formulario ODK enviado y ventana cerrada');
                        
                        // Realizar la solicitud al servidor para actualizar el caché
                        try {
                            await fetch('/invalidate_cache', { method: 'POST' });
                            console.log('Caché invalidado correctamente');
                            // También podrías recargar la página o actualizar la vista de las entradas si es necesario
                        } catch (error) {
                            console.error('Error al invalidar el caché', error);
                        }
                    }
                }, 1000);  // Verifica cada segundo si la ventana está cerrada
            }
        } else {
            console.error('La URL del formulario no está configurada o es inválida.');
        }
    } catch (error) {
        console.error('Error al intentar abrir el formulario:', error);
    }
});





/*
// Validar CUE y mostrar el formulario de agregar entrada
submitCueButton.addEventListener('click', async () => {
    const enteredCue = cueInput.value.trim();
    console.log("CUE ingresado:", enteredCue);

    try {
        const response = await fetch('/validate_cue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cue: enteredCue }),
        });

        const data = await response.json();
        console.log("Respuesta del servidor:", data);

        if (data.success) {
            cueModal.classList.add('hidden');
            addEntryFormContainer.classList.remove('hidden');
            wikiContainer.style.display = 'none';
            cueInput.value = '';
            cueError.style.display = 'none';

            // Establecer el nombre del usuario activo en el campo de autor
            authorInput.value = data.nombre;
        } else {
            cueError.style.display = 'block';
            cueError.textContent = data.error || 'CUE inválido o usuario inactivo. Inténtalo de nuevo.';
        }
    } catch (error) {
        console.error('Error al validar el CUE:', error);
        cueError.style.display = 'block';
        cueError.textContent = 'Error en el servidor. Intenta de nuevo más tarde.';
    }
});

// Variables para almacenar los archivos seleccionados
let accumulatedImages = [];
let accumulatedDocuments = [];

// Función para manejar vista previa y acumulación de archivos
function handleFilePreview(inputElement, previewContainer, fileList, acceptedFileTypes) {
    const newFiles = Array.from(inputElement.files);

    // Filtrar los archivos aceptados y evitar duplicados
    newFiles.forEach((file) => {
        if (
            (!acceptedFileTypes || acceptedFileTypes.includes(file.type)) &&
            !fileList.some((existingFile) => existingFile.name === file.name && existingFile.size === file.size)
        ) {
            fileList.push(file);
        }
    });

    // Limpiar el input para permitir volver a adjuntar el mismo archivo si se elimina
    inputElement.value = '';

    // Actualizar la vista previa
    updateFilePreview(previewContainer, fileList, (indexToRemove) => {
        fileList.splice(indexToRemove, 1); // Eliminar archivo de la lista
        handleFilePreview(inputElement, previewContainer, fileList, acceptedFileTypes); // Actualizar vista previa
    });
}

// Función para actualizar la vista previa
function updateFilePreview(previewContainer, fileList, onRemove) {
    previewContainer.innerHTML = ''; // Limpiar vista previa

    fileList.forEach((file, index) => {
        const filePreview = document.createElement('div');
        filePreview.classList.add('preview-item');

        // Vista previa de imágenes
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.classList.add('preview-image');
            filePreview.appendChild(img);
        }

        // Nombre del archivo
        const fileName = document.createElement('span');
        fileName.textContent = file.name;
        filePreview.appendChild(fileName);

        // Botón para eliminar
        const removeButton = document.createElement('span');
        removeButton.textContent = 'Eliminar';
        removeButton.classList.add('remove-file');
        removeButton.addEventListener('click', () => onRemove(index));
        filePreview.appendChild(removeButton);

        previewContainer.appendChild(filePreview);
    });
}

// Configuración de eventos para acumulación de imágenes
const imageInput = document.getElementById('entry-images');
const imagePreviewContainer = document.getElementById('image-preview-container');
imageInput.addEventListener('change', () => {
    handleFilePreview(imageInput, imagePreviewContainer, accumulatedImages, ['image/jpeg', 'image/png', 'image/gif']);
});

// Configuración de eventos para acumulación de documentos
const documentInput = document.getElementById('entry-documents');
const documentPreviewContainer = document.getElementById('document-preview-container');
documentInput.addEventListener('change', () => {
    handleFilePreview(documentInput, documentPreviewContainer, accumulatedDocuments, ['application/pdf']);
});

// Modificar el envío del formulario para incluir todos los archivos acumulados
addEntryForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData();

    // Añadir otros campos del formulario
    const fields = {
        'title': 'entry-title',
        'content': 'entry-content',
        'finca': 'entry-finca',
        'author': 'entry-authors',
        'creation_date': 'entry-creation_date'
    };

    for (const [fieldName, fieldId] of Object.entries(fields)) {
        const element = document.getElementById(fieldId);
        if (element) {
            formData.append(fieldName, element.value);
        }
    }

    // Añadir archivos acumulados
    accumulatedImages.forEach((file) => formData.append('images', file));
    accumulatedDocuments.forEach((file) => formData.append('documents', file));

    try {
        // Desactivar el botón para evitar múltiples envíos
        const submitButton = document.querySelector('.submit-button');
        submitButton.disabled = true;
        submitButton.textContent = 'Enviando...';

        // Enviar los datos al servidor
        const response = await fetch('/add_entry', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Mostrar mensaje de éxito
            alert('Entrada agregada exitosamente');

            // Ocultar el formulario de entrada y mostrar el wiki
            addEntryFormContainer.classList.add('hidden');
            wikiContainer.style.display = 'block';

            // Limpiar acumuladores y vistas previas
            accumulatedImages = [];
            accumulatedDocuments = [];
            imagePreviewContainer.innerHTML = '';
            documentPreviewContainer.innerHTML = '';

            // Limpiar el formulario de entrada
            addEntryForm.reset();

            // **Importante: No mostrar el modal después del envío exitoso**
            cueModal.classList.remove('show');
            cueModal.classList.add('hidden');
            cueInput.value = '';
            cueError.style.display = 'none';  // Ocultar mensaje de error

            // Desactivar el formulario de agregar entrada para evitar más envíos.
            addEntryForm.classList.add('submitted'); // Marcar el formulario como enviado
        } else {
            alert('Error al agregar la entrada: ' + data.error);
        }
    } catch (error) {
        console.error('Error al enviar la entrada:', error);
        alert('Error al enviar la entrada. Intenta de nuevo más tarde.');
    } finally {
        // Habilitar el botón de envío de nuevo
        const submitButton = document.querySelector('.submit-button');
        submitButton.disabled = false;
        submitButton.textContent = 'Enviar Entrada';
    }
});

const cancelButton = document.querySelector('.cancel-button');


// Modificar el comportamiento de "Cancelar"
cancelButton.addEventListener('click', () => {
    // Si el formulario ya fue enviado, no mostrar el modal ni hacer nada
    if (addEntryForm.classList.contains('submitted')) {
        return; // No hacer nada si ya se envió el formulario
    }

    // Ocultar el formulario de entrada y mostrar el wiki
    addEntryFormContainer.classList.add('hidden');
    wikiContainer.style.display = 'block';

    // Limpiar los campos del formulario
    addEntryForm.reset();

    // Asegurarse de que el modal del CUE esté oculto
    cueModal.classList.remove('show');
    cueModal.classList.add('hidden');
    cueInput.value = '';
    cueError.style.display = 'none';  // Ocultar mensaje de error
});
*/

    // Actualizar el año en el footer
    const currentYear = new Date().getFullYear();
    document.getElementById('current-year').textContent = currentYear;

    // Delegación de eventos para manejar botones dinámicos
    document.addEventListener('click', function (event) {
        // Detectar el clic en los botones PDF
        if (event.target.classList.contains('view-pdf')) {
            console.log("🖱️ Click detectado en un botón PDF.");
            const button = event.target;
    
            // Verificar si el atributo 'data-pdf' está presente
            const pdfUrl = button.getAttribute('data-pdf');
            console.log("Atributo 'data-pdf' del botón:", pdfUrl);
    
            if (!pdfUrl) {
                console.error("❌ No se encontró el atributo 'data-pdf' en el botón:", button);
                return;
            }
    
            console.log("🔍 PDF URL detectado correctamente:", pdfUrl);
    
            try {
                // Abrir el PDF en una nueva ventana/tab
                const newWindow = window.open(pdfUrl, '_blank');
                if (newWindow) {
                    newWindow.focus();
                    console.log("✅ PDF abierto en nueva ventana correctamente.");
                } else {
                    console.error("❌ No se pudo abrir una nueva ventana. Verifica las configuraciones del navegador.");
                }
            } catch (error) {
                console.error("❌ Error al abrir el PDF:", error.message);
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
        entryDetailsContainer.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' }); // Volver al inicio
    };

    // Función para regresar al listado principal
    window.goBack = function () {
        
        document.getElementById('wiki-container').style.display = 'block'; // Mostrar la lista
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

