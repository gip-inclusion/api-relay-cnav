from django.db import transaction
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from api_relay_cnav.api.permissions import APIAuthentication, IsAPIAnonymousUser
from api_relay_cnav.api.serializers import IdentitySerializer
from api_relay_cnav.rate_limit.throttling import BurstThrottle, LongThrottle


@extend_schema_view(
    post=extend_schema(
        operation_id="identity",
        parameters=[],
        request=IdentitySerializer,
        responses={
            200: IdentitySerializer,
        },
        description="API pour interroger la CNAV",
        examples=[],
    )
)
@method_decorator(transaction.non_atomic_requests, name="dispatch")
class IdentityView(generics.GenericAPIView):
    authentication_classes = [APIAuthentication]
    permission_classes = [IsAPIAnonymousUser]
    serializer_class = IdentitySerializer
    throttle_classes = [BurstThrottle, LongThrottle]  # TODO

    def post(self, request: Request) -> Response:
        self.request_serializer = self.get_serializer(data=request.data)
        self.request_serializer.is_valid(raise_exception=True)
        # TODO:
        # - perform SOAP call
        # - store logs of call & result summary
        # - return data
        response_data = {
            "result_code": 1000,
            "result_label": "Résultat OK",
            "infos": {
                "number": self.request_serializer.validated_data.get("number"),
                "birth_date": self.request_serializer.validated_data.get("birth_date"),
                "birth_name": {"accented": self.request_serializer.validated_data.get("name")},
                "sex_code": self.request_serializer.validated_data.get("sex_code"),
                "first_names": {
                    "accented": (self.request_serializer.validated_data.get("first_names") or "").split(" ")
                },
            },
        }
        response_serializer = self.get_serializer(response_data)
        return Response(response_serializer.data)
