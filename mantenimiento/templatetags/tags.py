# filtro tag de horas
from django import template

register = template.Library()

@register.filter(name='hms')
def hms(value):
    s = value.total_seconds() 
    s = int(s)

    h = int(s / 3600) # horas
    m = int((s % 3600)/60) # minutos
    
    if m < 10:
        min = '0'+str(m)
    else:
        min = m

    return f'{h}:{min}:00'


@register.filter(name='hms2')
def hms2(value):

    s = value
    h = s // 3600000
    m = (s/3600000) - h 
    m = (m * 3600) / 60
    m = round(m)
    
    if m < 10:
        min = '0'+str(m)
    else:
        min = m

    return f'{h}:{min}:00'