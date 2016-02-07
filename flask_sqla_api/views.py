from flask import json, make_response, request
from flask.views import MethodView


def json_response(data, status_code=200):
    response = make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    response.status_code = status_code
    return response


def api_error(status_code, message=None, payload=None):

    message_mapping = {
        400: 'Bad Request',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Internal Server Error',
    }
    message = message or message_mapping.get(status_code, 'Error')
    data = {'message': message}
    if payload:
        data['details'] = payload
    return json_response(data, status_code=status_code)


class BaseAPIView(MethodView):

    def __init__(self):
        self.schema = self.schema_cls()

    def get(self, id=None):
        if id is None:
            all_items = self.model.query.all()

            # We can't use self.schema.jsonify directly since top-level arrays
            # in JSON aren't supported in Flask
            output = self.schema_cls(many=True).dump(all_items).data
            return json_response(output)
        else:
            item = self.model.query.get(id)
            if item is None:
                return api_error(404)
            return self.schema.jsonify(item)

    def post(self):
        try:
            data = request.get_json()
            new_item, errors = self.schema.load(data)
        except:
            return api_error(400)
        if errors:
            return api_error(400, payload=errors)

        self.db.session.add(new_item)
        self.db.session.commit()

        output, errors = self.schema.dump(new_item)
        if errors:
            return api_error(500)

        response = self.schema.jsonify(new_item)
        response.status_code = 201
        response.headers['Location'] = output['href']
        return response

    def put(self, id):
        item = self.model.query.get(id)
        if item is None:
            return api_error(404)

        try:
            data = request.get_json()
            updated_item, errors = self.schema.load(data, instance=item, partial=True)
        except:
            return api_error(400)
        if errors:
            return api_error(400, payload=errors)

        self.db.session.add(updated_item)
        self.db.session.commit()

        return self.schema.jsonify(updated_item)

    def delete(self, id):
        item = self.model.query.get(id)
        if item is None:
            return api_error(404)
        self.db.session.delete(item)
        self.db.session.commit()
        return ''
