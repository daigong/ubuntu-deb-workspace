import xapian


class DefaultSorter(object):

    def __init__(self, request, enquire):
        self.request = request
        self.enquire = enquire

    def sort(self):
        return self.enquire


class DistanceSorter(xapian.LatLongDistanceKeyMaker):

    def __init__(self, request, enquire):
        self.request = request
        self.enquire = enquire
        lat, lon, radius = self.request.GET.get('range', ',,').split(',')
        if lat and lon and radius:
            self.washington = float(lat), float(lon)
        center = xapian.LatLongCoords()
        metric = xapian.GreatCircleMetric()
        center.append(xapian.LatLongCoord(float(lat), float(lon)))
        xapian.LatLongDistanceKeyMaker.__init__(self, 3, center, metric)

    def sort(self):
        if self.washington:
            self.enquire.set_sort_by_key_then_relevance(self, False)
        return self.enquire


class HeatSorter(DefaultSorter):

    def sort(self):
        self.enquire.set_sort_by_value_then_relevance(6, True)
        return self.enquire


sorters = {
    0: DefaultSorter,
    1: DistanceSorter,
    2: HeatSorter
}
set_enquire_sorter = lambda request, enquire, st: sorters.get(
    st, DefaultSorter)(request, enquire).sort()
