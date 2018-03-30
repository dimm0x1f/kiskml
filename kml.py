__author__ = 'dimm'
import simplekml
from time import localtime, strftime

descr = """SSID: {}<br />
TA: {}<br />
RA: {}<br />
Channel: {}<br />
Time: {}<br />
Chipter: {}<br />
GPS: {}"""

redstyle = simplekml.Style()
ornstyle = simplekml.Style()
grnstyle = simplekml.Style()
grastyle = simplekml.Style()
redstyle.iconstyle.icon.href = 'http://labs.google.com/ridefinder/images/mm_20_red.png'
ornstyle.iconstyle.icon.href = 'http://labs.google.com/ridefinder/images/mm_20_orange.png'
grnstyle.iconstyle.icon.href = 'http://labs.google.com/ridefinder/images/mm_20_green.png'
grastyle.iconstyle.icon.href = 'http://labs.google.com/ridefinder/images/mm_20_gray.png'

def build_kml(stats, out=None):
    kml = simplekml.Kml()
    apfold = kml.newfolder(name='AP')
    clfold = kml.newfolder(name='Station')
    for sta in sorted(stats.values(), key=lambda x: x.bssid):
        if sta.type1 == 'AP':
            fold = apfold.newfolder(name=sta.bssid)
        else:
            fold = clfold.newfolder(name=sta.bssid)
        for p in point_filter(sta.points):
            pnt = fold.newpoint(name=str(p.dbm))
            timst = strftime('%a %b %d %H:%M:%S %Y', localtime(p.timestamp))
            pnt.description = descr.format(sta.essid, sta.bssid, p.other.get('ra'), sta.channel,
                                           timst, ' '.join(sta.encryption), ','.join((str(p.lat), str(p.lon))))
            pnt.coords=[(p.lon, p.lat, p.alt)]
            if p.dbm <= -80:
                pnt.style = redstyle
            elif p.dbm <= -70:
                pnt.style = ornstyle
            elif p.dbm >= 0:
                pnt.style = grastyle
            else:
                pnt.style = grnstyle
    return kml


def point_filter(points, rad=0.0001):
    cpoints = list()
    gpoints = []
    for sp in points:
        #gr = []
        if not sp in gpoints:
            cpoints.append(sp)
            for p in points:
                if sp.lon - rad < p.lon < sp.lon + rad and sp.lat - rad < p.lat < sp.lat + rad and sp.dbm == p.dbm:
                    #gr.append(p)
                    gpoints.append(p)
    return cpoints
