import re

from rest_framework import serializers


NUMBER_REGEX = r"^[123478][0-9]{2}[0-9]{2}(2[AB]|[0-9]{2})[0-9]{3}[0-9]{3}$"


class NameSerializer(serializers.Serializer):
    accented = serializers.CharField(
        label="Variante avec caractères majuscules, minuscules et accentués",
        max_length=63,
        required=False,
    )
    filtered = serializers.CharField(
        label="Variante en majuscule sans caractères accentués",
        max_length=63,
        required=False,
    )


class FirstNamesSerializer(serializers.Serializer):
    accented = serializers.ListField(
        child=serializers.CharField(max_length=63),
        label="Variante avec caractères majuscules, minuscules et accentués",
        required=False,
    )
    filtered = serializers.ListField(
        child=serializers.CharField(max_length=63),
        label="Variante en majuscule sans caractères accentués",
        required=False,
    )


class InfosSerializer(serializers.Serializer):
    number = serializers.CharField(label="Numéro d’assuré (NIR ou NIA)", min_length=13, max_length=13)
    sex_code = serializers.IntegerField(label="Code sexe de l’assuré", min_value=1, max_value=2, required=False)
    birth_date = serializers.CharField(
        label="Date de naissance de l’assuré  (ISO 8601 avec 00 pour les parties inconnues)", required=False
    )
    birth_place = serializers.CharField(
        label="Code INSEE du lieu de naissance de l’assuré", max_length=5, required=False, read_only=True
    )
    death_date = serializers.CharField(
        label="Date de décès (ISO 8601 avec 00 pour les parties inconnues)", required=False, read_only=True
    )
    number_history = serializers.ListField(
        label="Listes des numéros d’assuré connus",
        child=serializers.CharField(min_length=13, max_length=13),
        required=False,
        read_only=True,
    )

    birth_name = NameSerializer(label="Nom de naissance de l’assuré", required=False)
    common_name = NameSerializer(label="Nom d’usage de l’assuré", required=False)
    marital_name = NameSerializer(label="Nom marital de l’assuré", required=False)
    first_names = FirstNamesSerializer(label="Prénoms de l’assuré", required=False)


class IdentitySerializer(serializers.Serializer):
    # Request fields
    request_uid = serializers.UUIDField(label="Identifiant de la requête", write_only=True, required=True)
    number = serializers.CharField(label="Numéro d’assuré (NIR ou NIA)", min_length=13, max_length=13, write_only=True)
    name = serializers.CharField(label="Nom de l’assuré", max_length=63, write_only=True, required=False)
    first_names = serializers.CharField(label="Prénoms de l’assuré", max_length=50, write_only=True, required=False)
    sex_code = serializers.IntegerField(
        label="Code sexe de l’assuré", min_value=1, max_value=2, write_only=True, required=False
    )
    birth_date = serializers.DateField(
        label="Date de naissance de l’assuré  (ISO 8601)",
        write_only=True,
        required=False,
    )

    # Response fields
    infos = InfosSerializer(label="Infos de l’assuré", required=False, read_only=True)
    result_code = serializers.IntegerField(label="Code réponse", read_only=True)
    result_label = serializers.CharField(label="Label réponse", read_only=True)

    def validate_number(self, value: str) -> str:
        if not re.match(NUMBER_REGEX, value) or value[-3:] == "000":
            raise serializers.ValidationError("Numéro invalide.")
        return value
