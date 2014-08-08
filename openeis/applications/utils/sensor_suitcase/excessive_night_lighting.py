import datetime

def excessive_nighttime(light_data, operational_hours):
    """
    Excessive Nighttime Lightingchecks to see a single sensor should be flagged.
    Parameters:
        - light_data: a 2d array with datetime and data
            - lights are on (1) or off (0)
            - assumes light_data is only for operational hours
        - operational_hours: building's operational in hours a day
    Returns: True or False (true meaning that this sensor should be flagged)
    """
    # Grabs the first time it starts logging so we know when the next day is
    first_time = light_data[0][0]
    # counts the seconds when the lights are on
    time_on = datetime.timedelta(0)
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
            # check if lights were left on yesterday
            # take the last point form yesterday and add the time to time_on
            if (light_data[i-1][1] == 1):
                time_on += (light_data[i-1][0] - last_on)
            day_count += 1
        # check lights were turned off, if so, increment on_to_off, lights
        # are now off, add time on to timeOn
        if ((lights_on) and (light_data[i][1] == 0)):
            lights_on = False
            time_on += (light_data[i][0] - last_on)
        # check if lights were turned on, set last_On to the current time
        elif ((not lights_on) and (light_data[i][1] == 1)):
            on = True
            last_On = light_data[i][0]
        i += 1

    if (time_on.days != 0):
        total_time = (time_on.days * 24) + (time_on.seconds / 60)
    else:
        total_time = (time_on.seconds / 60)

    if ((total_time / day_count) > 3):
        return True
    else:
        return False

