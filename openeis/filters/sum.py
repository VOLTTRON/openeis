from openeis.filters.common import BaseSimpleAggregate, register_column_modifier
from openeis.core.descriptors import Descriptor

@register_column_modifier     
class Sum(BaseSimpleAggregate):
    '''
    Aggregate by summation.
    '''
    
    def aggregate_values(self, target_dt, value_pairs):
        return sum(value for _, value in value_pairs)
    
    @classmethod
    def get_self_descriptor(cls):
        name = 'Sum'
        desc = 'Aggregate by summation.'
        return Descriptor(name=name, description=desc)