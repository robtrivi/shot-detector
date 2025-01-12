console.log("Cargando resultados.js");

// Formatear fecha para mostrarla en un formato amigable
function formatearFecha(fechaISO) {
    const opciones = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
    const fecha = new Date(fechaISO);
    return fecha.toLocaleString('es-ES', opciones);
}

// WebSocket para recibir los incidentes
const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(ws_scheme + '://' + window.location.host + '/ws/incidentes/');

// Objeto para almacenar instancias de mapas
const mapas = {};

// Al abrir el WebSocket
socket.onopen = function() {
    console.log("Conexión WebSocket establecida.");
};

// Al cerrar el WebSocket
socket.onclose = function() {
    console.log("Conexión WebSocket cerrada.");
};

// Al recibir datos del WebSocket
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Contenedor principal de incidentes
    const lista = document.getElementById("lista-incidentes");
    const nuevoItem = document.createElement("li");
    nuevoItem.id = `disparo-${data.id}`;

    // HTML para los datos del incidente
    nuevoItem.innerHTML = `
        <div class="datos">
            <h3>Posible disparo detectado el ${formatearFecha(data.fecha)}</h3>
            <p><strong>Probabilidad de disparo:</strong> ${data.probabilidad}%</p>
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
};

// Función para manejar la aprobación de incidentes
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
