from datetime import datetime
from typing import List, Optional
from django.db.models import QuerySet
from datos.models import PickingEstadistica


class PickingQuerySetBuilder:
    """
    Builder del queryset base para cualquier analítica de picking.

    Responsabilidad ÚNICA:
    - Definir el universo de datos sobre el que se calculan KPIs, percentiles y SLAs.

    No hace:
    - Cálculos
    - Agregaciones
    - Lógica de negocio

    Este objeto es el contrato entre:
    Frontend  →  Backend  →  Analítica
    """

    def __init__(
        self,
        # -------------------
        # Filtros temporales
        # -------------------
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        anio: Optional[int] = None,
        mes: Optional[int] = None,
        dias_semana: Optional[List[int]] = None,

        # -------------------
        # Dimensiones negocio
        # -------------------
        bodegas: Optional[List[str]] = None,
        tipo_cliente: Optional[str] = None,
        ciudad_cliente: Optional[str] = None,
        estado: Optional[str] = None,
        usuario_picking: Optional[str] = None,

        # -------------------
        # Flags de control
        # -------------------
        solo_datos_completos: bool = True,
    ):
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.anio = anio
        self.mes = mes
        self.dias_semana = dias_semana

        self.bodegas = bodegas
        self.tipo_cliente = tipo_cliente
        self.ciudad_cliente = ciudad_cliente
        self.estado = estado
        self.usuario_picking = usuario_picking

        self.solo_datos_completos = solo_datos_completos
        
    def build(self) -> QuerySet:
        """
        Devuelve el queryset base filtrado.
        Este queryset es el input de cualquier servicio analítico.
        """
        qs = PickingEstadistica.objects.all()

        if self.solo_datos_completos:
            qs = qs.filter(datos_completos=True)

        qs = self._apply_date_filters(qs)
        qs = self._apply_time_dimensions(qs)
        qs = self._apply_business_dimensions(qs)

        return qs
    
    def _apply_date_filters(self, qs: QuerySet) -> QuerySet:
        """
        Filtro por rango de fechas reales (datetime).
        Útil para dashboards diarios, semanales, mensuales dinámicos.
        """
        if self.fecha_inicio and self.fecha_fin:
            return qs.filter(
                creado_mba__gte=self.fecha_inicio,
                creado_mba__lte=self.fecha_fin,
            )

        if self.fecha_inicio:
            return qs.filter(creado_mba__gte=self.fecha_inicio)

        if self.fecha_fin:
            return qs.filter(creado_mba__lte=self.fecha_fin)

        return qs
    
    def _apply_time_dimensions(self, qs: QuerySet) -> QuerySet:
        """
        Filtros por columnas temporales ya calculadas.
        Esto es MUCHO más eficiente que funciones sobre datetime.
        """
        if self.anio:
            qs = qs.filter(anio_creado=self.anio)

        if self.mes:
            qs = qs.filter(mes_creado=self.mes)

        if self.dias_semana:
            qs = qs.filter(dia_semana_creado__in=self.dias_semana)

        return qs

    def _apply_business_dimensions(self, qs: QuerySet) -> QuerySet:
        """
        Dimensiones de análisis del negocio.
        Son las que permiten comparativos y segmentación.
        """
        if self.bodegas:
            qs = qs.filter(bodega__in=self.bodegas)

        if self.tipo_cliente:
            qs = qs.filter(tipo_cliente=self.tipo_cliente)

        if self.ciudad_cliente:
            qs = qs.filter(ciudad_cliente=self.ciudad_cliente)

        if self.estado:
            qs = qs.filter(estado=self.estado)

        if self.usuario_picking:
            qs = qs.filter(usuario_picking=self.usuario_picking)

        return qs
