from flask_marshmallow.fields import AbsoluteURLFor
from flask_marshmallow.sqla import ModelSchema
from marshmallow import (
    ValidationError,
    class_registry,
    fields,
    pre_load,
    validates_schema,
)


class BaseSchema(ModelSchema):
    """Overriden to add:
        * `href` field pointing to the resource URI
        * derived fields in the serialized output
        * nested fields in the serialized output
        * validation for non-existing field names
    """

    def __init__(self, *args, **kwargs):
        self.add_href_field()
        self.add_derived_fields()
        self.add_nested_fields()
        super().__init__(*args, **kwargs)

    def add_href_field(self):
        endpoint = "{}_api/show".format(self.Meta.model.__tablename__)
        url_field = AbsoluteURLFor(endpoint, id="<id>")
        self._declared_fields["href"] = url_field

    def add_derived_fields(self):
        model = self.Meta.model
        if not hasattr(model, "derived_fields"):
            return

        for field_name, field_type in model.derived_fields.items():
            field_cls = getattr(fields, field_type)
            self._declared_fields[field_name] = field_cls(dump_only=True)

    def add_nested_fields(self):
        model = self.Meta.model
        if not hasattr(model, "nested_fields"):
            return

        for field_name, config in model.nested_fields.items():
            resource_name = config["resource_name"]
            schema_name = "{}Schema".format(resource_name)
            self._declared_fields[field_name] = fields.Nested(schema_name, **config)

    @pre_load()
    def handle_nested_fields(self, data):
        """Expand (if needed) primary keys of nested related resources into a
        nested representation before loading a resource.

        Only single nested fields are handled. Attempting to update a
        collection of nested fields will raise a ValidationError.

        Example (assuming `category` is a nested field):

        >>> handle_nested_fields({ 'id': 1, 'name': 'Chair', 'category': 1 })
        {
            'id': 1,
            'name': 'Chair',
            'category': {
                'id': 1 ,
                'name': 'Furniture'
            }
        }
        """
        model = self.Meta.model
        if not hasattr(model, "nested_fields"):
            return data

        for field_name, config in model.nested_fields.items():
            if field_name not in data:
                continue

            if isinstance(data[field_name], dict):
                # Nested field is already expanded.
                continue

            related_field = self._declared_fields[field_name]
            related_schema = class_registry.get_class(related_field.nested)
            related_model = related_schema.Meta.model

            if config["many"]:
                error_msg = (
                    "Cannot update relationship through the `{model}` model. "
                    "An alternative is to direclty manipulate `{related_model}` objects."
                ).format(model=model.__name__, related_model=related_model.__name__)
                raise ValidationError(error_msg, field_names=[field_name])

            pk = data[field_name]
            related = related_model.query.get(pk)
            related_data, _ = related_schema().dump(related)
            for k in related_field.exclude:
                related_data.pop(k)
            data[field_name] = related_data

        return data

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError("Unknown field name {}".format(key))
