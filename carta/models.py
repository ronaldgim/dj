# Models
from django.db import models

# Datos Models
from datos.models import Marca, Product 
from users.models import UserPerfil

# Datetiem
from datetime import date

# Slugify
from django.template.defaultfilters import slugify

# Uuid
import uuid

# QR
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO
from django.core.files import File

# Create your models here.

MONTH_CHOICE = [
    ('Enero',       'Enero'),
    ('Febrero',     'Febrero'),
    ('Marzo',       'Marzo'),
    ('Abril',       'Abril'),
    ('Mayo',        'Mayo'),
    ('Junio',       'Junio'),
    ('Julio',       'Julio'),
    ('Agosto',      'Agosto'),
    ('Septiembre',  'Septiembre'),
    ('Octubre',     'Octubre'),
    ('Noviembre',   'Noviembre'),
    ('Diciembre',   'Diciembre'),
]

YEAR_CHOICE = [
    ('2022',  '2022'),
    ('2023',  '2023'),
    ('2024',  '2024'),
    # ('2025',  '2025'),
    # ('2026',  '2026'),
    # ('2027',  '2027'),
    # ('2028',  '2028'),
    # ('2029',  '2029'),
    # ('2030',  '2030'),
]


class CartaGeneral(models.Model):
    
    n_ofocio            = models.IntegerField(verbose_name='N° Oficio', null=True)
    oficio              = models.CharField(verbose_name='Oficio', max_length=30)
    ruc                 = models.CharField(verbose_name='Ruc', max_length=13)
    cliente             = models.CharField(verbose_name='Cliente', max_length=250)
    valido_hasta_mes    = models.CharField(verbose_name='Valido hasta mes', max_length=20, choices=MONTH_CHOICE)
    valido_hasta_anio   = models.CharField(verbose_name='Valido hasta anio', max_length=20, choices=YEAR_CHOICE)
    fecha_emision       = models.DateField(verbose_name='Fecha', auto_now_add=True)
    slug                = models.SlugField(unique=True)
    qr_code             = models.ImageField(verbose_name='QR', upload_to='qr_carta_general', blank=True)
    
    usuario             = models.ForeignKey(UserPerfil, verbose_name='Usuario', blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.oficio} - {self.cliente}'
        
        
    def save(self, *args, **kwargs):
        
        self.slug = slugify(
            uuid.uuid4()
        )
        
        f = date.today()
        y = str(f.year)
        
        if not CartaGeneral.objects.filter(fecha_emision__year=y).exists():
            n_of_f = '0001'
        else:
            n_of = CartaGeneral.objects.filter(fecha_emision__year=y).count() #.latest('id').pk
            n_of += 1
            #n_of += 286
            if n_of < 10:
                n_of_f = '000{n_oficio_final}'.format(n_oficio_final = str(n_of))
            elif n_of < 100:
                n_of_f = '00{n_oficio_final}'.format(n_oficio_final = str(n_of))
            elif n_of < 1000:
                n_of_f = '0{n_oficio_final}'.format(n_oficio_final = str(n_of))
            else:
                n_of_f = str(n_of)
        
        self.n_ofocio = n_of_f
        
        self.oficio = f'GIM-GF-CD-CG-{y}-{n_of_f}'
        
        qr_text = '{oficio}{cliente}{ruc}{f_em}{v_h_m} {v_h_a}\n{slug}'.format(
            oficio  =   self.oficio,
            cliente =   self.cliente, 
            ruc     =   self.ruc,
            f_em    =   f, 
            v_h_m   =   self.valido_hasta_mes,
            v_h_a   =   self.valido_hasta_anio,
            slug    =   self.slug
        )
        
        qrcode_img=qrcode.make(qr_text)
        canvas=Image.new('RGB', (650,650), 'white') #, 'green'
        draw=ImageDraw.Draw(canvas)
        canvas.paste(qrcode_img)
        buffer=BytesIO()
        canvas.save(buffer,"PNG")
        self.qr_code.save(f'{self.slug}' + '.png', File(buffer), save=False)
        canvas.close()
        
        return super().save(*args, **kwargs)
    

