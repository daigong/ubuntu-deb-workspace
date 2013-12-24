#encoding:utf-8
import json
from bottle import request, Bottle, HTTPError

from location import helper

application = Bottle()


@application.get('/location/ip')
def query_ip():
    pass


@application.get('/location/wifi')
def query_wifi():
    try:
        macs = map(
            lambda x: (x[0], int(x[1])),
            [mac.split(',') for mac in request.query.q.split("|")][0:30]
        )
    except:
        raise HTTPError(400)
    wifi_chunks = helper.get_wifi_chunks(macs)
    _, chunk = helper.choose_chunk(wifi_chunks=wifi_chunks)
    if not chunk:
        raise HTTPError(404)
    chunk_point = chunk.avg()
    result = {
        'lat': chunk_point.lat,
        'lon': chunk_point.lng,
        'accuracy': chunk_point.accuracy
    }
    return json.dumps(result)


@application.get('/location/cell')
def query_cell():
    try:
        cells = map(
            lambda x: (';'.join([str(x[0]), str(x[1]), str(x[2])]), int(x[3])),
            [cell.split(',') for cell in request.query.q.split("|")][0:30]
        )
    except:
        raise HTTPError(400)
    cell_chunks = helper.get_cell_chunks(cells)
    _, chunk = helper.choose_chunk(cell_chunks=cell_chunks)
    if not chunk:
        raise HTTPError(404)
    chunk_point = chunk.avg()
    result = {
        'lat': chunk_point.lat,
        'lon': chunk_point.lng,
        'accuracy': chunk_point.accuracy
    }
    return json.dumps(result)


@application.get('/location/geolocate')
def query_geolocate():
    """
    request headers:
        Content-Type:application/json

    request body:
        {
            "wifi_access_points":[
                {
                    "mac":'11:11:11:11:11',
                    "rssi":66,
                },
            ],
            "cell_towers":[
                {
                    "cid":210,
                    "lac":320,
                    "mcc":460,
                    "mnc":00,
                    "rssi":90,
                },
            ]
        }
    response body:
        {
            "lat": 51.0,
            "lon": -0.1
            "accuracy": 1200.4
        }
    """
    query = request.json()
    cell_towers = query['cell_towers']
    wifi_access_points = query['wifi_access_points']
    mac_keys = [(p.mac, p.rssi) for p in wifi_access_points]
    cell_keys = [(';'.join([
        str(c.lac),
        str(c.cid),
        str(c.mcc)+str(c.mnc)
    ]), c.rssi) for c in cell_towers]
    cell_chunks = helper.get_cell_chunks(cell_keys)
    wifi_chunks = helper.get_wifi_chunks(mac_keys)
    loc_type, chunk = helper.choose_chunk(
        cell_chunks=cell_chunks, wifi_chunks=wifi_chunks)
    if not chunk:
        raise HTTPError(404)
    chunk_point = chunk.avg()
    result = {
        'lat': chunk_point.lat,
        'lon': chunk_point.lng,
        'loc_type': loc_type,
        'accuracy': chunk_point.accuracy
    }
    return json.dumps(result)
