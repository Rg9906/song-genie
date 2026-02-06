import csv

def load_songs(path):
    songs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = {
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"]
            }

            for key in row:
                if key.endswith("_conf"):
                    song[key] = float(row[key])
                elif key not in ["id", "title", "artist"]:
                    song[key] = row[key]

            songs.append(song)

    return songs
