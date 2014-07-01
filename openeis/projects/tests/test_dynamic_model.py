from datetime import datetime, timezone
import random

from django.conf import settings
from django.test import TestCase
from django.test.utils import setup_test_environment

from openeis.projects import models
from openeis.projects.storage import dynamictables as dyn


class TestDynamicModelCreation(TestCase):
    def setUp(self):
        setup_test_environment()

    def _setup_model_depends(self):
        user = models.User(username='dynamo')
        user.save()
        self.project = models.Project(name='Dynamic Model Test', owner=user)
        self.project.save()
        self.output = models.AppOutput()
        self.output.save()
        
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
            model = dyn.get_output_model(project_id, fields)
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
        model3 = check_names(fields, 212, 'appoutputdata_212_4d3f1i1s')
        self.assertFalse(model3 is model1)
        self.assertFalse(model3 is model2)
        test_create(model3)

    def test_create_insert(self):
        '''Test table creation and insertion'''
        self._setup_model_depends()
        fields = {'time': 'timestamp', 'value': 'float',
                  'flags': 'integer', 'note': 'string'}
        model = dyn.get_output_model(self.project.id, fields)
        self.assertFalse(dyn.table_exists(model))
        dyn.create_table(model)
        self.assertTrue(dyn.table_exists(model))
        now = lambda: datetime.now().replace(tzinfo=timezone.utc)
        item = model(source=self.output, time=now(),
                     value=12.34, note='Testing')
        item.save()
        self.assertEqual(model.objects.count(), 1)
        item = model(source=self.output, time=now(),
                     value=2.345, note='Testing again')
        item.save()
        self.assertEqual(model.objects.count(), 2)
        item = model.objects.get(pk=item.id)
        self.assertEqual(item.value, 2.345)
        self.assertEqual(item.note, 'Testing again')
