import xml.etree.ElementTree as ET
from pprint import pformat

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from api_relay_cnav.audits import models
from api_relay_cnav.utils.interops import prettify_xml_string


@admin.register(models.InterOpsCall)
class InterOpsCallAdmin(admin.ModelAdmin):
    list_display = (
        "request_uid",
        "timestamp",
    )
    fields = (
        "timestamp",
        "request_uid",
        "pretty_request_content",
        "pretty_interops_request_content",
        "interops_response_status_code",
        "pretty_interops_response_content",
        "pretty_response_content",
    )
    search_fields = ("=request_uid",)
    ordering = ("-timestamp",)

    @admin.display(description="Données envoyées par le client")
    def pretty_request_content(self, obj: models.InterOpsCall) -> str:
        if obj.request_content:
            return format_html("<pre><code>{}</code></pre>", pformat(obj.request_content, width=200))

        return self.get_empty_value_display()

    @admin.display(description="Données transmises à InterOps")
    def pretty_interops_request_content(self, obj: models.InterOpsCall) -> str:
        if obj.interops_request_content:
            try:
                return format_html("<pre><code>{}</code></pre>", prettify_xml_string(obj.interops_request_content))
            except ET.ParseError:
                return obj.interops_request_content

        return self.get_empty_value_display()

    @admin.display(description="Données renvoyées par InterOps")
    def pretty_interops_response_content(self, obj: models.InterOpsCall) -> str:
        if obj.interops_response_content:
            try:
                return format_html("<pre><code>{}</code></pre>", prettify_xml_string(obj.interops_response_content))
            except ET.ParseError:
                return obj.interops_response_content

        return self.get_empty_value_display()

    @admin.display(description="Données renvoyées au client")
    def pretty_response_content(self, obj: models.InterOpsCall) -> str:
        if obj.response_content:
            return format_html("<pre><code>{}</code></pre>", pformat(obj.response_content, width=200))

        return self.get_empty_value_display()

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: models.InterOpsCall | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: models.InterOpsCall | None = None) -> bool:
        return False
