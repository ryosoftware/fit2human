from datetime import datetime, timezone, timedelta

import fit2human

import json
import sys
import os

HR_ZONES = {
    "Según umbral de lactato": [ 130, 147, 155, 163 ],
    "Según valor de FC máximo": [ 124, 143, 154, 170 ],
    "Según valor de FC en reposo": [ 131, 143, 150, 160 ],
}

def summarize_hr_by_number(data):
    if len(data["record_mesgs"]):
        summary_by_number = {}
        unknown, total = 0, 0
        for record_mesg in data["record_mesgs"]:
            heart_rate_found = False
            for heart_rate_source in [ 'external heart rate', 'wrist heart rate' ]:
                if heart_rate_source in record_mesg:
                    hr = record_mesg[heart_rate_source]
                    if hr not in summary_by_number: summary_by_number[hr] = 0
                    summary_by_number[hr] = summary_by_number[hr] + 1
                    total = total + 1
                    heart_rate_found = True
                    break
            if not heart_rate_found: unknown = unknown + 1
        summary_by_number['U'] = unknown
        summary_by_number['T'] = total
        return summary_by_number
    return None

def summarize_hr_by_zone(summary_by_number, zones):
    summary_by_zone = [0] * (len(zones) + 1)
    for hr in summary_by_number:
        if not isinstance(hr, int): continue
        seconds = summary_by_number[hr]
        zone_found = False
        for zone in range(len(zones) - 1, -1, -1):
            if hr > zones[zone]:
                summary_by_zone[zone + 1] = summary_by_zone[zone + 1] + seconds
                zone_found = True
                break
        if not zone_found: summary_by_zone[0] = summary_by_zone[0] + seconds
    return summary_by_zone

def get_file_hr_summary(data):
    for subdata in data['time_in_zone_mesgs']:
        if subdata['reference_mesg'] == 'session':
            hr_times, hr_limits = [ 0, 0, 0, 0, 0 ], [ 0, 0, 0, 0, 0 ]
            for i in range(0, len(subdata['hr_zone_high_boundary'])):
                j = max(0, min(i - 1, len(hr_times) - 1))
                hr_times[j] = hr_times[j] + subdata['time_in_hr_zone'][i]
                hr_limits[j] = subdata['hr_zone_high_boundary'][i]
            hr_limits.pop()
    return hr_times, hr_limits

def print_summary_by_zone(description, summary_by_zone, zones):
    print(description)
    print("\n")
    if summary_by_zone:
        total = sum(summary_by_zone)
        for index, seconds in enumerate(summary_by_zone):
            if index == 0: hr_zone_string = "HR menor que %d" % (zones[0])
            elif index < len(zones): hr_zone_string = "HR entre %d y %d" % (zones[index - 1], zones[index])
            else: hr_zone_string = "HR mayor que %d" % (zones[len(zones) - 1])
            print("Zona %d (%s): %.02f%%" % (index + 1, hr_zone_string, 100 * seconds / total))
    else:
        print("Sin datos")
    print("\n")

def main():
    if len(sys.argv) < 2:
        print('No input file received')
    else:
        source = sys.argv[1]
        data = None
        if os.path.splitext(source)[1] == '.fit':
            data = fit2human.main(source, 'json')
            if not data: print('Cannot load json data')
            else: data = json.loads(data)
        else:
            with open(source) as json_file: data = json.load(json_file)
        if data:
            file_hr_times, file_hr_zones = get_file_hr_summary(data)
            print_summary_by_zone("Según zonas definidas en el reloj", file_hr_times, file_hr_zones)
            summary = summarize_hr_by_number(data)
            for zones_description in HR_ZONES: print_summary_by_zone(zones_description, summarize_hr_by_zone(summary, HR_ZONES[zones_description]), HR_ZONES[zones_description])

if __name__ == "__main__": main()
