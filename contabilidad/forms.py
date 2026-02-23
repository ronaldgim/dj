from django.core.exceptions import ValidationError

# Forms
from django import forms

# Models
from contabilidad.models import NotificacionCartera

# Forms
class NotificacionCarteraForm(forms.ModelForm):

    class Meta:
        model = NotificacionCartera
        fields = ['codigo_cliente', 'correos']

    def clean_correos(self):
        correos = self.cleaned_data.get('correos', '')
        lista_correos = [c.strip() for c in correos.split(',')]

        email_validator = forms.EmailField()

        errores = []
        validos = []

        for correo in lista_correos:
            try:
                email_validator.clean(correo)
                validos.append(correo)
            except ValidationError:
                errores.append(correo)

        if errores:
            raise ValidationError(f"Correos inválidos: {', '.join(errores)}")

        # opcional: guardar limpio
        return ",".join(validos)