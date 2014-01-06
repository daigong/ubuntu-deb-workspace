import math
from collections import namedtuple


class GeoTools(object):
    @classmethod
    def distance(cls, lat1, lng1, lat2, lng2):
        rad = lambda d: d * math.pi/180.0
        radlat1 = rad(lat1)
        radlat2 = rad(lat2)
        a = radlat1 - radlat2
        b = rad(lng1) - rad(lng2)
        s = 2 * math.asin(math.sqrt(
            math.pow(math.sin(a/2), 2) +
            math.cos(radlat1) * math.cos(radlat2) * math.pow(math.sin(b/2), 2)
        ))
        return abs(s * 6378137.0)


BaseChunkPoint = namedtuple(
    "ChunkPoint",
    ["lat", "lng", "rssi", "accuracy", "created_time"]
)


class ChunkPoint(BaseChunkPoint):

    geo_tools = GeoTools()

    def distance(self, chunk_point):
        return self.geo_tools.distance(
            self.lat,
            self.lng,
            chunk_point.lat,
            chunk_point.lng
        )


class GeoChunk(object):
    geo_tools = GeoTools()

    def __init__(self, chunk_point, max_distance):
        self.created_time = chunk_point.created_time
        self.chunk_box = {
            'min_lat': chunk_point.lat,
            'min_lng': chunk_point.lng,
            'max_lat': chunk_point.lat,
            'max_lng': chunk_point.lng,
        }
        self.avg_cached = None
        self.point_list = [chunk_point, ]
        self.max_distance = max_distance

    def check(self, chunk_point):
        if self.geo_tools.distance(
            chunk_point.lat,
            chunk_point.lng,
            self.chunk_box['max_lat'],
            self.chunk_box['max_lng']
        ) > self.max_distance and self.geo_tools.distance(
            chunk_point.lat,
            chunk_point.lng,
            self.chunk_box['min_lat'],
            self.chunk_box['min_lng']
        ) > self.max_distance:
            return False
        return True

    def __len__(self):
        return len(self.point_list)

    def add(self, chunk_point):
        if chunk_point.lat < self.chunk_box['min_lat']:
            self.chunk_box['min_lat'] = chunk_point.lat
        elif chunk_point.lat > self.chunk_box['max_lat']:
            self.chunk_box['max_lat'] = chunk_point.lat
        if chunk_point.lng < self.chunk_box['min_lng']:
            self.chunk_box['min_lng'] = chunk_point.lng
        elif chunk_point.lng > self.chunk_box['max_lng']:
            self.chunk_box['max_lng'] = chunk_point.lng
        if self.created_time < chunk_point.created_time:
            self.created_time = chunk_point.created_time
        self.point_list.append(chunk_point)

    def avg(self, use_cached=True):
        if not use_cached or not self.avg_cached:
            point_list = sorted(self.point_list, key=lambda p: p.accuracy, reverse=True)
            if len(point_list) > 1:
                if len(point_list) > 3:
                    point_list = point_list[1:-1]
                length = len(point_list)
                lat, lng, rssi, accuracy = map(lambda x: x / length, reduce(
                    lambda x, y: (
                        x[0] + y[0],
                        x[1] + y[1],
                        x[2] + y[2],
                        x[3] + y[3],
                    ),
                    point_list
                ))
                self.avg_cached = ChunkPoint(
                    lat, lng, rssi, accuracy, self.created_time)
            else:
                self.avg_cached = self.point_list[0]
        return self.avg_cached
