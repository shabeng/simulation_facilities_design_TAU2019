from scipy.spatial import distance


def calc_distance(loc1, loc2):
    dist = distance.cityblock(loc1, loc2)
    return dist


def calc_time_dur(dist, speed):
    return float(dist)/speed
