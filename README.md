# flask-sqla-api

Simple API wrapper for SQLAlchemy models in Flask.


## Disclaimer

You probably don't want to use that. This was quickly made to get a minimal web
API going so that I could have something to work with when experimenting with
front-end programming.

It only handles primary keys that are integers, it might only be working with
models created through [Flask-SQLAlchemy][] (I haven't tried with "vanilla"
SQLAlchemy), and it returns JSON with a very minimalist structure. For example,
a many-to-many relation is represented as a simple list of ids, instead of
having inlined resources, let alone any URIs pointing to those resource.

If you need something more robust and configurable, have a look at
[Flask-RESTful][] or [Flask-Restless][].


## Quickstart

Assuming we have the following Flask app defining two (Flask-)SQLAlchemy models:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    items = db.relationship("Item", backref="category", lazy="dynamic")
```

Then we can expose REST-ish API endpoints at `/items/` and `/categories/` by
adding the following:


```python
from flask_sqla_api import Api

api = Api(app, db)

api.register_resource(Item, "/items/")
api.register_resource(Category, "/categories/")
```

And then run it with:

```python
db.create_all()
app.run()
```

We can now interact with the data through the usual `GET`, `POST`, `PUT`, and
`DELETE` HTTP requests.

```bash
$ curl -X POST http://localhost:5000/items/ -H "Content-Type: application/json" -d '{"name": "Chair"}'
{
  "category": null
  "href": "http://localhost:5000/items/1/",
  "id": 1,
  "name": "Chair",
}

$ curl -X POST http://localhost:5000/categories/ -H "Content-Type: application/json" -d '{"name": "Furniture"}'
{
  "href": "http://localhost:5000/categories/1/",
  "id": 1,
  "items": []
  "name": "Furniture",
}

$ curl -X PUT http://localhost:5000/items/1/ -H "Content-Type: application/json" -d '{"category": 1}'
{
  "categories": 1
  "href": "http://localhost:5000/items/1/",
  "id": 1,
  "name": "Chair",
}

$ curl http://localhost:5000/categories/1/
{
  "href": "http://localhost:5000/categories/1/",
  "id": 1,
  "items": [1],
  "name": "Furniture",
}

```

## Additional Features

### Derived Fields

We can specify some fields that don't correspond to any columns in the
database, but that should still be included in the serialized JSON output of
the resource.

This is done through the `derived_fields` attribute on the resource class,
which should be a dictionary where the keys are the field names and the values
are field types.

#### Example

```python
from flask_sqla_api.constants import FieldType


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    items = db.relationship("Item", backref="category", lazy="dynamic")

    derived_fields = {
        "enthusiastic_name": FieldType.String,
        "is_long_name": FieldType.Boolean,
    }

    @property
    def enthusiastic_name(self):
        return self.name + "!!!"

    @property
    def is_long_name(self):
        return len(self.name) > 12
```

```bash
$ curl http://localhost:5000/categories/1/
{
  "enthusiastic_name": "Furniture!!!"
  "href": "http://localhost:5000/categories/1/",
  "id": 1,
  "is_long_name": false,
  "items": [1]
  "name": "Furniture",
}
```

### Nested Fields

We can specify some related fields that should be nested (i.e. inlined) in the
serialized output.

This is done through the `nested_fields` attribute on the resource class, which
should be a dictionary where the keys are the field names and the values are
configuration dictionaries for those fields.

These configuration dictionaries should have a key `resource_name` with the
class name of the nested resource as a value, and optionally some keyword
arguments for the `marshmallow.fields.Nested` constructor, like `many` or
`exclude`.

#### Example

```python
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    nested_fields = {
        "category": {"resource_name": "Category", "many": False, "exclude": ["items"]},
    }
```

```bash
$ curl http://localhost:5000/items/1/
{
  "category": {
    "href": "http://localhost:5000/categories/1/",
    "id": 1,
    "name": "Furniture"
  }
  "href": "http://localhost:5000/items/1/",
  "id": 1,
  "name": "Chair",
}
```

## Dependencies

- [marshmallow][] (v2.x)
- [flask-marshmallow\[sqlalchemy\]][flask-marshmallow]


[Flask-SQLAlchemy]: http://flask-sqlalchemy.pocoo.org
[Flask-RESTful]: https://flask-restful.readthedocs.org
[Flask-Restless]: https://flask-restless.readthedocs.org

[marshmallow]: https://marshmallow.readthedocs.io/
[flask-marshmallow]: https://flask-marshmallow.readthedocs.org
