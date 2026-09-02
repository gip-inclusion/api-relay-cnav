import dataclasses

import httpx
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response

from api_relay_cnav.api.permissions import APIAuthentication, IsAPIAnonymousUser
from api_relay_cnav.api.serializers import IdentitySerializer
from api_relay_cnav.audits.models import InterOpsCall
from api_relay_cnav.utils.interops import get_client, parse_response


class InterOpsCommunicationException(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "interops-communication-error"


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
    throttle_classes = []  # TODO

    def post(self, request: Request) -> Response:
        self.request_serializer = self.get_serializer(data=request.data)
        self.request_serializer.is_valid(raise_exception=True)
        request_content = self.request_serializer.validated_data
        request_uid = request_content["request_uid"]
        interops_exchange = None
        response_content = None

        client = get_client()
        # Perform InterOps call
        try:
            interops_exchange = client.identity(
                number=request_content["number"],
                name=request_content.get("name"),
                first_names=request_content.get("first_names"),
                sex_code=request_content.get("sex_code"),
                birth_date=request_content.get("birth_date"),
            )
        except httpx.HTTPError as exc:
            raise InterOpsCommunicationException(detail=f"Error contacting InterOps: {exc}") from exc
        # Only log request with a full InterOps exchange (ignore timeout & connection errors)
        try:
            interops_response = parse_response(interops_exchange.response)
            response_data = dataclasses.asdict(interops_response)
            response_serializer = self.get_serializer(response_data)
            response_content = response_serializer.data
        finally:
            InterOpsCall.objects.create(
                request_uid=request_uid,
                request_content=request_content,
                interops_request_content=interops_exchange.request,
                interops_response_content=interops_exchange.response,
                interops_response_status_code=interops_exchange.response_status_code,
                response_content=response_content,
            )
        return Response(response_content)
