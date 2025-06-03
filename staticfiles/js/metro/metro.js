// Función auxiliar para obtener el token CSRF de las cookies
function obtenerCSRFToken() {
    const name = 'csrftoken';
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith(name))
        ?.split('=')[1];
    
    return cookieValue;
}

// Función para patch inventario
function metro_patch_inventario(id, datosParciales) {
    // Obtener el token CSRF
    const csrfToken = obtenerCSRFToken();
    
    // URL del endpoint
    const url = `/metro/inventario-edit-patch/${id}`;
    
    // Realizar la petición PATCH
    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(datosParciales)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Aquí puedes actualizar la UI con los datos actualizados
        // actualizarInterfaz(inventarioActualizado);
        // console.log(inventarioActualizado);
        location.reload();
    })
    .catch(error => {
        console.error('Error al actualizar producto:', error);
        // mostrarError('No se pudo actualizar el producto');
    });
}

function msg_alert(type, msg) {
    // Crear contenedor si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '1rem';
        toastContainer.style.right = '1rem';
        toastContainer.style.zIndex = '1060';
        toastContainer.style.pointerEvents = 'none'; 
        document.body.appendChild(toastContainer);
    }

    // Crear elemento toast
    const toastWrapper = document.createElement('div');
    toastWrapper.className = 'toast align-items-center text-bg-' + type;
    toastWrapper.setAttribute('role', 'alert');
    toastWrapper.setAttribute('aria-live', 'assertive');
    toastWrapper.setAttribute('aria-atomic', 'true');
    toastWrapper.setAttribute('tabindex', '-1');
    toastWrapper.style.minWidth = '250px';
    toastWrapper.style.marginBottom = '0.5rem';
    toastWrapper.style.pointerEvents = 'auto'; // Botón cerrable

    toastWrapper.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${msg}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    // Agregar al contenedor sin causar scroll
    toastContainer.appendChild(toastWrapper);

    // Inicializar correctamente con Bootstrap Toast API
    const bsToast = new bootstrap.Toast(toastWrapper, {
        animation: true,
        autohide: true,
        delay: 5000
    });

    bsToast.show();
}
