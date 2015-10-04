__author__ = 'dimm'
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

                sta = stations.Station(child.get('bssid'), points=point)
                stats.update(sta)
                self.result.update(sta)
            child.clear()
        return stats

    def sta_parse(self, sta):
        data = dict()
        bssid = sta.find('BSSID').text
        data['type1'] = 'AP'
        data['type2'] = sta.get('type')
        data['manuf'] = sta.find('manuf').text
        data['channel'] = int(sta.find('channel').text)
        data['last_seen'] = strptime(sta.get('last-time'), self.timeformat)
        data['first_seen'] = strptime(sta.get('first-time'), self.timeformat)
        if not sta.find('gps-info') is None:
            data['points'] = stations.Point(float(sta.find('gps-info/max-lat').text),
                                            float(sta.find('gps-info/max-lon').text),
                                            float(sta.find('gps-info/max-alt').text),
                                            float(sta.find('gps-info/max-spd').text),
                                            int(sta.find('snr-info/max_signal_dbm').text),)
        elif not sta.find('snr-info') is None:
            data['points'] = stations.Point(0, 0, 0, 0, int(sta.find('snr-info/max_signal_dbm').text),)
        else:
            data['points'] = stations.Point(0, 0, 0, 0, 0,)

        ssid = sta.find('SSID')
        if not ssid is None:
            data['encryption'] = set()
            for enc in ssid.findall('encryption'):
                data['encryption'].update(enc.text.split('+'))
            essid = ssid.find('essid')
            data['essid'] = essid.text
            data['cloaked'] = True if ssid.find('essid').get('cloaked') == 'true' else False
        for cli in sta.findall('wireless-client'):
            client = self.client_parse(cli, bssid, data)
            if client:
                data['connected'] = client.bssid
        sta = stations.Station(bssid, **data)
        self.result.update(sta)
        return sta

    def client_parse(self, cli, sta_bssid, sta_data):
        data = dict()
        bssid = cli.find('client-mac').text
        if bssid == sta_bssid:
            return None
        if not cli.find('gps-info') is None:
            data['points'] = stations.Point(float(cli.find('gps-info/max-lat').text),
                                   float(cli.find('gps-info/max-lon').text),
                                   float(cli.find('gps-info/max-alt').text),
                                   float(cli.find('gps-info/max-spd').text),
                                   int(cli.find('snr-info/max_signal_dbm').text),)
        elif not cli.find('snr-info') is None:
            data['points'] = stations.Point(0, 0, 0, 0, int(cli.find('snr-info/max_signal_dbm').text),)
        else:
            data['points'] = stations.Point(0, 0, 0, 0, 0,)
        data['type1'] = 'CL'
        data['type2'] = cli.get('type')
        data['manuf'] = cli.find('client-manuf').text
        data['channel'] = int(cli.find('channel').text)
        data['last_seen'] = strptime(cli.get('last-time'), self.timeformat)
        data['first_seen'] = strptime(cli.get('first-time'), self.timeformat)
        data['connected'] = sta_bssid
        if sta_data.get('essid'):
            data['probes_essid'] = sta_data.get('essid')
        sta = stations.Station(bssid, **data)
        self.result.update(sta)
        return sta

class ReadPcap(object):

    def __init__(self, files_, filter_=None):
        self.result = stations.Stations()
        self.filter = filter_
        for pf in files_:
            cap = pyshark.FileCapture(pf, display_filter=self.filter)
            for pack in cap:
                if 'ppi' in pack and 'wlan' in pack and 'ta' in pack.wlan.field_names:
                    data = dict()
                    ta = str(pack.wlan.get_field('ta'))
                    ra = str(pack.wlan.get_field('ra'))
                    if ra and ra != 'ff:ff:ff:ff:ff:ff':
                        data['connected'] = ra
                    if 'wlan_mgt' in pack:
                        chn = pack.wlan_mgt.get_field('ds_current_channel')
                        if chn:
                            data['channel'] = int(chn)
                    if 'ppi_gps_lat' in pack.ppi.field_names:
                        lat = float(pack.ppi.ppi_gps_lat.replace(',','.'))
                        lon = float(pack.ppi.ppi_gps_lon.replace(',','.'))
                        alt = pack.ppi.get_field('ppi_gps_alt')
                        if not alt:
                            alt = 0
                        else:
                            alt = float(alt.replace(',','.'))
                        dbm = pack.ppi.get_field('80211_common_dbm_antsignal')
                        if not dbm:
                            dbm = 0
                        else:
                            dbm = int(pack.ppi.get_field('80211_common_dbm_antsignal'))
                        data['points'] = stations.Point(lat, lon, alt, 0, dbm, float(pack.sniff_timestamp),
                                                        ra=ra)
                    if 'wlan_mgt' in pack and pack.wlan.fc_type_subtype == '8':
                        ssid = pack.wlan_mgt.get_field('ssid')
                        data['type1'] = 'AP'
                        if ssid and ssid != 'SSID: ':
                            data['essid'] = ssid
                    sta = stations.Station(ta, **data)
                    self.result.update(sta)
        pass

    def get_result(self):
        return self.result
