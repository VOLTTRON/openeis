from datetime import datetime, timezone
import random

from django.conf import settings
from django.test import TestCase
from django.test.utils import setup_test_environment

from openeis.projects import models
from openeis.projects.storage import dynamictables as dyn
from openeis.projects.storage import sensorstore


now = lambda: datetime.now().replace(tzinfo=timezone.utc)


def get_output_model(project_id, fields):
    '''Return a Django model with the given fields for application output.'''
    attrs = {'source': models.models.ForeignKey(
             models.AppOutput, related_name='+')}
    return dyn.create_model('AppOutputData', project_id, fields, attrs)


class TestDynamicModelCreation(TestCase):
    def setUp(self):
        setup_test_environment()

    def test_table_naming(self):
        '''Test that table and fields are properly named and ordered.

        The table signature is based on the numer and types of fields.
        Changing the order of the fields or their names should have no
        effect on the table signature. However, changing the number of
        fields or their types will change the model.

        This test also checks creating fields using lists, dictionaries,
        and iterators.
        '''
        fields = [('test0', 'datetime'), ('test1', 'string'),
                  ('test2', 'datetime'), ('test3', 'float'),
                  ('test4', 'integer'), ('test5', 'integer'),
                  ('test6', 'float'), ('test7', 'float'),
                  ('test8', 'datetime'), ('test9', 'datetime')]
        expect = [('id', None, 'AutoField'), ('source', None, 'ForeignKey'),
                  ('test0', 'field0', 'DateTimeField'),
                  ('test2', 'field1', 'DateTimeField'),
                  ('test8', 'field2', 'DateTimeField'),
                  ('test9', 'field3', 'DateTimeField'),
                  ('test3', 'field4', 'FloatField'),
                  ('test6', 'field5', 'FloatField'),
                  ('test7', 'field6', 'FloatField'),
                  ('test4', 'field7', 'IntegerField'),
                  ('test5', 'field8', 'IntegerField'),
                  ('test1', 'field9', 'TextField')]

        def check_names(fields, project_id=131,
                        table_name='appoutputdata_131_4d3f2i1s'):
            model = get_output_model(project_id, fields)
            self.assertEqual(model._meta.db_table, table_name)
            self.assertEqual([(f.name, f.db_column, f.__class__.__name__)
                              for f in model._meta.fields], expect)
            return model

        def test_create(model):
            self.assertFalse(dyn.table_exists(model))
            dyn.create_table(model)
            self.assertTrue(dyn.table_exists(model))

        # Test model generation with the same fields in different orders
        # and by different values.
        model1 = check_names(fields)
        fields.reverse()
        self.assertTrue(check_names(iter(fields)) is model1)
        random.shuffle(fields)
        self.assertTrue(check_names(dict(fields)) is model1)
        test_create(model1)

        # Test model with different field names, but same signature.
        for i, (name, field_type) in enumerate(fields):
            fields[i] = ('x' + name, field_type)
        for i, (name, db_column, field_class) in enumerate(expect):
            expect[i] = (('x' + name if name.startswith('test') else name),
                         db_column, field_class)
        model2 = check_names(fields)
        self.assertFalse(model2 is model1)
        self.assertTrue(dyn.table_exists(model2))

        # Remove a field and test that the model differs from previous
        # models.
        fields.remove(('xtest5', 'integer'))
        expect[-2:] = [('xtest1', 'field8', 'TextField')]
        model3 = check_names(fields, table_name='appoutputdata_131_4d3f1i1s')
        self.assertFalse(model3 is model1)
        self.assertFalse(model3 is model2)
        test_create(model3)

        # Changing only the project_id should result in a new model
        model4 = check_names(fields, 241, 'appoutputdata_241_4d3f1i1s')
        self.assertFalse(model4 is model3)
        test_create(model4)

    def test_create_insert(self):
        '''Test table creation and insertion'''
        user = models.User.objects.create(username='dynamo')
        project = models.Project.objects.create(
                name='Dynamic Model Test', owner=user)
        output = models.AppOutput.objects.create()
        fields = {'time': 'timestamp', 'value': 'float',
                  'flags': 'integer', 'note': 'string'}
        model = get_output_model(project.pk, fields)
        self.assertFalse(dyn.table_exists(model))
        dyn.create_table(model)
        self.assertTrue(dyn.table_exists(model))
        item = model(source=output, time=now(),
                     value=12.34, note='Testing')
        item.save()
        self.assertEqual(model.objects.count(), 1)
        item = model(source=output, time=now(),
                     value=2.345, note='Testing again')
        item.save()
        self.assertEqual(model.objects.count(), 2)
        item = model.objects.get(pk=item.id)
        self.assertEqual(item.value, 2.345)
        self.assertEqual(item.note, 'Testing again')

    def test_create_output(self):
        def tolist(objs):
            result = [(x.pk, x.source.id, x.time, x.value, x.flags, x.note)
                      for x in objs]
            result.sort()
            return result
        fields = {'time': 'timestamp', 'value': 'float',
                  'flags': 'integer', 'note': 'string'}
        output, model = sensorstore.create_output(5, fields)
        self.assertTrue(dyn.table_exists(model))
        items = tolist(model.objects.create(time=now(), value=float(i),
                 note='Testing {}'.format(i)) for i in range(5))
        objs = tolist(model.objects.all())
        self.assertEqual(objs, items)
        model = sensorstore.get_output(output, 5, fields)
        objs = tolist(model.objects.all())
        self.assertEqual(objs, items)

    def test_bulk_create(self):
        fields = {'time': 'timestamp', 'value': 'float',
                  'flags': 'integer', 'note': 'string'}
        output, model = sensorstore.create_output(5, fields)
        self.assertTrue(dyn.table_exists(model))
        items = [model(time=now(), value=float(i), note='Testing {}'.format(i))
                 for i in range(5)]
        model.objects.bulk_create(items)
        self.assertEqual(model.objects.count(), 5)
        output, model = sensorstore.create_output(6, fields)
        self.assertTrue(dyn.table_exists(model))
        items = [model(time=now(), value=float(i), note='Testing {}'.format(i))
                 for i in range(5)]
        model.objects.bulk_create(items)
        self.assertEqual(model.objects.count(), 5)