class CartaProcesos(models.Model):
    
    n_ofocio            = models.IntegerField(verbose_name='N° Oficio', null=True)
    oficio              = models.CharField(verbose_name='Oficio', max_length=50)
    ruc                 = models.CharField(verbose_name='Ruc', max_length=15)
    cliente             = models.CharField(verbose_name='Cliente', max_length=150)
    marcas              = models.ManyToManyField(Marca, verbose_name='Marca')
    hospital            = models.CharField(verbose_name='Hospital', max_length=100)
    proceso             = models.CharField(verbose_name='N° Proceso', max_length=50)
    fecha_emision       = models.DateField(verbose_name='Fecha', auto_now_add=True)
    slug                = models.SlugField(unique=True)
    qr_code             = models.ImageField(verbose_name='QR', upload_to='qr_carta_procesos', blank=True)

    usuario             = models.ForeignKey(UserPerfil, verbose_name='Usuario', blank=True, null=True, on_delete=models.PROTECT)

    autorizacion        = models.CharField(verbose_name='Autorización', max_length=450, blank=True)
    
    def __str__(self):
        return f'{self.oficio} - {self.cliente}'
    
    
    def save(self, *args, **kwargs):
        
        self.slug = slugify(
            uuid.uuid4()
        )
        
        f = date.today()
        y = str(f.year)
        
        if not CartaProcesos.objects.filter(fecha_emision__year=y).exists():
            n_of_f = '0001'
        else:
            # n_of = CartaProcesos.objects.latest('id').pk
            n_of = CartaProcesos.objects.filter(fecha_emision__year=y).count()
            n_of += 1
            # n_of += 285
            if n_of < 10:
                n_of_f = '000{n_oficio_final}'.format(n_oficio_final = str(n_of))
            elif n_of < 100:
                n_of_f = '00{n_oficio_final}'.format(n_oficio_final = str(n_of))
            elif n_of < 1000:
                n_of_f = '0{n_oficio_final}'.format(n_oficio_final = str(n_of))
            else:
                n_of_f = str(n_of)
        
        self.n_ofocio = n_of_f
        
        self.oficio = f'GIM-GF-CD-CP-{y}-{n_of_f}'
        
        # qr_text = '{oficio}{cliente}{ruc}{f_em}{hosp}{proc}\n{slug}'.format(
        #     oficio  =   self.oficio,
        #     cliente =   self.cliente, 
        #     ruc     =   self.ruc,
        #     f_em    =   f, 
        #     hosp    =   self.hospital,
        #     proc    =   self.proceso,
        #     slug    =   self.slug
        # )
        
        qr_text = f"{self.oficio}{self.cliente}{self.ruc}{self.hospital}{self.proceso}\n{self.slug}"
        
        # qrcode_img=qrcode.make(qr_text)
        # canvas=Image.new('RGB', (650,650), 'white') #, 'green white'
        # draw=ImageDraw.Draw(canvas)
        # canvas.paste(qrcode_img)
        # buffer=BytesIO()
        # canvas.save(buffer,"PNG")
        # self.qr_code.save(f'{self.slug}' + '.png', File(buffer), save=False)
        # canvas.close()
        
        # return super().save(*args, **kwargs)
        qr = qrcode.QRCode(
            version=1,  # Controla el tamaño del QR (1 es el más pequeño)
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta corrección de errores
            box_size=10,  # Tamaño de cada cuadro en el código QR
            border=4,  # Bordes del QR
        )
        qr.add_data(qr_text)
        qr.make(fit=True)

        # Crear la imagen QR
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Crear un canvas en blanco y pegar la imagen QR
        canvas = Image.new('RGB', (650, 650), 'white')
        qr_width, qr_height = qr_img.size
        offset = ((canvas.size[0] - qr_width) // 2, (canvas.size[1] - qr_height) // 2)
        canvas.paste(qr_img, offset)

        # Guardar la imagen en un buffer de memoria
        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)  # Reiniciar el puntero del buffer

        # Guardar la imagen en el campo `qr_code` del modelo
        filename = f"{self.slug}.png"  # Nombre del archivo basado en `slug`
        self.qr_code.save(filename, File(buffer), save=False)

        # Limpiar recursos
        buffer.close()
        canvas.close()

        # Llamar al método `save` del modelo base
        return super().save(*args, **kwargs)


