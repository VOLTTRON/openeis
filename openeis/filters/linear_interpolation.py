from openeis.filters.common import BaseSimpleNormalize, register_column_modifier
from openeis.core.descriptors import Descriptor


@register_column_modifier    
class LinearInterpolation(BaseSimpleNormalize):
    '''
    Normalize values to a specified time period using Linear Interpolation to 
    supply missing values.
    '''
    
    def calculate_value(self, target_dt):
        x0 = self.previous_point[0]
        x1 = self.next_point[0]
        if x1 <= target_dt <= x0:
            raise RuntimeError('Tried to interpolate value during incorrect state.')
        y0 = self.previous_point[1]
        y1 = self.next_point[1]
        return target_dt, y0 + ((y1-y0)*((target_dt-x0)/(x1-x0)))
        
    @classmethod
    def get_self_descriptor(cls):
        name = 'Linear Interpolation'
        desc = 'Normalize values to a specified time period using Linear Interpolation to supply missing values.'
        return Descriptor(name=name, description=desc)
