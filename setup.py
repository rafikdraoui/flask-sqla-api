import io
from setuptools import setup, find_packages


short_description = 'Simple API wrapper for SQLAlchemy models in Flask'
with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='Flask-SQLA-API',
    version='0.1',
    url='https://github.com/rafikdraoui/flask-sqla-api/',
    author='Rafik Draoui',
    author_email='rafik@rafik.ca',
    license='MIT',
    description=short_description,
    long_description=long_description,
    install_requires=[
        'Flask',
        'flask-marshmallow',
        'marshmallow-sqlalchemy',
    ],
    packages=find_packages(),
)
