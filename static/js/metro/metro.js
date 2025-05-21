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
        toastContainer.style.pointerEvents = 'none'; // Evita que afecte la interacción general
        document.body.appendChild(toastContainer);
    }

    // Crear toast
    const toast = document.createElement('div');
    toast.className = `toast text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.minWidth = '250px';
    toast.style.marginBottom = '0.5rem';
    toast.style.pointerEvents = 'auto'; // Permite clicks dentro del toast

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${msg}
            </div>
            <button type="button" class="btn-close btn-close-black me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Inicializar Bootstrap Toast con JavaScript
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();

    // Eliminar del DOM cuando desaparece
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}
