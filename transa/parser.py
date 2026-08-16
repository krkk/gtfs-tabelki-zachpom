#!/usr/bin/env python3
from bs4 import BeautifulSoup
import csv
from io import StringIO
from itertools import zip_longest
from shutil import copyfileobj, make_archive


def fix_time(input: str):
    time = input.strip()
    if '>' in time:
        return None
    hours, minutes = time.replace(';', ':').split(':')
    return f'{hours:>02}:{minutes:>02}:00'


def fix_service_id(name):
    if name == 'D*nz':
        return 'Dnz*'
    if name == 'E*nz 7':
        return 'Enz*7'
    if name == 'E*nz':
        return 'Enz*'
    if name == 'D 6':
        return 'E'
    return name


normalized_stop_names = {
    'Cisewo - Plac zabaw': 'Cisewo - Plac Zabaw',
    'Jęczydół - Na Polanie': 'Jęczydół - Os. Na Polanie',
    'Jęczydół - Os. Na Polania': 'Jęczydół - Os. Na Polanie',
    'Jęczydół -  Świetlica': 'Jęczydół - Świetlica',
    'Miedwiecko -Punkt Przesiadkowy': 'Miedwiecko - Punkt Przesiadkowy',
    'Miedwiecko Punkt Przesiadkowy': 'Miedwiecko - Punkt Przesiadkowy',
    'Morzyczyn - skrzyżowanie Jęczydół': 'Morzyczyn - Skrzyżowanie Jęczydół',
    'Morzyczyn-Os. Południowe': 'Morzyczyn - Os. Południowe',
    'Morzyczyn NETTO': 'Morzyczyn - NETTO',
    'Niedźwiedź - Sportowa': 'Niedźwiedź - ul. Sportowa',
    'Reptowo Punkt Przesiadkowy': 'Reptowo - Punkt Przesiadkowy',
    'Stargard (Lipnik)ul. Lipowa': 'Stargard (Lipnik) Lipowa',
    'Stargard (Lipnik) - Szczecińska': 'Stargard (Lipnik) Szczecińska',
    'Stargard ul. Szczecińska - Pl. Zgody': 'Stargard Szczecińska - Pl. Zgody',
    'Stargardul. Szczecińska - Słoneczna': 'Stargard Szczecińska - Słoneczna',
    'Stargard ul. Szczecińska - Wieniawskiego': 'Stargard Szczecińska - Wieniawskiego',
    'Stargardul. Szczecińska - Wieżowiec': 'Stargard Szczecińska - Wieżowiec',
    'Stargard ZCP Peron 5': 'Stargard ZCP - Peron 5',
    'SzczecinBasen Górniczy': 'Szczecin - Basen Górniczy',
    'Szczecin Kijewo': 'Szczecin - Kijewo',
    'Szczecin Wiosenna': 'Szczecin - Wiosenna',
    'Szczecin -Płonia Most': 'Szczecin - Płonia Most',
    'Szczecin Płonia most': 'Szczecin - Płonia Most',
}

with open('transa/gtfs/stops.txt', newline='') as csvfile:
    stop_names_to_id = {row['stop_name']: row['stop_id'] for row in csv.DictReader(csvfile)}

routes_fp = StringIO()
routes_csv = csv.writer(routes_fp)
routes_csv.writerow(['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'route_text_color'])
trips_fp = StringIO()
trips_csv = csv.writer(trips_fp)
trips_csv.writerow(['route_id', 'service_id', 'trip_id', 'direction_id'])
stop_times_fp = StringIO()
stop_times_csv = csv.writer(stop_times_fp)
stop_times_csv.writerow(['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])


def gen(direction_id, trip):
    if True:
        stops = trip.select('tr')
        if direction_id < 2:
            route_ids = [x.get_text().strip() for x in stops.pop(0)][1:]
        elif direction_id < 4:
            route_id = '346'
        elif direction_id == 4:
            route_id = '348'
        else:
            route_id = '349'
        service_ids = [fix_service_id(x.get_text().strip()) for x in stops.pop(0)][1:]
        stops.pop(0)

        stop_ids = []
        stops_departures = []

        for trip_seq, stop in enumerate(stops):
            departures = [x.get_text() for x in stop.select('td')]
            stop_name = departures.pop(0).strip()
            stop_name = normalized_stop_names.get(stop_name, stop_name)
            stop_id = stop_names_to_id.get(stop_name)
            if stop_id is not None and stop_id[-1] in '01':
                direction = int(direction_id % 2) if direction_id < 4 else int(trip_seq % 2)
                stop_id = stop_id[:-1] + str(direction)
            if stop_id is None:
                print(stop_name, 'ist None')
            if stop_name in ['Reptowo - Zachód', 'Reptowo - Skrzyżowanie Motaniec']: # FIXME
                stop_id = None

            stops_departures.append(list(map(fix_time, departures)))
            stop_ids.append(stop_id)

        # Transpose, https://stackoverflow.com/a/6473724
        trips = list(map(list, zip_longest(*stops_departures, fillvalue=None)))

        for trip_seq, (trip, service_id) in enumerate(zip(trips, service_ids, strict=True)):
            if direction_id < 2:
                route_id = route_ids[trip_seq]
            trip_id = f'{route_id}-{direction_id}-{trip_seq}'

            # stop_times.txt
            for stop_seq, (stop_id, stop_time) in enumerate(zip(stop_ids, trip, strict=True)):
                if stop_time is not None:
                    stop_times_csv.writerow([trip_id, stop_time, stop_time, stop_id, stop_seq])

            # trips.txt
            direction = int(direction_id % 2) if direction_id < 4 else int(trip_seq % 2)
            trips_csv.writerow([route_id, service_id, trip_id, direction])


with open('transa/gmina-kobylanka.html') as fp:
    content = BeautifulSoup(fp, 'lxml').select('table')

for route_id, route in enumerate(content):
    gen(route_id, route)

for infp, outname in [(trips_fp, 'trips.txt'), (stop_times_fp, 'stop_times.txt')]:
    with open('transa/gtfs/' + outname, 'w') as fd:
        infp.seek(0)
        copyfileobj(infp, fd)

make_archive('out/transa', 'zip', 'transa/gtfs')
