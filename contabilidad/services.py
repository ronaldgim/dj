from django.db.models import Sum, Count, Avg, Q, F, DecimalField
from django.db.models.functions import Coalesce
from datetime import date, timedelta
from decimal import Decimal


class CarteraKPIService:

    def __init__(self, queryset):
        self.qs  = queryset
        self.hoy = date.today()

    def base_annotations(self):
        return self.qs.annotate(
            saldo   = Coalesce('valor_total_saldo_a_cobrar', Decimal(0)),
            vencida = Q(fecha_vencimiento__lt=self.hoy)
        )

    def resumen_general(self):
        qs = self.base_annotations()

        data = qs.aggregate(
            total_cartera=Coalesce(Sum('saldo'), Decimal(0)),
            total_facturas=Count('codigo_factura'),
            ticket_promedio=Coalesce(Avg('saldo'), Decimal(0)),

            total_vencido=Coalesce(
                Sum('saldo', filter=Q(fecha_vencimiento__lt=self.hoy)),
                Decimal(0)
            ),

            total_vigente=Coalesce(
                Sum('saldo', filter=Q(fecha_vencimiento__gte=self.hoy)),
                Decimal(0)
            ),
        )

        total = data['total_cartera'] or Decimal(0)

        data['porcentaje_vencido'] = (
            round((data['total_vencido'] / total) * 100, 2)
            if total > 0 else 0
        )

        return data

    # def envejecimiento(self):
    #     qs = self.base_annotations()

    #     return qs.aggregate(
    #         mora_1_30=Coalesce(Sum(
    #             'saldo',
    #             filter= Q(fecha_vencimiento__lt=self.hoy) &
    #                     Q(fecha_vencimiento__gte=self.hoy.replace(day=1))
    #         ), Decimal(0)),

    #         mora_31_60=Coalesce(Sum(
    #             'saldo',
    #             filter=Q(fecha_vencimiento__lt=self.hoy)
    #         ), Decimal(0)),

    #         mora_61_90=Coalesce(Sum(
    #             'saldo',
    #             filter=Q(fecha_vencimiento__lt=self.hoy)
    #         ), Decimal(0)),

    #         mora_90_plus=Coalesce(Sum(
    #             'saldo',
    #             filter=Q(fecha_vencimiento__lt=self.hoy)
    #         ), Decimal(0)),
    #     )

    def riesgo(self):
        qs = self.base_annotations()

        return qs.aggregate(
            cartera_mayor_30=Coalesce(
                Sum(
                    "valor_total_saldo_a_cobrar",
                    filter=Q(fecha_vencimiento__lt=self.hoy - timedelta(days=30))
                ),
                Decimal(0)
            ),

            cartera_mayor_60=Coalesce(
                Sum(
                    "valor_total_saldo_a_cobrar",
                    filter=Q(fecha_vencimiento__lt=self.hoy - timedelta(days=60))
                ),
                Decimal(0)
            ),

            cartera_mayor_90=Coalesce(
                Sum(
                    "valor_total_saldo_a_cobrar",
                    filter=Q(fecha_vencimiento__lt=self.hoy - timedelta(days=90))
                ),
                Decimal(0)
            ),
        )

    def credito(self):
        qs = self.qs

        return qs.aggregate(
            promedio_uso_credito=Coalesce(
                Avg(
                    (F('balance') / F('limite_credito')) * 100,
                    output_field=DecimalField()
                ),
                Decimal(0)
            ),

            clientes_sobre_limite=Count(
                'codigo_cliente',
                filter=Q(balance__gt=F('limite_credito')),
                distinct=True
            )
        )

    def get_all_kpis(self):
        return {
            **self.resumen_general(),
            # **self.envejecimiento(),
            **self.riesgo(),
            **self.credito(),
        }