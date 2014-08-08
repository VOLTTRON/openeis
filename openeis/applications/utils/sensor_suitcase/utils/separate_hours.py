from datetime import datetime

def separate_hours(data, op_hours, days_op, holidays=[]):
    """
    Given a dataset and a building's operational hours, this function will
    separate data from operational hours and non-operational hours.

    Parameters:
        - data: array of arrays that have [datetime, data]
        - op_hours: operational hour for the building in military time
            - i.e. [9, 17]
        - days_op: days of the week it is operational as a list
            - Monday = 1, Tuesday = 2 ... Sunday = 7
            - i.e. [1, 2, 3, 4, 5] is Monday through Friday
        - holidays: a list of datetime.date that are holidays.
            - data with these dates will be put into non-operational hours
    """
    operational = []
    non_op = []
    for point in data:
        if (point[0].date in holidays) or \
            (point[0].isoweekday() not in days_op):
            non_op.append(point)
        elif ((point[0].hour >= op_hours[0]) and (point[0].hour < op_hours[1])):
            operational.append(point)
        else:
            non_op.append(point)
    return operational, non_op
