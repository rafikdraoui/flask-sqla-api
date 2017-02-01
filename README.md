# Flask-SQLA-API

Simple API wrapper for SQLAlchemy models in Flask.


## Disclaimer

You probably don't want to use that. This was quickly made to get a minimal
working web API going so that I could have something to work with when
experimenting with front-end programming. It's on GitHub because I wanted it to
be easily `pip`-installable from anywhere.

It is only tested on Python 3, only handles primary keys that are integers,
might only be working with models created through [Flask-SQLAlchemy][] (I
haven't tried with "vanilla" SQLAlchemy), and returns JSON with a very
minimalist structure. For example, a many-to-many relation is represented as a
simple list of ids, instead of having inlined resources, let alone any URIs
pointing to those resource.

If you need something more robust and configurable, have a look at
[Flask-RESTful][] or [Flask-Restless][].


## Quickstart

Assuming we have the following Flask app defining two (Flask-)SQLAlchemy models:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    items = db.relationship('Item', backref='category', lazy='dynamic')
```

Then we can expose REST-ish API endpoints at `/items/` and `/categories/` by
adding the following:


```python
from flask_sqla_api import Api

api = Api(app, db)

api.register_resource(Item, '/items/')
api.register_resource(Category, '/categories/')
```

And then run it with:

```python
if __name__ == '__main__':
    db.create_all()
    app.run()
```

We can now interact with the data through the usual `GET`, `POST`, `PUT`, and
`DELETE` HTTP requests.

```bash
$ curl -X POST :5000/items/ -H "Content-Type: application/json" -d '{"name": "Chair"}'
{
    "id": 1,
    "href": "http://localhost:5000/items/1/",
    "name": "Chair",
    "category": null
}

$ curl -X POST :5000/categories/ -H "Content-Type: application/json" -d '{"name": "Furniture"}'
{
    "id": 1,
    "href": "http://localhost:5000/categories/1/",
    "name": "Furniture",
    "items": []
}

$ curl -X PUT :5000/items/1/ -H "Content-Type: application/json" -d '{"category": 1}'
{
    "id": 1,
    "href": "http://localhost:5000/items/1/",
    "name": "Chair",
    "categories": 1
}

$ curl :5000/categories/1/
{
    "id": 1,
    "href": "http://localhost:5000/categories/1/",
    "name": "Furniture",
    "items": [1]
}

```

## Additional Features

### Derived Fields

We can specify some fields that don't correspond to any columns in the
database, but that should still be included in the serialized JSON output of
the resource.

This is done through the `derived_fields` attribute on the resource class,
which should be a dictionary with keys being the field names and values the
(marshmallow) field types.

#### Example

```python
from flask_sqla_api.constants import FieldType

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    items = db.relationship('Item', backref='category', lazy='dynamic')

    derived_fields = {
        'enthusiastic_name': FieldType.String,
        'is_long_name': FieldType.Boolean,
    }

    @property
    def enthusiastic_name(self):
        return self.name + '!!!'

    @property
    def is_long_name(self):
        return len(self.name) > 12
```

```bash
$ curl :5000/categories/1/
{
    "id": 1,
    "href": "http://localhost:5000/categories/1/",
    "name": "Furniture",
    "enthusiastic_name": "Furniture!!!"
    "is_long_name": false,
    "items": [1]
}
```

### Nested Fields

We can specify some related fields that should be nested (i.e. inlined) in the
serialized output.

This is done through the `nested_fields` attribute on the resource class, which
should be a dictionary with keys being the field names and values configuration
dictionaries.

These configuration dictionaries should have a key `resource_name` with the
class name of the nested resource as a value, and optionally some keyword
arguments for the `marshmallow.fields.Nested` constructor, like `many` or
`exclude`.

Note that loading resources with nested fields from data (for example, when
making a `PUT` request) won't work if including a collection of nested fields.


#### Example

```python
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    nested_fields = {
        'category': {
            'resource_name': 'Category',
            'many': False,
            'exclude': ['items'],
        },
    }
```

```bash
$ curl :5000/items/1/
{
  "id": 1,
  "href": "http://:5000/items/1/",
  "name": "Chair",
  "category": {
    "id": 1,
    "href": "http://:5000/categories/1/",
    "name": "Furniture"
  }
}
```


## Dependencies

This library depends on [Flask][], [flask-marshmallow][], and
[marshmallow-sqlalchemy][]. They should be automatically installed when
installing Flask-SQLA-API with `pip` or `setup.py`.

[Flask]: http://flask.pocoo.org
[flask-marshmallow]: https://flask-marshmallow.readthedocs.org
[marshmallow-sqlalchemy]: https://marshmallow-sqlalchemy.readthedocs.org

[Flask-SQLAlchemy]: http://flask-sqlalchemy.pocoo.org
[Flask-RESTful]: https://flask-restful.readthedocs.org
[Flask-Restless]: https://flask-restless.readthedocs.org
