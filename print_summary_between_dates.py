import os
import re
import sys
import subprocess
from datetime import datetime

get_fit_file_summary_data = "/home/roberto/fit2human/print_rellevant_data_from_fit_file.py"

def get_time_from_human_readable_date(date: str) -> int:
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date)
    if match:
        year, month, day = map(int, match.groups())
        date = datetime(year, month, day)
        return int(date.timestamp())
    return None

def get_seconds_from_human_readable_time(time: str) -> int:
    parts = time.split(":")
    total = 0
    multiplier = 1
    for part in reversed(parts):
        total += int(part) * multiplier
        multiplier *= 60
    return total

def get_human_readable_time(seconds: int) -> str:
    time_str = ""
    divider = 3600
    while seconds > 0 and divider >= 1:
        if seconds // divider > 0:
            time_str += "%s%02d" % ( ":" if time_str else "", seconds // divider )
            seconds = seconds % divider
        divider //= 60
    return time_str

def get_times_for_distances(data: str) -> dict:
    distances = {}
    for line in data.splitlines():
        match_total = re.match(r"^Total distance:\t+([^\s]+)", line)
        match_km = re.match(r"^Km (\d+):\t+([^\s]+)\s(.*)$", line)
        if match_total:
            distance = match_total.group(1).replace(",", "")
            distances["total"] = float(distance)
        elif match_km:
            distance, time, is_partial = match_km.groups()
            distance = int(distance)
            if distance > 10: break
            if is_partial:
                if distance <= 5: distances["5"] = -1
                if distance <= 10: distances["10"] = -1
            else:
                seconds = get_seconds_from_human_readable_time(time)
                if "1" not in distances or seconds < distances["1"]: distances["1"] = seconds
                if distance <= 5 and distances.get("5", 0) != -1: distances["5"] = distances.get("5", 0) + seconds
                if distances.get("10", 0) != -1: distances["10"] = distances.get("10", 0) + seconds
    return distances

def main():
    if len(sys.argv) != 2 and len(sys.argv) != 4:
        print("Exec with %s directory min-date max-date" % ( sys.argv[0] ))
        print("Exec with %s directory" % ( sys.argv[0] ))
        print("\n")
        print("Date format: yyyy-mm-dd")
        sys.exit(-1)

    directory = sys.argv[1]
    min_time = get_time_from_human_readable_date(sys.argv[2] if len(sys.argv) == 4 else '1970-01-01')
    max_time = get_time_from_human_readable_date(sys.argv[3] if len(sys.argv) == 4 else '2099-12-31')

    if not os.path.isdir(directory) or not min_time or not max_time or min_time > max_time:
        print("Exec with %s directory min-date max-date" % ( sys.argv[0] ))
        print("Exec with %s directory" % ( sys.argv[0] ))
        print("\n")
        print("Date format: yyyy-mm-dd")
        sys.exit(-1)

    files = os.listdir(directory)
    distances = {}
    count = 0

    files.sort()
    for file in files:
        if file not in (".", ".."):
            match = re.match(r"^(\d{4}-\d{2}-\d{2})_.+_(.+)\.fit$", file)
            if match:
                date, data_type = match.groups()
                if data_type in ("Carrera", "Entrenamiento", "Series"):
                    time = get_time_from_human_readable_date(date)
                    if time and (time >= min_time) and (time <= max_time):
                        output = subprocess.getoutput("python3 %s %s" % ( get_fit_file_summary_data, os.path.join(directory, file) ))
                        if output:
                            partial_distances = get_times_for_distances(output)
                            if "total" in partial_distances:
                                distances["total"] = distances.get("total", 0) + partial_distances["total"]
                                distances["max"] = max(distances.get("max", 0), partial_distances["total"])
                            for k in ("1", "5", "10"):
                                if partial_distances.get(k, 0) != -1 and ((k not in distances) or ((k in partial_distances) and (partial_distances[k] < distances[k]["distance"]))):
                                    distances[k] = { "distance": partial_distances[k], "date": date }
                            count += 1

    print("Distancia total: %.02f Km" % ( distances.get('total', 0) ))
    print("Número de salidas: %d" % ( count ))
    print("Distancia máxima: %.02f Km" % ( distances.get('max', 0) ))
    print("\n")
    for k in ("1", "5", "10"):
        if k in distances:
            print("Tiempo mínimo para %sK: %s (%s)" % ( k, get_human_readable_time(distances[k]['distance']), distances[k]['date'] ))
    print("\n")

if __name__ == "__main__":
    main()
