from django.urls import reverse

from tests.audits.factories import InterOpsCallFactory


def test_all_admin(admin_client):
    call = InterOpsCallFactory()
    # List view
    response = admin_client.get(reverse("admin:audits_interopscall_changelist"))
    assert response.status_code == 200

    # Add view
    response = admin_client.get(reverse("admin:audits_interopscall_add"))
    assert response.status_code == 403

    # Change view
    url = reverse("admin:audits_interopscall_change", args=(call.pk,))
    response = admin_client.get(url)
    assert response.status_code == 200

    # Test with imvalid XML
    invalid_call = InterOpsCallFactory(interops_request_content="Pas du XML")
    url = reverse("admin:audits_interopscall_change", args=(invalid_call.pk,))
    response = admin_client.get(url)
    assert response.status_code == 200
