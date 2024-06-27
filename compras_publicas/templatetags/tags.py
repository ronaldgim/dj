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
def formato_numero_miles_cantidad(numero):
    try:
        formato_miles = f'{numero:,.0f}'
        return formato_miles
    except:
        return numero