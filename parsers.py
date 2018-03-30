from __future__ import print_function
from lxml import etree
from time import strptime
import pyshark

import stations

class ReadXML():

    timeformat = '%a %b %d %H:%M:%S %Y'

    def __init__(self, files_):
        self.result = stations.Stations()
        for f in files_:
            if f.split('.')[-1] == 'netxml':
                self.parse_netxml(f)
            elif f.split('.')[-1] == 'gpsxml':
                self.parse_gpsxml(f)

    def get_result(self):
        return self.result

    def parse_netxml(self, file_):
        elem = etree.iterparse(file_, tag='wireless-network')
        stats = stations.Stations()
        for e, child in elem:
            stats.update(self.sta_parse(child))
            child.clear()
        return stats

    def parse_gpsxml(self, file_):
        elem = etree.iterparse(file_, tag='gps-point')
        stats = stations.Stations()
        for e, child in elem:
            if child.get('bssid') == 'GP:SD:TR:AC:KL:OG' or not child.get('bssid'):
                pass
            else:
                utime = (float(child.get('time-usec', 0)) / (10 ** len(child.get('time-usec', '0'))))
                timestamp = int(child.get('time-sec', 0)) + utime
                point = stations.Point(float(child.get('lat', 0)),
                                       float(child.get('lon', 0)),
                                       float(child.get('alt', 0)),
                                       float(child.get('spd', 0)),
                                       int(child.get('signal_dbm', 0)),
                                       timestamp)

                sta = stations.Station(child.get('bssid'), points=fix_dbm(point))
                stats.update(sta)
                self.result.update(sta)
            child.clear()
        return stats

    def sta_parse(self, data):
        sta = stations.Station(data.find('BSSID').text)
        sta.update(type1='AP', type2=data.get('type'), manuf=data.find('manuf').text)
        sta.update(channel=int(data.find('channel').text))
        sta.update(last_seen=strptime(data.get('last-time'), self.timeformat))
        sta.update(first_seen=strptime(data.get('first-time'), self.timeformat))
        if not data.find('gps-info') is None:
            point = stations.Point(float(data.find('gps-info/max-lat').text),
                                   float(data.find('gps-info/max-lon').text),
                                   float(data.find('gps-info/max-alt').text),
                                   float(data.find('gps-info/max-spd').text),
                                   int(data.find('snr-info/max_signal_dbm').text))
        elif not data.find('snr-info') is None:
            point = stations.Point(0, 0, 0, 0, int(data.find('snr-info/max_signal_dbm').text))
        else:
            point = stations.Point(0, 0, 0, 0, 0,)
        sta.update(points=fix_dbm(point))

        ssid = data.find('SSID')
        if not ssid is None:
            for enc in ssid.findall('encryption'):
                sta.update(encryption=enc.text.split('+'))
            essid = ssid.find('essid')
            sta.update(essid=essid.text)
            sta.update(cloaked=True if ssid.find('essid').get('cloaked') == 'true' else False)
        for cli in data.findall('wireless-client'):
            client = self.client_parse(cli, sta)
            if client:
                sta.update(connected=client.bssid)
        self.result.update(sta)
        return sta

    def client_parse(self, data, sta):
        bssid = data.find('client-mac').text
        if bssid == sta:
            return None
        cli = stations.Station(bssid)
        if not data.find('gps-info') is None:
            point = stations.Point(float(data.find('gps-info/max-lat').text),
                                 float(data.find('gps-info/max-lon').text),
                                 float(data.find('gps-info/max-alt').text),
                                 float(data.find('gps-info/max-spd').text),
                                 int(data.find('snr-info/max_signal_dbm').text))
        elif not data.find('snr-info') is None:
            point = stations.Point(0, 0, 0, 0, int(data.find('snr-info/max_signal_dbm').text))
        else:
            point = stations.Point(0, 0, 0, 0, 0,)
        cli.update(points=fix_dbm(point))
        cli.update(type1='CL')
        cli.update(type2=data.get('type'))
        cli.update(manuf=data.find('client-manuf').text)
        cli.update(channel=int(data.find('channel').text))
        cli.update(last_seen=strptime(data.get('last-time'), self.timeformat))
        cli.update(first_seen=strptime(data.get('first-time'), self.timeformat))
        cli.update(connected=sta.bssid)
        if sta.essid:
            cli.update(probes_essid=sta.essid)
        self.result.update(cli)
        return cli

class ReadPcap(object):

    def __init__(self, files_, filter_=None):
        self.result = stations.Stations()
        self.filter = filter_
        for pf in files_:
            print('Analyze {}'.format(pf), end='\t')
            try:
                cap = pyshark.FileCapture(pf, display_filter=self.filter)
                for pack in cap:
                    if 'ppi' in pack and 'wlan' in pack and 'ta' in pack.wlan.field_names:
                        ta = str(pack.wlan.get_field('ta'))
                        sta = stations.Station(ta)
                        ra = str(pack.wlan.get_field('ra'))
                        if ra:
                            if ra != 'ff:ff:ff:ff:ff:ff':
                                sta.update(connected=ra)
                                self.result.update(stations.Station(ra, connected=ta))
                        if 'ppi_gps_lat' in pack.ppi.field_names and 'ppi_gps_lon' in pack.ppi.field_names:
                            lat = float(pack.ppi.ppi_gps_lat.replace(',', '.'))
                            lon = float(pack.ppi.ppi_gps_lon.replace(',', '.'))
                            alt = pack.ppi.get_field('ppi_gps_alt')
                            if not alt:
                                alt = 0
                            else:
                                alt = float(alt.replace(',', '.'))
                            dbm = pack.ppi.get_field('80211_common_dbm_antsignal')
                            if not dbm:
                                dbm = 0
                            else:
                                dbm = int(pack.ppi.get_field('80211_common_dbm_antsignal'))
                            sta.update(points=fix_dbm(stations.Point(lat, lon, alt, 0, dbm,
                                                      float(pack.sniff_timestamp), ra=ra)))
                        if 'wlan_mgt' in pack:
                            chn = pack.wlan_mgt.get_field('ds_current_channel')
                            if chn:
                                sta.update(channel=int(chn))
                            if pack.wlan.fc_type_subtype == '8':
                                ssid = pack.wlan_mgt.get_field('ssid')
                                if ssid and ssid != 'SSID: ':
                                    sta.update(essid=ssid)
                                sta.update(type1='AP')
                        self.result.update(sta)
            except pyshark.capture.capture.TSharkCrashException as err:
                print('FAIL')
            else:
                print('DONE')
        pass

    def get_result(self):
        return self.result

def fix_dbm(point):
    if point.dbm > 0:
        point.dbm = -point.dbm
    return point
