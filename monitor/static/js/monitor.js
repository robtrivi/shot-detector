let audioContext = null;
let websocket = null;
let mediaRecorder = null;
let audioStream = null;
const mapas = {};

// Botones
const startBtn = document.getElementById('start-monitoring');
const stopBtn = document.getElementById('stop-monitoring');
const status = document.getElementById('status');

function formatearFecha(fechaISO) {
    const opciones = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
    const fecha = new Date(fechaISO);
    return fecha.toLocaleString('es-ES', opciones);
}


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

        // Recibir respuesta
        websocket.onmessage = addIncident;
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

function addIncident(event){
    const data = JSON.parse(event.data);

    // Contenedor principal de incidentes
    const lista = document.getElementById("lista-incidentes");
    const nuevoItem = document.createElement("li");
    nuevoItem.id = `disparo-${data.id}`;
    console.log(data);
    // HTML para los datos del incidente
    nuevoItem.innerHTML = `
        <div class="datos">
            <h3>Posible disparo detectado el ${formatearFecha(data.fecha)}</h3>
            <p><strong>Ubicación aproximada:</strong></p>
            <div id="mapa-${data.id}" class="mapa"></div>
            <audio controls>
                <source src="/media/disparos/disparo_${data.id}.wav" type="audio/wav">
                Tu navegador no soporta la reproducción de audio.
            </audio>
            <div class="action-controls">
                <button id="aprobar-${data.id}" class="btn" onclick="aprobar(${data.id})">Marcar como confirmado</button>
                <button id="desaprobar-${data.id}" class="btn" onclick="desaprobar(${data.id})">Descartar</button>
            </div>
        </div>
    `;

    lista.insertBefore(nuevoItem, lista.firstChild);

    // Si el mapa ya existe, eliminarlo
    if (mapas[data.id]) {
        mapas[data.id].remove();
        delete mapas[data.id];
    }

    // Crear un nuevo mapa
    const mapa = L.map(`mapa-${data.id}`, {
        center: [data.latitud, data.longitud],
        zoom: 16,
        scrollWheelZoom: false
    });

    // Agregar capa base al mapa
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(mapa);

    // Agregar un círculo para marcar el incidente
    L.circle([data.latitud, data.longitud], {
        color: 'blue',
        fillColor: 'blue',
        fillOpacity: 0.2,
        radius: 100
    }).addTo(mapa);

    // Guardar el mapa en el objeto
    mapas[data.id] = mapa;

    // Asegurar que el mapa se renderice correctamente
    setTimeout(() => {
        mapa.invalidateSize();
    }, 200);
}
// Asignar eventos a los botones
startBtn.addEventListener('click', startMonitoring);
stopBtn.addEventListener('click', stopMonitoring);

function aprobar(id) {
    fetch(`/aprobar_disparo/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    }).then(response => {
        if (response.ok) {
            console.log("Disparo aprobado.");
            borrarBotones(id);
        }
    }).catch(error => console.error(error));
}

// Función para manejar el descarte de incidentes
function desaprobar(id) {
    fetch(`/desaprobar_disparo/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    }).then(response => {
        if (response.ok) {
            console.log("Disparo desaprobado.");
            borrarBotones(id);
        }
    }).catch(error => console.error(error));
}

// Eliminar botones de acciones
function borrarBotones(id) {
    const aprobarBtn = document.getElementById(`aprobar-${id}`);
    const desaprobarBtn = document.getElementById(`desaprobar-${id}`);
    if (aprobarBtn) aprobarBtn.remove();
    if (desaprobarBtn) desaprobarBtn.remove();
}

// Obtener CSRF Token para las solicitudes
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}