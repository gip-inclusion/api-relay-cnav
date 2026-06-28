import factory

from api_relay_cnav.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"user{n}@inclusion.gouv.fr")
    password = factory.django.Password(None)
    sub = factory.Sequence(lambda n: f"authentik-uid-{n}")
    is_staff = True
