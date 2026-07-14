#!/usr/bin/env python3
from bs4 import BeautifulSoup
import csv
from io import StringIO
from itertools import batched, zip_longest
from shutil import copyfileobj, make_archive


def fix_time(input: str):
    time = input.strip()
    if len(time) == 0 or time in ['x', 'X']:
        return None
    hours, minutes = time.replace('.', ':').split(':')
    return f'{hours:>02}:{minutes:>02}:00'


routes_fp = StringIO()
routes_csv = csv.writer(routes_fp)
routes_csv.writerow(['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'route_text_color'])
trips_fp = StringIO()
trips_csv = csv.writer(trips_fp)
trips_csv.writerow(['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id'])
stop_times_fp = StringIO()
stop_times_csv = csv.writer(stop_times_fp)
stop_times_csv.writerow(['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])

with open('dabek/gtfs/stops.txt', newline='') as csvfile:
    stop_names_to_id = {row['stop_name']: row['stop_id'] for row in csv.DictReader(csvfile)}
duplicated_stops = {
    'Krapiel': '0783440-1',  # TYPO: Krąpiel
    'Sadłowo WIEŚ': '0784020-1',  # MERGING WITH: Sadłowo
}
stop_names_to_id.update(duplicated_stops)

with open('dabek/dabek.html') as fp:
    content = BeautifulSoup(fp, 'lxml').select_one('.page-content')
trip_variant_tables = content.select('table')
trip_variant_names = (x.get_text() for x in content.select('strong'))
for route_id, route in enumerate(list(batched(zip(trip_variant_tables, trip_variant_names), 2))):
    for direction_id, (trip, trip_name) in enumerate(route):
        print(trip_name)
        stop_ids = []
        stops_departures = []

        stops = trip.select('tr')
        service_ids = [x.get_text().strip() for x in stops.pop(0)][1:]
        for stop in stops:
            departures = [x.get_text() for x in stop.select('td')]
            stop_name = departures.pop(0).strip()

            stops_departures.append(list(map(fix_time, departures)))
            stop_ids.append(stop_names_to_id[stop_name])

        # Transpose, https://stackoverflow.com/a/6473724
        trips = list(map(list, zip_longest(*stops_departures, fillvalue=None)))

        for trip_seq, (trip, service_id) in enumerate(zip(trips, service_ids, strict=True)):
            trip_id = f'{route_id}-{direction_id}-{trip_seq}'

            # stop_times.txt
            for stop_seq, (stop_id, stop_time) in enumerate(zip(stop_ids, trip, strict=True)):
                if stop_time is not None:
                    stop_times_csv.writerow([trip_id, stop_time, stop_time, stop_id, stop_seq])

            # trips.txt
            headsign = trip_name.rsplit('-', 1)[-1].rsplit('–', 1)[-1].title()
            trips_csv.writerow([route_id, service_id, trip_id, headsign, direction_id])

    # routes.txt
    routes_csv.writerow([route_id, 'Dabek', 'Dąbek', route[0][1], 3, 'http://autobusy-dabek.pl/rozklad-jazdy/', 'A1121B', 'FFFFFF'])

for infp, outname in [(routes_fp, 'routes.txt'), (trips_fp, 'trips.txt'), (stop_times_fp, 'stop_times.txt')]:
    with open('dabek/gtfs/' + outname, 'w') as fd:
        infp.seek(0)
        copyfileobj(infp, fd)

make_archive('out/dabek', 'zip', 'dabek/gtfs')
