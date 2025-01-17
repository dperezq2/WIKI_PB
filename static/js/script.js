document.addEventListener('DOMContentLoaded', function () {
    console.log("✅ Script de wiki cargado completamente");


    const addEntryButton = document.getElementById('add-entry-button');
const cueModal = document.getElementById('cue-modal');
const cueInput = document.getElementById('cue-input');
const submitCueButton = document.getElementById('submit-cue');
const closeModalButton = document.getElementById('close-cue-modal');
const cueError = document.getElementById('cue-error');
const addEntryFormContainer = document.getElementById('add-entry-form-container');
const wikiContainer = document.getElementById('wiki-container');
const authorInput = document.getElementById('entry-authors');  // Mantener esta referencia
const addEntryForm = document.getElementById('add-entry-form');

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
});

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

// Enviar el formulario de agregar entrada
addEntryForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Crear FormData manualmente
    const formData = new FormData();
    
    // Objeto para mapear los campos y sus IDs
    const fields = {
        'title': 'entry-title',
        'content': 'entry-content',
        'finca': 'entry-finca',
        'author': 'entry-authors',
        'creation_date': 'entry-creation_date'
    };

    // Verificar cada campo e imprimir información de debug
    for (const [fieldName, fieldId] of Object.entries(fields)) {
        const element = document.getElementById(fieldId);
        console.log(`Buscando elemento con ID: ${fieldId}`);
        if (element) {
            console.log(`Encontrado ${fieldId} con valor: ${element.value}`);
            formData.append(fieldName, element.value);
        } else {
            console.error(`No se encontró el elemento con ID: ${fieldId}`);
        }
    }

    // Manejo de archivos
    const imageInput = document.getElementById('entry-images');
    const documentInput = document.getElementById('entry-documents');

    if (imageInput) {
        const imageFiles = imageInput.files;
        for (let i = 0; i < imageFiles.length; i++) {
            formData.append('images', imageFiles[i]);
        }
    }

    if (documentInput) {
        const documentFiles = documentInput.files;
        for (let i = 0; i < documentFiles.length; i++) {
            formData.append('documents', documentFiles[i]);
        }
    }

    // Debug: mostrar todos los datos que se enviarán
    console.log('Datos a enviar:');
    for (let pair of formData.entries()) {
        console.log(pair[0] + ': ' + pair[1]);
    }

    try {
        const submitButton = document.querySelector('.submit-button');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Enviando...';
        }

        const response = await fetch('/add_entry', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log("Respuesta del servidor:", data);

        if (data.success) {
            alert('Entrada agregada exitosamente');
            addEntryFormContainer.classList.add('hidden');
            wikiContainer.style.display = 'block';
            addEntryForm.reset();
        } else {
            alert('Error al agregar la entrada: ' + data.error);
        }
    } catch (error) {
        console.error('Error al enviar la entrada:', error);
        alert('Error al enviar la entrada. Intenta de nuevo más tarde.');
    } finally {
        const submitButton = document.querySelector('.submit-button');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Enviar Entrada';
        }
    }
});

// Botón de "Cancelar" en el formulario
const cancelButton = document.querySelector('.cancel-button');

cancelButton.addEventListener('click', () => {
    // Ocultar el formulario y mostrar el wiki
    addEntryFormContainer.classList.add('hidden');
    wikiContainer.style.display = 'block';

    // Limpiar los campos del formulario
    addEntryForm.reset();

    // Si el modal está visible, también lo ocultamos
    cueModal.classList.remove('show');
    cueModal.classList.add('hidden');
});



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
