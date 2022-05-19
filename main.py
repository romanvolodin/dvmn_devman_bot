from time import sleep

import requests
from environs import Env
from telegram import Bot


def format_message(response):
    message_template = "Проверили работу «{title}».\n{result}\n{url}"
    messages = []

    for attempt in response["new_attempts"]:
        if attempt["is_negative"]:
            result = "Всё круто, но надо кое-чего поправить =)"
        else:
            result = "Работа принята, можно переходить к следующему уроку!"

        message = message_template.format(
            title=attempt["lesson_title"],
            result=result,
            url=attempt["lesson_url"],
        )

        messages.append(message)

    return "\n\n".join(messages)


def main():
    env = Env()
    env.read_env()

    dvmn_token = env.str("DVMN_TOKEN")
    tg_bot_token = env.str("TG_BOT_TOKEN")
    tg_chat_id = env.str("TG_CHAT_ID")

    polling_timeout_sec = 60
    connection_error_sleep_sec = 5

    bot = Bot(token=tg_bot_token)

    url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {dvmn_token}"}
    params = {}

    while True:
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=polling_timeout_sec,
            )
            response.raise_for_status()
            review_result = response.json()

            if review_result["status"] == "timeout":
                params["timestamp"] = review_result["timestamp_to_request"]
                continue

            params["timestamp"] = review_result["last_attempt_timestamp"]
            bot.send_message(tg_chat_id, format_message(review_result))
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            print("No Internet connection")
            sleep(connection_error_sleep_sec)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
