import csv

def load_songs(path):
    songs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            songs.append(row)
    return songs
