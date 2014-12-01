from openeis.filters.common import BaseSimpleNormalize, register_column_modifier
from openeis.core.descriptors import Descriptor


@register_column_modifier     
class Fill(BaseSimpleNormalize):
    '''
    Normalize values to a specified time period using the most recent previous value to supply any missing values.
    '''
    def calculate_value(self, target_dt):
        return target_dt, self.previous_point[1]
    
    @classmethod
    def get_self_descriptor(cls):
        name = 'Fill'
        desc = 'Normalize values to a specified time period using the most recent previous value to supply any missing values.'
        return Descriptor(name=name, description=desc)