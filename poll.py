import requests
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from playsound import playsound
from datetime import datetime

#log = open("poll.log", "a")
logger = logging.getLogger(__name__)
loglevel = logging.DEBUG
logger.setLevel(loglevel)
log_file_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s')
log_console_formatter = logging.Formatter('%(message)s')
# Set default log format
if len(logger.handlers) == 0:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
else:
    handler = logger.handlers[0]
    handler.setFormatter(log_console_formatter)

# Max 5 log files each 10 MB.
rotate_handler = RotatingFileHandler(filename='poll.log', maxBytes=10000000,
                                     backupCount=5)
rotate_handler.setFormatter(log_file_formatter)
rotate_handler.setLevel(loglevel)
# Log to Rotating File
logger.addHandler(rotate_handler)

notification_ts = {}
sound_ts = {}

def send_telegram_msg(token, vac_center, free_slots, link):
    chat_ids = get_telegram_chat_ids(token)
    for chat_id in chat_ids:
        params = {"chat_id": chat_id, "text": f"{free_slots} freie Impftermine in {vac_center}: {link}"}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message = requests.post(url, params=params)
        notification_ts[vac_center] = datetime.now()


def get_telegram_chat_ids(token):
    chat_ids = {}
    try:
        answer = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
        content = answer.content
        data = json.loads(content)
        chats = data['result']
        for chat in chats:
            if 'message' in chat:
                chat_id = chat['message']['chat']['id']
                text = chat['message']['text']
                if chat_id is not None:
                    logger.debug(f'Chat ID: {chat_id}')
                    chat_ids[chat_id] = chat_id
    except Exception as e:
        logger.exception("Error in retrieving telegram chat ids", e)
    return chat_ids

def replace_start_date(url, new_start_date):
    index = url.find('start_date=')
    url = url[:index] + 'start_date='+new_start_date + url[index + 21:]
    return url

def date_from_timestamp(timestamp):
    return timestamp[:10]

def get_second_appointment_url(url):
    index = url.find('availabilities.json')
    url = url[:index] + 'second_shot_availabilities.json' + url[index + 19:]
    return url

def check_second_appointment(vac_center, url, first_date, second_date):
    total = 0
    second_date = date_from_timestamp(second_date)
    url = replace_start_date(url, second_date)
    #logger.debug(f'{vac_center} second appoint URL:\t {url}')
    url = get_second_appointment_url(url)
    url = url + '&first_slot='+first_date
    logger.debug(f'{vac_center} second appoint URL:\t {url}')

    res = requests.get(url)
    if res.status_code != 200:
        logger.error("Error: " + vac_center)
        logger.debug(res)
        return total
    logger.debug(f'{vac_center} second appoint:\t {res.text}')
    parsed = json.loads(res.text)
    total = parsed["total"]
    return total

def check_all(endpoints, sound, token):
    try:
        success = False
        for target in endpoints:
            current_date = datetime.today().strftime('%Y-%m-%d')
            vac_center = target["name"]
            link_url = target["link-url"]
            url = target["url"]
            url = replace_start_date(url, current_date)
            res = requests.get(url)
            if res.status_code != 200:
                logger.error("Error: " + vac_center)
                logger.debug(res)
                continue
            logger.debug(vac_center + ":\t" + res.text)
            parsed = json.loads(res.text)
            total = parsed["total"]

            if total == 0 and "next_slot" in parsed:
                next_slot = parsed["next_slot"]
                logger.debug(f'{vac_center}:\t Next Free Slot {next_slot}!')
                url = replace_start_date(url, next_slot)
                try:
                    res = requests.get(url)
                except Exception as ex:
                    logger.exception(f'Error retrieving data for url {url}', ex)
                    continue
                if res.status_code != 200:
                    logger.error("Error: " + vac_center)
                    logger.debug(res)
                    continue
                logger.debug(f'{vac_center} checking slot {next_slot}:\t {res.text}')
                parsed = json.loads(res.text)
                total = parsed["total"]

            if total != 0:
                avails = parsed['availabilities']
                for availability in avails:
                    try:
                        slots = availability['slots']
                        for slot in slots:
                            first_date = slot['start_date']
                            step = slot['steps'][1]
                            second_start_date = step['start_date']
                            second_total = check_second_appointment(vac_center, url, first_date, second_start_date)
                            if second_total > 0:
                                success = True
                                if second_total < total:
                                    logger.info(f'{second_total} freie Impftermine in {vac_center}: {link_url}')
                                else:
                                    logger.info(f'{total} freie Impftermine in {vac_center}: {link_url}')
                                break
                        if success:
                            break
                    except Exception as ex:
                        logger.exception(f'Error checking second appointments:', ex)
                        continue


            #Make sure only every 10 min. Telegram Messages are sent out
            if success and token and total > 0:
                if vac_center in notification_ts:
                    datediff = datetime.now() - notification_ts[vac_center]
                    logger.info(f'{vac_center} Date Diff in sec: {datediff.seconds}')
                    if datediff.seconds >= 600:
                        if success and token and total > 0:
                            send_telegram_msg(token, vac_center, total, link_url)
                else:
                    send_telegram_msg(token, vac_center, total, link_url)

        if success and sound:
            playsound(sound)
    except Exception as e:
        logger.exception(f'Error in checking endpoints', e)

def main():
    try:
        settings_file = open("settings.json", "r")
        settings = json.load(settings_file);
        settings_file.close()

        sound = ""
        telegram_token = None
        if "sound" in settings:
            sound = settings["sound"]
            logger.info("Using alarm sound " + sound)

        if "telegram-token" in settings:
            telegram_token = settings['telegram-token']
            logger.info("Using Telegram Push Notifications!")
        interval = 3
        if "interval" in settings:
            interval = settings["interval"]

        while True:
            check_all(settings["endpoints"], sound, telegram_token)
            time.sleep(interval)
        #log.close()
    except Exception as e:
        logger.error(f'Error in main function {e}')

if __name__ == "__main__":
    main()