class CartaItem(models.Model):
    n_ofocio            = models.IntegerField(verbose_name='N° Oficio', null=True)
    oficio              = models.CharField(verbose_name='Oficio', max_length=30)
    ruc                 = models.CharField(verbose_name='Ruc', max_length=13)
    cliente             = models.CharField(verbose_name='Cliente', max_length=150)
    items               = models.ManyToManyField(Product, verbose_name='Productos')
    hospital            = models.CharField(verbose_name='Hospital', max_length=100)
    proceso             = models.CharField(verbose_name='N° Proceso', max_length=50)
    fecha_emision       = models.DateField(verbose_name='Fecha', auto_now_add=True)
    slug                = models.SlugField(unique=True)
    qr_code             = models.ImageField(verbose_name='QR', upload_to='qr_carta_procesos', blank=True)

    usuario             = models.ForeignKey(UserPerfil, verbose_name='Usuario', blank=True, null=True ,on_delete=models.PROTECT)
    
    autorizacion        = models.CharField(verbose_name='Autorización', max_length=450, blank=True)
    
    def __str__(self):
        return f'{self.oficio} - {self.cliente}'
    
    
    def save(self, *args, **kwargs):
        
        self.slug = slugify(
            uuid.uuid4()
        )
        
        f = date.today()
        y = str(f.year)
        
        if not CartaItem.objects.filter(fecha_emision__year=y).exists():
            n_of_f = '0001'
        else:
            n_of = CartaItem.objects.filter(fecha_emision__year=y).count() #latest('id').pk
            n_of += 1
            if n_of < 10:
                n_of_f = '000{n_oficio_final}'.format(n_oficio_final = str(n_of))
            elif n_of < 100:
                n_of_f = '00{n_oficio_final}'.format(n_oficio_final = str(n_of))
            elif n_of < 1000:
                n_of_f = '0{n_oficio_final}'.format(n_oficio_final = str(n_of))
            else:
                n_of_f = str(n_of)
        
        self.n_ofocio = n_of_f
        
        self.oficio = f'GIM-GF-CD-CI-{y}-{n_of_f}'
        
        qr_text = '{oficio}{cliente}{ruc}{f_em}{hosp}{proc}\n{slug}'.format(
            oficio  =   self.oficio,
            cliente =   self.cliente, 
            ruc     =   self.ruc,
            f_em    =   f, 
            hosp    =   self.hospital,
            proc    =   self.proceso,
            slug    =   self.slug
        )
        
        qrcode_img=qrcode.make(qr_text)
        canvas=Image.new('RGB', (650,650), 'white') #, 'green white'
        draw=ImageDraw.Draw(canvas)
        canvas.paste(qrcode_img)
        buffer=BytesIO()
        canvas.save(buffer,"PNG")
        self.qr_code.save(f'{self.slug}' + '.png', File(buffer), save=False)
        canvas.close()
        
        return super().save(*args, **kwargs)
    

class AnularCartaGeneral(models.Model):
    
    cartageneral = models.OneToOneField(CartaGeneral, verbose_name='Carta General', on_delete=models.CASCADE)
    comentario   = models.TextField(verbose_name='Comentario', max_length=300)
    fecha        = models.DateTimeField(verbose_name='Fecha de anulación', auto_now_add=True)
    slug         = models.SlugField(unique=True)

    usuario             = models.ForeignKey(UserPerfil, verbose_name='Usuario', blank=True, null=True, on_delete=models.PROTECT)
    
    def __str__(self):
        return str(self.cartageneral)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)
    

class AnularCartaProcesos(models.Model):
    
    cartaprocesos = models.OneToOneField(CartaProcesos, verbose_name='Carta Procesos', on_delete=models.CASCADE)
    comentario    = models.TextField(verbose_name='Comentario', max_length=300)
    fecha         = models.DateTimeField(verbose_name='Fecha de anulación', auto_now_add=True)
    slug          = models.SlugField(unique=True)

    usuario             = models.ForeignKey(UserPerfil, verbose_name='Usuario', blank=True, null=True ,on_delete=models.PROTECT)
    
    def __str__(self):
        return str(self.cartaprocesos)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)


class AnularCartaItem(models.Model):
    
    cartaitem     = models.OneToOneField(CartaItem, verbose_name='Carta Procesos', on_delete=models.CASCADE)
    comentario    = models.TextField(verbose_name='Comentario', max_length=300)
    fecha         = models.DateTimeField(verbose_name='Fecha de anulación', auto_now_add=True)
    slug          = models.SlugField(unique=True)

    usuario       = models.ForeignKey(UserPerfil, verbose_name='Usuario', blank=True, null=True, on_delete=models.PROTECT)
    
    def __str__(self):
        return str(self.cartaitem)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)