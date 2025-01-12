let audioContext = null;
let websocket = null;
let mediaRecorder = null;
let audioStream = null;

// Botones
const startBtn = document.getElementById('start-monitoring');
const stopBtn = document.getElementById('stop-monitoring');
const status = document.getElementById('status');

async function getLocation() {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            position => resolve({
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
            }),
            error => reject(error)
        );
    });
}

async function startMonitoring() {
    try {
        // Iniciar AudioContext
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        }

        // Obtener ubicación del usuario
        const location = await getLocation();
        console.log("Ubicación obtenida:", location);

        // Establecer conexión WebSocket
        websocket = new WebSocket("ws://127.0.0.1:8000/ws/audio/");
        websocket.onopen = () => {
            console.log("WebSocket conectado.");
            websocket.send(JSON.stringify({
                type: "metadata",
                data: {
                    location,
                    sampleRate : 16000
                }
            }));
        };
        websocket.onclose = () => console.log("WebSocket cerrado.");
        websocket.onerror = err => console.error("Error en WebSocket:", err);

        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = audioContext.createMediaStreamSource(audioStream);

        // Crear un ScriptProcessorNode para capturar PCM
        const bufferSize = 4096;
        const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (event) => {
            // Obtener los datos de audio del canal izquierdo
            const inputData = event.inputBuffer.getChannelData(0);
            // Convertir los datos a Int16
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
            let s = Math.max(-1, Math.min(1, inputData[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            // Enviar los bytes al servidor si el WebSocket está abierto
            if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(pcmData.buffer);
            }
        };
        // Iniciar grabación
        console.log("Monitoreo de audio iniciado.");

        // Actualizar UI
        startBtn.disabled = true;
        stopBtn.disabled = false;
        status.textContent = "Monitoreando audio...";
    } catch (error) {
        console.error("Error al iniciar el monitoreo:", error);
        status.textContent = "Error al iniciar el monitoreo. Revisa los permisos.";
    }
}

function stopMonitoring() {
    // Detener la grabación
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        console.log("Grabación detenida.");
    }

    // Detener el audio stream
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
    }

    // Cerrar conexión WebSocket
    if (websocket) {
        websocket.close();
        console.log("WebSocket desconectado.");
    }

    // Actualizar UI
    startBtn.disabled = false;
    stopBtn.disabled = true;
    status.textContent = "Monitoreo detenido.";
}

// Asignar eventos a los botones
startBtn.addEventListener('click', startMonitoring);
stopBtn.addEventListener('click', stopMonitoring);