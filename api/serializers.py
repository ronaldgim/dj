from rest_framework import serializers
from warehouse.models import Promocion

class PromocionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Promocion
        fields = "__all__"
