#!/usr/bin/env python3
from bs4 import BeautifulSoup
import csv
from io import StringIO
from itertools import zip_longest
from os import listdir
from shutil import copyfileobj, make_archive


def fedenczak_find_service_id(text):
    if text.endswith(' E,7') or text.endswith('E7'):
        return 'E7'
    if text.endswith(' E, F'):
        return 'EF'
    # S - dni nauki szkolnej
    # D - pn-pt (oprócz swiąt)
    # E - pn-so
    # 7 - niedziela
    # F - 1 listopada i 24 grudnia
    if text.endswith(('S', 'D', 'E', 'F', ' 7')):
        return text[-1]
    print('- using default service_id D')
    return 'D'


def fedenczak_fix_time(hours, minutes):
    # resko-szczecin: Żerzyno
    if minutes == '353':
        minutes = '53'
    # resko-szczecin: Kikorze
    elif minutes == '539':
        minutes = '39'
    # szkolny-nowogard-maszewo: Bęczno
    elif minutes == '228':
        minutes = '28'
    return f'{hours:>02}', f'{minutes:>02}'


def fix_time(input: str):
    time = input.strip().replace(';', ':').replace(' ', ':').rstrip('SDEF').split(':')
    if '-' in time[0]:
        return None
    hours, minutes = fedenczak_fix_time(time[0], time[1])
    return f'{hours}:{minutes}:00'


with open('fedenczak/gtfs/stops.txt', newline='') as csvfile:
    stop_names_to_id = {row['stop_name']: row['stop_id'] for row in csv.DictReader(csvfile)}
duplicated_stops = {
    'Ostrzyca': '0780156-1',  # MERGING WITH: Ostrzyca skrzyż.
    'Skrzyż. Ostrzyca': '0780156-1',  # TYPO: Ostrzyca skrzyż. (szkolny-nowogard-maszewo)
    'Olchowo': '0780080-1',  # MERGING WITH: Olchowo skrzyż. Kościuszki
    'Kościuszki skrzyż.': '0780080-1',  # MERGING WITH: Olchowo skrzyż. Kościuszki
    'Olchowo skrz. Kościuszki': '0780080-1',  # TYPO: Olchowo skrzyż. Kościuszki (nowogard-golewniow-szczecin)
    'Sąponica': '0780179-1',  # TYPO: Sąpolnica (szkolny-nowogard-maszewo)
    'Bodzięcin': '0780423-1',  # TYPO: Bodzęcin (resko-szczecin)
    'Dalno skrz.': '0778432-1',  # TYPO: Dalno skrzyż. (adowo-wielkie-lobez)
    'Stodólsko': '0779093-1',  # TYPO: Stodólsko (szkolny-nowogard-maszewo)
    'Leszczynka': '0779101-1',  # MERGING WITH: Leszczynka skrzyż. (Leszczynka)
    'Strzemiele': '0782340-1',  # TYPO: Strzmiele (radowo-wiekie-nowogard)
    'Starogard-Kolonia': '0782793-1',  # TYPO: Starogard - Kolonia (lobez-gryfice)
    'Goleniów ul. Szkolna NETTO': '0978929-1',
    'Goleniów (NETTO)': '0978929-1',
    'Goleniów (szkolna)': '0978929-1',  # MERGING WITH: Goleniów ul. Szkolna (NETTO) (goleniow-goleczewo)
    'Maszewo': '0979188-1',  # MERGING WITH: Maszewo ul. Nowogardzka (szkolny-nowogard-maszewo)
    'Goleniów ul . Dworzec PKS': '0978929-2',
    'Goleniów-Dworzec PKS': '0978929-2',
    'Goleniów ul. Szkolna GARAŻE': '0978929-3',
    'Goleniów ul. Szkolna garaże': '0978929-3',
    'Goleniów GARAŻE': '0978929-3',
    'Goleniów Armii Krajowej': '0978929-4',
    'Gryfice ul. Nieorska (szpital)': '0979053-2',
    'Nowogard ul. Rzeszowskiego p': '0979389-02',  # TYPO: Nowogard ul. Rzeszowskiego
    'Stargard Gdańska': '0979596-2',  # TYPO: Stargard ul. Gdańska
    # komunikacja-miejska:
    'Dworzec PKS': '0979389-02',  # MERGING WITH: Nowogard ul. Rzeszowskiego
    'ul.Bema 9': '0979389-10',  # TYPO
    'ul.Kościuszki 36': '0979389-17',  # TYPO
    'ul.Armii Krajowej 17': '0979389-18',  # TYPO
    'ul.Armii Krajowej 29': '0979389-19',  # TYPO
    'ul.Armii Krajowej 46': '0979389-20',  # TYPO
    'ul.Wojska Polskiego 4': '0979389-21',  # TYPO
    'ul.Romualda Traugutta': '0979389-22',  # TYPO
    'ul.Kościelna': '0979389-25',  # TYPO
    # skipuje te przystanki. nie mam jak zmatchować do tripów, bo mają tylko część
    'ul. 3 Maja': None,
    'ul. Poniatowskiego': None,
    'ul. Boh. Warszawy "ZS ORLIK"': None,
}
stop_names_to_id.update(duplicated_stops)

