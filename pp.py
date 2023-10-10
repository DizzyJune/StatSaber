import math

def blCurve2(acc):
    pointList2 = [
        [1.0, 7.424],
        [0.999, 6.241],
        [0.9975, 5.158],
        [0.995, 4.01],
        [0.9925, 3.241],
        [0.99, 2.7],
        [0.9875, 2.303],
        [0.985, 2.007],
        [0.9825, 1.786],
        [0.98, 1.618],
        [0.9775, 1.49],
        [0.975, 1.392],
        [0.9725, 1.315],
        [0.97, 1.256],
        [0.965, 1.167],
        [0.96, 1.094],
        [0.955, 1.039],
        [0.95, 1.0],
        [0.94, 0.931],
        [0.93, 0.867],
        [0.92, 0.813],
        [0.91, 0.768],
        [0.9, 0.729],
        [0.875, 0.65],
        [0.85, 0.581],
        [0.825, 0.522],
        [0.8, 0.473],
        [0.75, 0.404],
        [0.7, 0.345],
        [0.65, 0.296],
        [0.6, 0.256],
        [0.0, 0.0]
    ]

    i = 0
    while i < len(pointList2):
        if pointList2[i][0] <= acc:
            break
        i += 1

    if i == 0:
        i = 1

    middle_dis = (acc - pointList2[i - 1][0]) / (pointList2[i][0] - pointList2[i - 1][0])
    return pointList2[i - 1][1] + middle_dis * (pointList2[i][1] - pointList2[i - 1][1])

def blInflate(peepee):
    return (650 * math.pow(peepee, 1.3)) / math.pow(650, 1.3)

def blCurve(acc, passRating, accRating, techRating):
    passPP = 15.2 * math.exp(math.pow(passRating, 1 / 2.62)) - 30
    if not math.isfinite(passPP) or math.isnan(passPP):
        passPP = 0
    accPP = blCurve2(acc) * accRating * 34
    techPP = math.exp(1.9 * acc) * 1.08 * techRating
    return blInflate(passPP + accPP + techPP)

def blPpFromAcc(acc, ratings, modeName='Standard'):
    if not ratings:
        return 0
    if modeName == 'rhythmgamestandard':
        return acc * ratings['passRating'] * 55
    else:
        return blCurve(acc, ratings['passRating'], ratings['accRating'], ratings['techRating'])