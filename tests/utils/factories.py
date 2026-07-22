import datetime
import random
import uuid

import factory
import factory.fuzzy


def generate_number(*, birth_date, sex_code=None, birth_place=None):
    if sex_code is None:
        sex_code = random.randint(1, 2)
    if birth_place is None:
        department = str(random.randint(1, 99)).zfill(2)
        random_1 = str(random.randint(0, 399)).zfill(3)
        birth_place = f"{department}{random_1}"
    else:
        assert len(birth_place) == 5
    gender = random.choice("137" if sex_code == 1 else "248")
    year_month = birth_date.strftime("%y%m")
    random_2 = str(random.randint(0, 399)).zfill(3)
    return f"{gender}{year_month}{birth_place}{random_2}"


class IdentityRequestFactory(factory.DictFactory):
    request_uid = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("last_name")
    first_names = factory.Faker("first_name")
    birth_date = factory.fuzzy.FuzzyDate(datetime.date(1968, 1, 1), datetime.date(1999, 12, 31))

    @factory.lazy_attribute
    def number(self):
        return generate_number(birth_date=self.birth_date)
