
from django.db.models.sql import compiler
from django.db.models.fields import FieldDoesNotExist

class SQLCompiler(compiler.SQLCompiler):
    def resolve_columns(self, row, fields=()):
        if self.query.extra_select:
            row = list(row)
            for i, name in enumerate(self.query.extra_select):
                try:
                    field = self.query.model._meta.get_field_by_name(name)[0]
                except FieldDoesNotExist:
                    continue
                row[i] = field.to_python(row[i])
        return row

class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):
    pass

class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    pass

class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    pass

class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    pass

class SQLDateCompiler(compiler.SQLDateCompiler, SQLCompiler):
    pass

class SQLDateTimeCompiler(compiler.SQLDateTimeCompiler, SQLCompiler):
    pass


