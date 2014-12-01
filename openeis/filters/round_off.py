from openeis.filters import SimpleRuleFilter, register_column_modifier
from openeis.core.descriptors import ConfigDescriptor, Descriptor


@register_column_modifier
class RoundOff(SimpleRuleFilter):
    '''
    Round the value of a column to a specified number of places.
    '''
    
    def __init__(self, places=0, **kwargs):
        super().__init__(**kwargs)
        self.places = places
    
    def rule(self, time, value):
        return time, round(value, self.places)
    
    @classmethod
    def get_config_parameters(cls):
        description  = 'Number of places to round to. \n'
        description += 'i.e. 2 will round to 1.12345 to 1.12. \n'
        description += 'i.e. 0 will round to 123.12345 to 123. \n'
        description += 'i.e. -2 will round to 1234.12345 to 1200.'
        return {
                'places': ConfigDescriptor(int, "Rounding Places",
                                           description=description,
                                           value_default=0)
                }
        
    @classmethod
    def get_self_descriptor(cls):
        name = 'Rounding Filter'
        desc = 'Round the value of a column to a specified number of places.'
        return Descriptor(name=name, description=desc)