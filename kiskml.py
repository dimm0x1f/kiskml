#!/usr/bin/python
from __future__ import print_function

__author__ = 'dimm'
import optparse
import kml
import parsers
from stations import Stations
import glob


def show_all(stats):
    res_str = ''
    for i, sta in enumerate(filter(lambda x: x.type1 == 'AP', stats.values())):
        bp = sorted(list(sta.points), key=lambda x: x.dbm, reverse=True)
        astr = '{}# {} Ch:{} Points:{} ENC:{}'.format(i+1, sta.bssid, sta.channel,
                                                               len(sta.points), ','.join(sta.encryption))
        if sta.essid:
            essid = sta.essid
        else:
            essid = ''
        astr = '{} ESSID:{}'.format(astr, essid)
        if bp:
            astr = '{} Signal:{} dbm {}'.format(astr, bp[0].dbm if bp else 0, bp[0])
        res_str += astr + '\n'
        for ii, cl in enumerate(sta.connected):
            cstr = '\t{}# {}'.format(ii+1, cl)
            cli = stats.get(cl)
            if cli and cli.points:
                bpc = sorted(list(cli.points), key=lambda x: x.dbm, reverse=True)
                if bpc:
                    cstr = '{} Signal:{} dbm; Points:{}; {}'.format(cstr, bpc[0].dbm, len(cli.points), bpc[0])
            res_str += cstr + '\n'
        res_str += '\n'
    return res_str

def parse_opt():
    parser = optparse.OptionParser(description='This program reading kismet files(netxml, gpsxml, pcap) and build kml file')
    parser.add_option('-k', '--kml', type='string', action='store', dest='kml_file')
    parser.add_option('-f', '--filter', type='string', action='store', dest='filter')
    parser.add_option('--show', action='store_true', dest='show')

    return parser.parse_args()

def main():
    opts, args = parse_opt()
    pcaps = []
    xmls = []
    # gpsxml = []
    for arg in args:
        for f in glob.glob(arg):
            t = f.split('.')[-1]
            if t == 'pcapdump':
                pcaps.append(f)
            elif t == 'netxml':
                xmls.insert(0, f)
            elif t == 'gpsxml':
                xmls.append(f)
            else:
                print('"*.{}" is not supported!'.format(t))
    result = Stations()
    if pcaps:
        print('Reading {} pcap files'.format(len(pcaps)))
        pcap_reader = parsers.ReadPcap(pcaps, opts.filter)
        result.update(pcap_reader.get_result())
        del pcap_reader
    if xmls:
        print('Reading {} xml files'.format(len(xmls)))
        xml_reader = parsers.ReadXML(xmls)
        result.update(xml_reader.get_result())
        del xml_reader

    if opts.show and opts.kml_file != '-':
        show = show_all(result)
        print(show)
    if opts.kml_file:
        kml_f = kml.build_kml(result)
        if opts.kml_file == '-':
            print(kml_f.kml())
        else:
            kml_f.save(opts.kml_file)

if __name__ == '__main__':
    main()
