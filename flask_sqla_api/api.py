from .schema import BaseSchema
from .views import BaseAPIView, api_error


class Api:

    def __init__(self, app=None, db=None):
        self.resources = []
        if app and db:
            self.init_app(app, db)

    def init_app(self, app, db):
        self.app = app
        self.db = db

        for model, endpoint in self.resources:
            self._register_resource(model, endpoint)

        self.add_error_handlers()

        app.extensions['api'] = self

    def add_error_handlers(self):
        for status_code in (400, 405, 500):
            self.app.errorhandler(status_code)(lambda _: api_error(status_code))

    def register_resource(self, model, endpoint):
        if self.app is None or self.db is None:
            self.resources.append((model, endpoint))
        else:
            self._register_resource(model, endpoint)

    def _register_resource(self, model, endpoint):
        resource_name = model.__tablename__.title()

        schema_meta = type(
            '{}SchemaMeta'.format(resource_name),
            (BaseSchema.Meta,),
            {'model': model, 'sqla_session': self.db.session},
        )

        schema = type(
            '{}Schema'.format(resource_name),
            (BaseSchema,),
            {'Meta': schema_meta},
        )

        view = type(
            '{}API'.format(resource_name),
            (BaseAPIView,),
            {'model': model, 'schema_cls': schema, 'db': self.db}
        )

        self._register_endpoint(view, endpoint)

    def _register_endpoint(self, view, url):
        base_endpoint = '{}_api'.format(view.model.__tablename__)

        index_endpoint = base_endpoint + '/index'
        self.app.add_url_rule(
            url,
            defaults={'id': None},
            view_func=view.as_view(index_endpoint),
            methods=['GET'],
            endpoint=index_endpoint,
        )

        create_endpoint = base_endpoint + '/create'
        self.app.add_url_rule(
            url,
            view_func=view.as_view(create_endpoint),
            methods=['POST'],
            endpoint=create_endpoint,
        )

        show_endpoint = base_endpoint + '/show'
        self.app.add_url_rule(
            '{url}<int:id>/'.format(url=url),
            view_func=view.as_view(show_endpoint),
            methods=['GET', 'PUT', 'DELETE'],
            endpoint=show_endpoint,
        )
