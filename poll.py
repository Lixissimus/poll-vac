import requests
import json
import time
from playsound import playsound

log = open("poll.log", "a")

def check_all(endpoints, sound):
    success = False
    for target in endpoints:
        res = requests.get(target["url"])
        if res.status_code != 200:
            print("Error: " + target["name"])
            print(res)
            continue
        log.write(target["name"] + ":\t" + res.text + "\n")
        log.flush()
        parsed = json.loads(res.text)

        if parsed["total"] != 0:
            success = True
            print("\nAppointments at " + target["name"])
            print(parsed)
        else:
            print(".", end="", flush=True)

    if success and sound:
        playsound(sound)

def main():
    settings_file = open("settings.json", "r")
    settings = json.load(settings_file);
    settings_file.close()

    sound = ""
    if "sound" in settings:
        sound = settings["sound"]
        print("Using alarm sound " + sound)

    interval = 3
    if "interval" in settings:
        interval = settings["interval"]

    while True:
        check_all(settings["endpoints"], sound)
        time.sleep(interval)
    log.close()

if __name__ == "__main__":
    main()
