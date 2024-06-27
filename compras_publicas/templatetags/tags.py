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
def formato_numero_precio_unitario(numero):
    try:
        # Convertir el número a cadena
        numero_str = str(numero)
        
        # Dividir en parte entera y parte decimal
        if '.' in numero_str:
            parte_entera, parte_decimal = numero_str.split('.')
            formato_entero = f'{int(parte_entera):,}'
            return f'{formato_entero}.{parte_decimal}'
        else:
            # Si no tiene parte decimal
            return f'{int(numero):,}'
    except (ValueError, TypeError):
        return numero
    
    
@register.filter
def formato_numero_miles_cantidad(numero):
    try:
        formato_miles = f'{numero:,.0f}'
        return formato_miles
    except:
        return numero