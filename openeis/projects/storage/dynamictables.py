'''Support creating dynamic tables for application input and output.'''

# See this link for more information on dynamic tables:
# https://code.djangoproject.com/wiki/DynamicModels

import hashlib
import itertools

from django.core.management.color import no_style
from django.db import connections, models, transaction


__all__ = ['table_exists', 'create_table', 'create_model']


def table_exists(model, db='default'):
    '''Test if the table for the given model exists in the database.

    Returns True if the table exists, False otherwise. A database other
    than the default can be given with the db parameter.
    '''
    return model._meta.db_table in connections[db].introspection.table_names()


def create_table(model, db='default'):
    '''Create a table in the database for the given model.

    This routine will raise ValueError if the table already exists.
    Other database exceptions may also be raised.
    '''
    model = model._meta.concrete_model
    style = no_style()
    connection = connections[db]
    cursor = connection.cursor()

    # Get a list of already installed *models* so that references work right.
    tables = connection.introspection.table_names()
    if model._meta.db_table in tables:
        raise ValueError('table already exists for given model')
    seen_models = connection.introspection.installed_models(tables)
    created_models = set()
    pending_references = {}

    # Create the tables for each model
    with transaction.commit_on_success_unless_managed(using=db):
        # Create the model's database table, if it doesn't already exist.
        sql, references = connection.creation.sql_create_model(
                model, style, seen_models)
        seen_models.add(model)
        created_models.add(model)
        for refto, refs in references.items():
            pending_references.setdefault(refto, []).extend(refs)
            if refto in seen_models:
                sql.extend(connection.creation.sql_for_pending_references(
                        refto, style, pending_references))
        sql.extend(connection.creation.sql_for_pending_references(
                model, style, pending_references))
        for statement in sql:
            cursor.execute(statement)
        tables.append(connection.introspection.table_name_converter(
                model._meta.db_table))

    # Install SQL indices for all newly created models
    index_sql = connection.creation.sql_indexes_for_model(model, style)
    if index_sql:
        with transaction.commit_on_success_unless_managed(using=db):
            for sql in index_sql:
                cursor.execute(sql)


# Field type name to Django model type mapping.
_fields = {
    'boolean': lambda **kwargs: models.NullBooleanField(**kwargs),
    'datetime': lambda **kwargs: models.DateTimeField(null=True, **kwargs),
    'float': lambda **kwargs: models.FloatField(null=True, **kwargs),
    'integer': lambda **kwargs: models.IntegerField(null=True, **kwargs),
    'string': lambda **kwargs: models.TextField(null=True, **kwargs),
    'timestamp': lambda **kwargs: models.DateTimeField(**kwargs),
}


def create_model(model_name, table_basename, scope, fields, attrs=None):
    '''Dynamically generate a table model with the given fields.

    The table is unique to the given scope and includes scope in the
    name, which takes the form 'NAME_SCOPE_SIG' where name is replaced
    by table_basename.lower(), SCOPE is replaced by str(scope), and SIG
    is replaced by the count and type of the fields.

    fields is expected to be a dictionary or iterable of 2-tuples (such
    as is returned by dict.items()) containing (field_name, field_type)
    pairs. Field names must be valid Python identifiers and field types
    are strings indicating the data type and must be one of 'boolean',
    'datetime', 'float', 'integer', 'string', or 'timestamp'. The only
    difference between timestamp and datetime is that datetime values
    may be null. In the future, timestamp fields may be indexed
    automatically, so please only use them for time-series data.

    Additional model attributes may be passed as a dictionary via attrs.

    Django caches model classes during creation by app_label and
    model_name.  It is the responsibility of the caller to ensure that
    model_name does not clash with the names of any pre-existing models.
    Otherwise the pre-existing model will be returned rather than the
    one being created and errors will likely ensue.
    '''
    if attrs is None:
        attrs = {}
    if hasattr(fields, 'items'):
        fields = fields.items()
    field_groups = [(type_, name) for name, type_ in fields]
    field_groups.sort()
    # Group fields by type and count each type
    signature = ''.join('{}{}'.format(sum(1 for i in group), type_[0])
                        for type_, group in itertools.groupby(
                                field_groups, lambda x: x[0]))
    table_name = '_'.join([table_basename.lower(), str(scope), signature])
    attrs.update({name: _fields[type_](db_column='field{}'.format(i))
                  for i, (type_, name) in enumerate(field_groups)})
    attrs['Meta'] = type('Meta', (attrs.get('Meta', object),),
                         {'db_table': table_name})
    attrs.setdefault('__module__', __name__)
    attrs.setdefault('__name__', model_name)
    return type(model_name, (models.Model,), attrs)
