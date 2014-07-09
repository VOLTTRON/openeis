'''Support creating dynamic tables for application input and output.'''

# See this link for more information on dynamic tables:
# https://code.djangoproject.com/wiki/DynamicModels

import hashlib
import itertools
import sys

from django.core.management.color import no_style
from django.db import connections, models, transaction

from ..models import AppOutput


__all__ = ['table_exists', 'create_table', 'get_output_model']


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


def _create_model(model_name, project_id, fields, attrs=None):
    '''Dynamically generate a table model with the given fields.'''
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
    table_name = '_'.join([model_name.lower(), str(project_id), signature])
    attrs.update({name: _fields[type_](db_column='field{}'.format(i))
                  for i, (type_, name) in enumerate(field_groups)})
    attrs['Meta'] = type('Meta', (attrs.get('Meta', object),),
                         {'db_table': table_name})
    attrs.setdefault('__module__', __name__)
    hash = hashlib.md5()
    hash.update(table_name.encode('utf-8'))
    for key in sorted(attrs.keys()):
        hash.update(key.encode('utf-8'))
        hash.update(str(attrs[key]).encode('utf-8'))
    return type(model_name + '_' + hash.hexdigest(), (models.Model,), attrs)


def get_output_model(project_id, fields):
    '''Return a Django model with the given fields for application output.

    The table is unique to a project and includes project_id in the
    name, which takes the form 'dynappout_ID_SIG' where ID is replaced
    by the base-10 representation of project_id and SIG represents the
    count and type of the fields. The model references the AppOutput
    model to support storing output from multiple applications or
    application runs in the same table.

    fields is expected to be a dictionary or iterable of 2-tuples (such
    as is returned by dict.items()) containing (field_name, field_type)
    pairs. Field names must be valid Python identifiers and field types
    are strings indicating the data type and must be one of 'boolean',
    'datetime', 'float', 'integer', 'string', or 'timestamp'. The only
    difference between timestamp and datetime is that datetime values
    may be null. In the future, timestamp fields may be indexed
    automatically, so please only use them for time-series data.
    '''
    attrs = {'source': models.ForeignKey(AppOutput, related_name='+')}
    return _create_model('AppOutputData', project_id, fields, attrs)


#def main():
#    from openeis.projects.models import SensorIngest
#    model = create_model('DynamicTest', SensorIngest,
#                         (('time', 'datetime'), ('value', 'float')))
#    create_table(model, db='dynamic')


#if __name__ == '__main__':
#    main()
