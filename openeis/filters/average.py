from openeis.filters.common import BaseSimpleAggregate, register_column_modifier
from openeis.core.descriptors import Descriptor

@register_column_modifier     
class Average(BaseSimpleAggregate):
    '''
    Aggregate by averaging.
    '''
    def aggregate_values(self, target_dt, value_pairs):
        return sum(value for _, value in value_pairs)/len(value_pairs)
    
    @classmethod
    def get_self_descriptor(cls):
        name = 'Average'
        desc = 'Aggregate by averaging.'
        return Descriptor(name=name, description=desc)          