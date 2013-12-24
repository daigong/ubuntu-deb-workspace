#encoding:utf-8
import os
import leveldb
from location.geo import GeoChunk, ChunkPoint, GeoTools


here = os.path.abspath(os.path.dirname(__file__))
WIFI_DB = leveldb.LevelDB(os.path.join(here, '../data/wifi'))
CELL_DB = leveldb.LevelDB(os.path.join(here, '../data/cell'))
GEO_TOOLS = GeoTools()


def get_wifi_chunks(keys):
    chunks = []
    for mac, rssi in keys:
        try:
            value = WIFI_DB.Get(mac)
            lon, lat, accuracy, created_time = map(float, value.split(','))
            chunk_point = ChunkPoint(lat, lon, rssi, accuracy, created_time)
            hit = None
            for chunk in chunks:
                if chunk.check(chunk_point):
                    hit = chunk
                    chunk.add(chunk_point)
                    break
            if not hit:
                chunks.append(GeoChunk(chunk_point, 2000))
        except KeyError:
            continue
    chunks.sort(key=lambda chunk: len(chunk.point_list), reverse=True)
    return chunks


def get_cell_chunks(keys):
    chunks = []
    for cell, rssi in keys:
        try:
            value = CELL_DB.Get(cell)
            lon, lat, accuracy, created_time = map(float, value.split(','))
            chunk_point = ChunkPoint(lat, lon, rssi, accuracy, created_time)
            hit = None
            for chunk in chunks:
                if chunk.check(chunk_point):
                    hit = chunk
                    chunk.add(chunk_point)
                    break
            if not hit:
                chunks.append(GeoChunk(chunk_point, 2000))
        except KeyError:
            continue
    chunks.sort(key=lambda chunk: len(chunk.point_list), reverse=True)
    return chunks



def choose_chunk(**kwargs):
    wifi_chunks = kwargs.get("wifi_chunks", [])
    cell_chunks = kwargs.get("cell_chunks", [])
    if not wifi_chunks and not cell_chunks:
        return None, None
    elif not cell_chunks and wifi_chunks:
        if len(wifi_chunks) == 1:
            if len(wifi_chunks[0].point_list) == 1:
                return None, None
        elif len(wifi_chunks[0].point_list) == len(wifi_chunks[1].point_list):
            return None, None
        return 'wifi', wifi_chunks[0]
    loc_type, result_chunk = 'cell', cell_chunks[0]
    if wifi_chunks:
        for cell_chunk in cell_chunks:
            for wifi_chunk in wifi_chunks:
                cell_point = cell_chunk.avg(use_cached=True)
                wifi_point = wifi_chunk.avg(use_cached=True)
                distance = cell_point.distance(wifi_point)
                if distance < 5000 or distance < cell_point.accuracy:
                    result_chunk = wifi_chunk
                    loc_type = 'wifi'
                    break
    return loc_type, result_chunk
