import shutil
from zipfile import ZipFile
from markdownify import markdownify
from pytz import timezone
from datetime import datetime
import glob
import uuid
import json
import os
print(f"Current working directory: {os.getcwd()}")


def getuuid():
    uu = str(uuid.uuid4())
    return uu.replace("-", "").upper()


def convert_unixtime(unixtime, timezone_str):
    date = datetime.fromtimestamp(unixtime / 1000)
    try:
        # Attempt to localize the date with the provided timezone string
        date = timezone(timezone_str).localize(date)
    except Exception as e:
        print(f"Error with timezone '{timezone_str}': {e}")
        # Fallback to a default timezone if there's an error (e.g., timezone string is empty or not recognized)
        default_timezone_str = 'UTC'
        print(f"Using default timezone: {default_timezone_str}")
        date = timezone(default_timezone_str).localize(date)

    return date.astimezone(timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


# def convert_unixtime(unixtime, timezone_str):
    # date = datetime.fromtimestamp(unixtime / 1000)
    # date = timezone(timezone_str).localize(date)
    # return date.astimezone(timezone("UTC")).strftime#("%Y-%m-%dT%H:%M:%SZ")


def convert_photo(name, i):
    md5, type = os.path.splitext(name)
    type = type[1:] if len(type) else type
    return {
        "orderInEntry": i,
        "identifier": getuuid(),
        "type": type,
        "isSketch": False,
        "creationDevice": "Joe's MacBook Pro",
        "md5": md5,
    }


def journeyjson2dayonejson(journey):
    dayone = {
        "creationOSName": "macOS",
        "creationOSVersion": "10.15.7",
        "creationDevice": "Joe's MacBook Pro",
        "creationDeviceType": "MacBook Pro",
        "creationDate": convert_unixtime(journey["date_journal"], journey["timezone"]),
        "timeZone": journey["timezone"],
        "starred": False,
        "uuid": getuuid(),
        "text": markdownify(journey["text"], strip=["div"]).strip().replace("\\n\\n", "\\n").replace("\\n  \\n", "\\n"),
    }

    if abs(journey["lat"]) < 90:
        dayone["location"] = {
            "longitude": journey["lon"],
            "latitude": journey["lat"],
            "placeName": journey["address"].strip(),
        }

    if journey["weather"]["degree_c"] < 100:
        dayone["weather"] = {
            "temperatureCelsius": journey["weather"]["degree_c"],
            "conditionsDescription": journey["weather"]["description"],
        }

    if journey["tags"]:
        dayone["tags"] = journey["tags"]

    if journey["photos"]:
        i = 0
        dayone["photos"] = []
        for f in journey["photos"]:
            dayone["photos"].append(convert_photo(f, i))
            i += 1

    return dayone


if os.path.exists("./dayone"):
    shutil.rmtree("./dayone")

os.makedirs("dayone/photos")

entries = []
json_files = glob.glob("./journey/*.json")
print(f"Found {len(json_files)} json files in './journey' directory.")
for f in glob.glob("./journey/*.json"):
    with open(f, "r") as fh:
        journey = json.load(fh)

    dayone = journeyjson2dayonejson(journey)

    if journey["photos"]:
        for (p, j) in zip(dayone["photos"], journey["photos"]):
            source = "./journey/" + str(j)
            target = "./dayone/photos/" + str(j)
            print(f"Copying photo from {source} to {target}")
            shutil.copyfile(source, target)

            dayone["text"] = dayone["text"] + \
                "\n![](dayone-moment://{})".format(p["identifier"])
    entries.append(dayone)

print(f"Total entries processed: {len(entries)}")
dayone_json = {"metadata": {"version": "1.0"}, "entries": entries}

with open("./dayone/Journey.json", "w") as fh:
    fh.write(json.dumps(dayone_json, indent=4,
             separators=(",", ": ")).replace("/", r"\/"))

if os.path.exists("dayone.zip"):
    os.remove("dayone.zip")

shutil.make_archive("dayone", "zip", "./dayone")
print("dayone.zip created successfully.")
