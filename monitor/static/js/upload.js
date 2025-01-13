const uploadInput = document.getElementById('upload-file');
const analyzeUploadBtn = document.getElementById('analyze-upload');
const uploadStatus = document.getElementById('upload-status');

// Habilitar el botón "Analizar" al seleccionar un archivo
uploadInput.addEventListener('change', () => {
    if (uploadInput.files.length === 1) {
        analyzeUploadBtn.disabled = false;
        uploadStatus.textContent = ""; // Limpiar mensajes previos
    } else if (uploadInput.files.length > 1) {
        analyzeUploadBtn.disabled = true;
        uploadStatus.textContent = "Por favor, selecciona solo un archivo.";
    } else {
        analyzeUploadBtn.disabled = true;
    }
});

// Enviar el archivo para análisis
analyzeUploadBtn.addEventListener('click', () => {
    const file = uploadInput.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('audio', file);

        // Deshabilitar botones mientras se procesa
        analyzeUploadBtn.disabled = true;
        uploadInput.disabled = true;

        // Mostrar mensaje de estado inicial
        uploadStatus.textContent = "Procesando el audio, por favor espera...";

        fetch('/analyze/', {
            method: 'POST',
            body: formData,
        })
            .then(response => {
                if (!response.ok) {
                    console.log(response);
                    throw new Error("Error en el servidor", response);
                }
                return response.json();
            })
            .then(data => {
                // Mostrar la respuesta del servidor
                if (data.clase && data.confidence !== undefined) {
                    uploadStatus.innerHTML = `
                        <strong>Resultado:</strong> ${data.clase}<br>
                        <strong>Probabilidad:</strong> ${(data.confidence * 100).toFixed(2)}%
                    `;
                } else {
                    uploadStatus.textContent = "Respuesta inesperada del servidor";
                }
            })
            .catch(error => {
                console.error("Error al analizar el audio:", error);
                uploadStatus.textContent = "Error al procesar el audio. Intenta nuevamente.";
            })
            .finally(() => {
                // Rehabilitar botones después del procesamiento
                analyzeUploadBtn.disabled = false;
                uploadInput.disabled = false;
            });
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('upload-file');
    const analyzeButton = document.getElementById('analyze-upload');
    const uploadStatus = document.getElementById('upload-status');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadStatus.textContent = `Archivo seleccionado: ${fileInput.files[0].name}`;
            analyzeButton.disabled = false;
        } else {
            uploadStatus.textContent = "No se seleccionó ningún archivo.";
            analyzeButton.disabled = true;
        }
    });
});
