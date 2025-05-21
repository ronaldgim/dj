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
        toastContainer.style.zIndex = '1060'; // Sobre modals
        document.body.appendChild(toastContainer);
    }

    // Crear toast
    const toastId = `toast-${Date.now()}`;
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0 show`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.id = toastId;
    toast.style.minWidth = '250px';
    toast.style.marginBottom = '0.5rem';

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${msg}
            </div>
            <button type="button" class="btn-close btn-close-black me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Eliminar después de 5s automáticamente
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    }, 5000);
}