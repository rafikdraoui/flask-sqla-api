from flask_marshmallow.fields import AbsoluteURLFor
from flask_marshmallow.sqla import ModelSchema
from marshmallow import validates_schema, ValidationError


class BaseSchema(ModelSchema):
    """Overriden to add an `href` field pointing to the resource URI, and to
    add validation for unknown field names.
    """

    def __init__(self, *args, **kwargs):
        self.add_href_field()
        super().__init__(*args, **kwargs)

    def add_href_field(self):
        endpoint = '{}_api/show'.format(self.Meta.model.__tablename__)
        url_field = AbsoluteURLFor(endpoint, id='<id>')
        self._declared_fields['href'] = url_field

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('Unknown field name {}'.format(key))
