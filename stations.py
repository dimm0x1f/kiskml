__author__ = 'dimm'


class Station(object):
    def __init__(self, bssid, **kwargs):
        self.bssid = bssid
        self.points = set()
        self.probes_essid = set()
        self.connected = set()
        self.channel = None
        self.type1 = None
        self.type2 = None
        self.manuf = None
        self.encryption = set()
        self.cloaked = None
        self.essid = None
        self.last_seen = None
        self.first_seen = None
        self.update(**kwargs)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.bssid == other
        elif isinstance(other, self.__class__):
            return self.bssid == other.bssid
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.bssid)

    def __str__(self):
        return self.bssid

    def _check_bssid(self):
        pass

    def update(self, **kwargs):
        point = kwargs.get('points', set())
        if isinstance(point, Point):
            self.points.add(point)
        elif isinstance(point, (set, list, tuple)):
            self.points.update(point)
        else:
            raise TypeError

        probes_essid = kwargs.get('probes_essid', set())
        if isinstance(probes_essid, str):
            self.probes_essid.add(probes_essid)
        elif isinstance(probes_essid, (set, list, tuple)):
            self.probes_essid.update(probes_essid)
        else:
            raise TypeError

        connected = kwargs.get('connected', set())
        if isinstance(connected, str):
            self.connected.add(connected)
        elif isinstance(connected, (set, list, tuple)):
            self.connected.update(connected)
        else:
            raise TypeError

        self.channel = kwargs.get('channel', self.channel)
        self.type1 = kwargs.get('type1', self.type1)
        self.type2 = kwargs.get('type2', self.type2)
        self.manuf = kwargs.get('manuf', self.manuf)
        self.encryption = kwargs.get('encryption', self.encryption)
        self.cloaked = kwargs.get('cloaked', self.cloaked)
        self.essid = kwargs.get('essid', self.essid)
        self.last_seen = kwargs.get('last_seen', self.last_seen)
        self.first_seen = kwargs.get('first_seen', self.first_seen)


class Stations(dict):
    # def __contains__(self, item):
    #     for station in self.values():
    #         if station == item:
    #             return True
    #     return False

    def update(self, E=None, **F):
        def elem_upd(elem):
            if elem in self:
                self[elem].update(points=elem.points)
                self[elem].update(probes_essid=elem.probes_essid)
                self[elem].update(connected=elem.connected)
                self[elem].update(channel=elem.channel)
                self[elem].update(type1=elem.type1)
                self[elem].update(type2=elem.type2)
                self[elem].update(encryption=elem.encryption)
                self[elem].update(essid=elem.essid)
            else:
                dict.update(self, {elem.bssid: elem})

        if isinstance(E, Station):
            elem_upd(E)

        elif isinstance(E, (self.__class__)):
            for e in E.values():
                elem_upd(e)

        elif E is None:
            pass

        else:
            errstr = "descriptor 'update' requires a 'Station' or 'Stations' " \
                     "objects but received a '{}'".format(E.__class__)
            raise TypeError(errstr)


class Point(object):
    def __init__(self, lat, lon, alt, spd=0, dbm=None, timestamp=None, **other):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.spd = spd
        self.dbm = dbm
        self.timestamp = timestamp
        self.other = other

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        return False

    def __hash__(self):
        return hash((self.lat, self.lon, self.alt, self.spd, self.dbm))

    def __str__(self):
        return '{},{}'.format(self.lat, self.lon)

