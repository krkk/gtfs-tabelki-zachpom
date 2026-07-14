#!/usr/bin/env python3
import csv
from io import StringIO
from shutil import copyfileobj, make_archive
import json

"""
Zdobywanie danych:
1. Wejdz na https://www.styl-bus.com.pl/rozklad-jazdy/
2. Dodaj brakepointa gdzieś z `this.scheduleService.getLine`
3. Poklikaj aż brakea zdobędziesz
4. ```js
   [...Array(6).keys()].map(n => {
     const line = 1 + (n/2)|0;
     const direction = n%2 ? 'TAM' : 'POW';
     return this.scheduleService.getLine(line.toString(), direction)
   });
   ```
5. `jq 'def chunk(n): range(length/n|ceil) as $i | .[n*$i:n*$i+n]; map( map([ .name, .value[] ]) | transpose ) | chunk(2)' data.json > stop_times.json`
6. Ręcznie znajdź setActiveLineNumber i zrób z tego route_names poniżej
"""
route_names = [
    ('stargard-nowa-dabrowa', 'Nowa Dąbrowa - Krzywnica - Chlebowo - Białuń - Tolcz - Stara Dąbrowa - Stargard'),
    ('stargard-chlebowo', 'Chlebowo - Krzywnica - Nowa Dąbrowa - Stara Dąbrowa - Stargard'),
    ('stargard-maszewo', 'Maszewo - Parlino - Łęczyca - Załęcze - Storkówko - Moskorze - Stargard'),
]


def stylbus_get_service_id(text):
    return text[-1]


def fix_time(input: str):
    time = input.strip().rstrip('DE').split(':')
    if '-' in time[0]:
        return None
    return f'{time[0]:>02}:{time[1]:>02}:00'


with open('stylbus/gtfs/stops.txt', newline='') as csvfile:
    stop_names_to_id = {row['stop_name']: row['stop_id'] for row in csv.DictReader(csvfile)}
duplicated_stops = {
    'Stara Dąbrowa skrż': '0783054-1',  # TYPO: Stara Dąbrowa skrż.
    'Grabowo Piaszcze nż.': '0783350-1',  # TYPO: Grabowo Piaszcze nż
    'Kicko skrz.': '0782942-2',  # TYPO: Kicko skrzyż.
    'Parlino nż.': '0783025-1',  # MERGING WITH: Parlino (raczej niepoprawne bo na rozkładzie jest normalnie jeden po drugim)
}
stop_names_to_id.update(duplicated_stops)

routes_fp = StringIO()
routes_csv = csv.writer(routes_fp)
routes_csv.writerow(['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url'])
trips_fp = StringIO()
trips_csv = csv.writer(trips_fp)
trips_csv.writerow(['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id'])
stop_times_fp = StringIO()
stop_times_csv = csv.writer(stop_times_fp)
stop_times_csv.writerow(['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'pickup_type', 'drop_off_type'])

with open('stylbus/stop_times.json') as f:
    routes = json.load(f)
for route, (route_id, route_long_name) in zip(routes, route_names, strict=True):
    print(route_id)
    for direction_id, trips in enumerate(route):
        stop_names = trips.pop(0)
        stop_ids = [stop_names_to_id[x] for x in stop_names]
        stop_pickup_types = ['3' if x.endswith((' nż.', ' nż')) else '' for x in stop_names]

        for trip_seq, trip in enumerate(trips):
            trip_id = f'{route_id}-{direction_id}-{trip_seq}'

            # stop_times.txt
            for stop_seq, (stop_id, stop_pickup_type, stop_time) in enumerate(zip(stop_ids, stop_pickup_types, trip, strict=True)):
                stop_time = fix_time(stop_time)
                if stop_time is not None:
                    stop_times_csv.writerow([trip_id, stop_time, stop_time, stop_id, stop_seq, stop_pickup_type, stop_pickup_type])

            # trips.txt
            service_id = next(stylbus_get_service_id(x) for x in trip if stylbus_get_service_id(x) != '-')
            headsign = stop_names[-1]
            trips_csv.writerow([route_id, service_id, trip_id, headsign, direction_id])

    # routes.txt
    routes_csv.writerow([route_id, 'Styl-bus', 'Styl-bus', route_long_name, 3, 'https://www.styl-bus.com.pl/rozklad-jazdy/{route_id}/'])

for infp, outname in [(routes_fp, 'routes.txt'), (trips_fp, 'trips.txt'), (stop_times_fp, 'stop_times.txt')]:
    with open('stylbus/gtfs/' + outname, 'w') as fd:
        infp.seek(0)
        copyfileobj(infp, fd)

make_archive('out/stylbus', 'zip', 'stylbus/gtfs')
