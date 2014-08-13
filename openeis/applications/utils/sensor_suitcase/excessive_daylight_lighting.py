import datetime

def excessive_daylight(light_data, operational_hours):
    """
    Excessive Daylight checks to see a single sensor should be flagged.
    Parameters:
        - light_data: a 2d array with datetime and data
            - lights are on (1) or off (0)
            - assumes light_data is only for operational hours
        - operational_hours: building's operational in hours a day
    Returns: True or False (true meaning that this sensor should be flagged)
    """
    # Grabs the first time it starts logging so we know when the next day is
    first_time = light_data[0][0]
    # counts times when lights go from on to off
    on_to_off = 0
    # counts the seconds when the lights are on
    time_on = datetime.timedelta(0)
    # counts flagged days
    day_flag = 0
    # counts the total number of days
    day_count = 0

    # accounts for the first point, checks if the lights are on, sets when
    # lights were last set to on to the first time
    if (light_data[0][1] == 1):
        lights_on = True
        last_on = first_time
    else:
        lights_on = False

    # iterate through the light data
    i = 1
    while (i < len(light_data)):
        # check if it's a new day
        if (light_data[i][0].time() == first_time.time()):
            # check if it should be flagged, time delta is in seconds so / 3600
            # to get hours
            if (light_data[i][1] == 1):
                time_on += (light_data[i][0] - last_on)
            # turn days into hours to be compared to operational hours per day
            if (time_on.days != 0):
                time_on_hours = (24 * time_on.days) + time_on.seconds/3600
            else:
                time_on_hours = time_on.seconds/3600
            if ((on_to_off < 2) and \
                    ((time_on_hours / operational_hours) > 0.5)):
                day_flag += 1
            day_count += 1
        # check lights were turned off, if so, increment on_to_off, lights
        # are now off, add time on to timeOn
        if ((lights_on) and (light_data[i][1] == 0)):
            on_to_off += 1
            lights_on = False
            time_on += (light_data[i][0] - last_on)
        # check if lights were turned on, set last_On to the current time
        elif ((not lights_on) and (light_data[i][1] == 1)):
            on = True
            last_On = light_data[i][0]
        i += 1

    # if more than half of the days are flagged, there's a problem.
    if (day_flag / day_count > 0.5):
        return True
    else:
        return False

