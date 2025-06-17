import requests

URL_MARA_AGUA = 'http://10.10.3.4/app/api/procesarPdf'
# URL_MARA_AGUA = 'https://www.gimpromed.com/app/api/procesarPdf'
# URL_MARA_AGUA = 'http://www.gimpromed.com/app/api/procesarPdf'


def api_marca_agua(texto, file_path, opacidad):
    try:
        
        data = {
            'texto': texto,
            'espacio': '100',
            'opacidad':opacidad
        }
        
        with open(file_path, 'rb') as pdf_file:
            files = {'pdf': pdf_file}
        
            response = requests.post(url=URL_MARA_AGUA, data=data, files=files) 
            if response.status_code == 200:
                return response
            else:
                return None
    except Exception as e:
        print(e)
        return e


# def prueba_api_marca_agua(request):
#     # Obtener el documento desde la base de datos
#     doc = DocumentoLote.objects.get(id=5304).documento.path
    
#     print(f"Documento a enviar: {doc}")
    
#     url_api = 'https://www.gimpromed.com/app/api/procesarPdf'
    
#     # Cargar el archivo y los datos que se enviarán
#     with open(doc, 'rb') as pdf_file:
#         # Definir el payload con datos adicionales
#         data = {
#             'texto': """
# GIMPROMED CIA. LTDA.
# AUTORIZA EL USO DE
# ESTE DOCUMENTO A:
# COMERCIALIZADORA Y
# CONSULTORA DE IMPLEMENTOS MAYKCARS S.A
# PARA PARTICIPAR EN EL:
# PROCESO No.
# SIE-HTMC-2023-202
# HOSPITAL DE ESPECIALIDADES
# TEODORO MALDONADO CARBO DISTRITNAL DE NUMERO 1
# USO VALIDO HASTA:
# MARZO 2024
# """,
#             'espacio': '100'
#         }
        
#         # Enviar el archivo PDF y los datos adicionales a la API externa
#         files = {
#             'pdf': pdf_file  # Aquí 'pdf' es el nombre del campo que la API espera
#         }
        
#         try:
#             r = requests.post(url_api, data=data, files=files)
            
#             # Verificar si la solicitud fue exitosa
#             if r.status_code == 200:
#                 # Imprimir la respuesta o la URL de descarga si la API lo proporciona
#                 print(f"Respuesta de la API: {r.text}")
#                 try:
#                     response_json = r.json()  # Intentar convertir la respuesta a JSON
#                     url_descarga = response_json.get('url_descarga', 'URL no disponible')
                    
#                     # Retornar un mensaje o redirigir al usuario a la URL de descarga
#                     return HttpResponse(f"El archivo fue procesado exitosamente. Descarga aquí: {url_descarga}")
#                 except ValueError:
#                     # Si la respuesta no es JSON, retornar el texto de la respuesta
#                     return HttpResponse(f"Respuesta de la API: {r.text}")
#             else:
#                 # Si hubo un error con la solicitud
#                 return HttpResponse(f"Error al procesar el archivo. Código de estado: {r.status_code}")
        
#         except requests.exceptions.RequestException as e:
#             # Manejar cualquier excepción de la solicitud
#             return HttpResponse(f"Error al conectarse a la API: {str(e)}")
