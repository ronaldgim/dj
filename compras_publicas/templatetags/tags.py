# filtro tag de horas
from django import template

register = template.Library()

@register.filter
def formato_numero_miles(numero):
    try:
        formato_miles = f'{numero:,.2f}'
        return formato_miles
    except:
        return numero
    

@register.filter
def formato_numero_precio_unitario(numero, decimales=2):
    try:
        # Convertir el número a float para formatearlo
        numero_float = float(numero)
        
        # Formatear el número con la cantidad especificada de decimales
        formato = f'{{:,.{decimales}f}}'
        numero_formateado = formato.format(numero_float)
        
        return numero_formateado
    except (ValueError, TypeError):
        return numero
    
@register.filter
def formato_numero_precio_unitario_hcam(numero, decimales=2):
    try:
        # Convertir el número a float para formatearlo
        numero_float = float(numero)
        
        # Formatear el número con la cantidad especificada de decimales
        formato = f'{{:,.{decimales}f}}'
        numero_formateado = formato.format(numero_float)
        
        # Reemplazar la coma con un punto para separar los miles y el punto con una coma para separar los decimales
        numero_formateado = numero_formateado.replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return numero_formateado
    except (ValueError, TypeError):
        return numero
    
    
@register.filter
def formato_numero_miles_cantidad(numero):
    try:
        formato_miles = f'{numero:,.0f}'
        return formato_miles
    except:
        return numero