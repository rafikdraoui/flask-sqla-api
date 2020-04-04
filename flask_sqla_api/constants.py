import marshmallow


class _FieldType:
    def __init__(self):
        for field_type in marshmallow.fields.__all__:
            setattr(self, field_type, field_type)


FieldType = _FieldType()
