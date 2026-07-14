Nieoficjalne rozkłady busów w formacie GTFS, przetworzone z tabelek przewoźników w HTMLu.

Nie spodziewaj się wysokiej jakości:
**lokalizacje przystanków mogą być niepoprawne**, bo zostały wybrane na oko z latania po mapie OSM,
feedy są całkowicie aktualizowane ręczne i tylko gdy sobie o nich przypomne,
nie przygotowałem też metody, by łączyć rozkłady gdy nowy wyjdzie a stary dalej obowiązuje,
oraz `start_date` i `end_date` to cały rok 2026 (pewnie zgubiłem też parę swiąt przy okazji).

Dostępne feedy:
- Dąbek: https://krkk.github.io/gtfs-tabelki-zachpom/dabek.zip
- Fedeńczak: https://krkk.github.io/gtfs-tabelki-zachpom/fedenczak.zip
- Styl-bus: https://krkk.github.io/gtfs-tabelki-zachpom/stylbus.zip
- Transa (gmina Kobylanka): https://krkk.github.io/gtfs-tabelki-zachpom/transa.zip

Generowanie

```shell
$ python3 <dabek|fedenczak|stylbus|transa>/parser.py
```

Licencja CC0 na feedy, MIT na kod.
