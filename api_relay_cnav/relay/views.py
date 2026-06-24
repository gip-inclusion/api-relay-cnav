from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import fields, generics
from rest_framework.response import Response

from api_relay_cnav.relay.serializers import IdentityRequestSerializer, IdentityResponseSerializer


@extend_schema_view(
    post=extend_schema(
        operation_id="candidatures_recherche",
        parameters=[],
        request=IdentityRequestSerializer,
        responses={
            200: JobApplicationSearchResponseSerializer,
            400: inline_serializer(
                name="JobApplicationSearchRequestInvalidResponse",
                fields={
                    "nir": fields.ListField(
                        child=fields.CharField(label="Erreur individuelle"),
                        label="Erreurs liées au NIR",
                        required=False,
                    ),
                    "nom": fields.ListField(
                        child=fields.CharField(label="Erreur individuelle"),
                        label="Erreurs liées au nom",
                        required=False,
                    ),
                    "prenom": fields.ListField(
                        child=fields.CharField(label="Erreur individuelle"),
                        label="Erreurs liées au prénom",
                        required=False,
                    ),
                    "date_naissance": fields.ListField(
                        child=fields.CharField(label="Erreur individuelle"),
                        label="Erreurs liées à la date de naissance",
                        required=False,
                    ),
                },
            ),
        },
        description="API pour interroger la CNAV",
        examples=[
            schema.job_application_search_request_example,
            schema.job_application_search_response_valid_example,
            schema.job_application_search_response_valid_no_results_example,
            schema.job_application_search_response_invalid_example,
        ],
    )
)
class IdentityView(LoginNotRequiredMixin, generics.GenericAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = IdentityResponseSerializer
    throttle_classes = []

    def post(self, request, *args, **kwargs):
        self.request_serializer = IdentityRequestSerializer(data=request.data)
        self.request_serializer.is_valid(raise_exception=True)
        return Response(IdentityResponseSerializer().data)