routes_fp = StringIO()
routes_csv = csv.writer(routes_fp)
routes_csv.writerow(['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_url', 'route_color', 'route_text_color'])
trips_fp = StringIO()
trips_csv = csv.writer(trips_fp)
trips_csv.writerow(['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id'])
stop_times_fp = StringIO()
stop_times_csv = csv.writer(stop_times_fp)
stop_times_csv.writerow(['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])

for route_id in sorted(listdir('fedenczak/html')):
    print(route_id)
    with open('fedenczak/html/' + route_id) as fp:
        soup = BeautifulSoup(fp, 'lxml')
    content = soup.select_one('section')

    if route_id == 'komunikacja-miejska':
        trip_names = [x.get_text().strip().title().replace('\n', '') for x in content.select('h2')]
    else:
        trip_names = [x.get_text().strip().title().replace('\n', '') for x in content.select('.u-text-1, .u-text-3')]
    for direction_id, (trip, trip_name) in enumerate(zip(content.select('.wpsm_panel-group'), trip_names, strict=True)):
        stops_departures = []
        stop_ids = []
        service_ids = []
        for panel in trip.select('.wpsm_panel'):
            stop_name = panel.select_one('h4').get_text().strip()
            if len(stop_name.strip('-')) == 0:
                continue
            stop_id = stop_names_to_id[stop_name]
            if stop_id is None:
                continue
            stop_times = [fix_time(x.get_text()) for x in panel.select('li')]
            if len(service_ids) == 0:
                service_ids = [fedenczak_find_service_id(x.get_text()) for x in panel.select('li')]
            else:
                assert len(service_ids) == len(panel.select('li'))
            stops_departures.append(stop_times)
            stop_ids.append(stop_id)

        # Transpose, https://stackoverflow.com/a/6473724
        trips = list(map(list, zip_longest(*stops_departures, fillvalue=None)))

        # Remove duplicated trips.
        if route_id == 'nowogard-golenow-szczecin':
            for i, x in enumerate(service_ids):
                # Contained in 'resko-szczecin'
                if (x == 'E' and trips[i][0] in ['08:00:00', '13:35:00']) or (x == 'E7' and trips[i][0] == '16:15:00'):
                    del trips[i]
                    del service_ids[i]

        for trip_seq, (trip, service_id) in enumerate(zip(trips, service_ids, strict=True)):
            trip_id = f'{route_id}-{direction_id}-{trip_seq}'

            # stop_times.txt
            for stop_seq, (stop_id, stop_time) in enumerate(zip(stop_ids, trip, strict=True)):
                if stop_time is not None:
                    stop_times_csv.writerow([trip_id, stop_time, stop_time, stop_id, stop_seq])

            # trips.txt
            if route_id == 'komunikacja-miejska':
                # one's ascii, the other's en dash
                headsign = trip_name.rsplit(' -> ', 1)[-1].rsplit(' –> ', 1)[-1]
                real_route_id = route_id + str(direction_id // 2)
                real_direction_id = direction_id % 2
                trips_csv.writerow([real_route_id, service_id, trip_id, headsign, real_direction_id])
            else:
                headsign = trip_name.rsplit(' - ', 1)[-1].rsplit('-', 1)[-1]
                trips_csv.writerow([route_id, service_id, trip_id, headsign, direction_id])

        # routes.txt (komunikacja-miejska)
        if route_id == 'komunikacja-miejska' and (direction_id % 2) == 0:
            real_route_id = route_id + str(direction_id // 2)
            routes_csv.writerow([real_route_id, 'Fedenczak', 'Fedeńczak', trip_name, 3, f'https://fedenczak.com.pl/{route_id}/', 'F4E21A', '000000'])

    # routes.txt
    if route_id != 'komunikacja-miejska':
        routes_csv.writerow([route_id, 'Fedenczak', 'Fedeńczak', trip_names[0], 3, f'https://fedenczak.com.pl/{route_id}/', 'F4E21A', '000000'])

for infp, outname in [(routes_fp, 'routes.txt'), (trips_fp, 'trips.txt'), (stop_times_fp, 'stop_times.txt')]:
    with open('fedenczak/gtfs/' + outname, 'w') as fd:
        infp.seek(0)
        copyfileobj(infp, fd)

make_archive('out/fedenczak', 'zip', 'fedenczak/gtfs')
