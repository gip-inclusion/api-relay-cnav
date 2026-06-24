from rest_framework import serializers


class IdentityRequestSerializer(serializers.Serializer):
    numero = serializers.CharField(write_only=True, label="Numéro d’assuré (NIR ou NIA)", max_length=13)
    nom = serializers.CharField(write_only=True, label="Nom de l’assuré", max_length=63)
    prenoms = serializers.CharField(write_only=True, label="Prénoms de l’assuré", max_length=50)
    code_sexe = serializers.IntegerField(write_only=True, label="Code sexe de l’assuré", min_value=1, max_value=2)
    date_naissance = serializers.DateField(write_only=True, label="Date de naissance de l’assuré (ISO 8601)")


class IdentityResponseSerializer(serializers.Serializer):
    pass
