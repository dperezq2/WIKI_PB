// Lista de textos a mostrar
const texts = [
    "Bienvenido a la Wiki de Palo Blanco - Explora, aprende y contribuye: el conocimiento está en tus manos.",
    "Transformando datos en conocimiento al alcance de todos.",
    "Descubre y comparte el saber de Palo Blanco, tu puerta al conocimiento colectivo."
];

// Índice para rastrear el texto actual
let currentIndex = 0;

// Referencia al elemento del banner
const banner = document.getElementById("rotating-text");

// Función para actualizar el texto
function updateText() {
    // Actualiza el texto actual
    banner.textContent = texts[currentIndex];
    // Reinicia la animación
    banner.style.animation = "none"; // Pausa animación para reiniciarla
    setTimeout(() => {
        banner.style.animation = ""; // Reactiva la animación
    }, 50);

    // Cambia al siguiente texto después de un retraso
    currentIndex = (currentIndex + 1) % texts.length; // Cambia al siguiente texto

    // Llama a la función nuevamente después de 5s (duración animación) + 2s de pausa
    setTimeout(updateText, 10000);
}

// Inicializa el primer texto al cargar
window.onload = () => {
    updateText();
};
