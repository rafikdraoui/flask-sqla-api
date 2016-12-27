from flask_marshmallow.fields import AbsoluteURLFor
from flask_marshmallow.sqla import ModelSchema
from marshmallow import validates_schema, ValidationError, fields


class BaseSchema(ModelSchema):
    """Overriden to add an `href` field pointing to the resource URI, add
    derived fields to the serialized output, and to add validation for unknown
    field names.
    """

    def __init__(self, *args, **kwargs):
        self.add_href_field()
        self.add_derived_fields()
        super().__init__(*args, **kwargs)

    def add_href_field(self):
        endpoint = '{}_api/show'.format(self.Meta.model.__tablename__)
        url_field = AbsoluteURLFor(endpoint, id='<id>')
        self._declared_fields['href'] = url_field

    def add_derived_fields(self):
        model = self.Meta.model
        if not hasattr(model, 'derived_fields'):
            return

        for field_name, field_type in model.derived_fields.items():
            field_cls = getattr(fields, field_type)
            self._declared_fields[field_name] = field_cls(dump_only=True)

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('Unknown field name {}'.format(key))
