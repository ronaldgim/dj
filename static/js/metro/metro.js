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
    .then(inventarioActualizado => {
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