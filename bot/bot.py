#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

import argparse
import json
import os
import requests
import time
import random
from private import *


HEADERS = {
    'content-type': 'application/json'
}

USERS_JSON = os.path.join('..', 'users.json')

BTC_SIGN = 'BTC'


def _get_endpoint(token):
    return f'https://api.telegram.org/bot{token}'


def _get_users_from_json(json_filename):
    with open(json_filename, 'r', encoding='utf-8') as file:
        return json.load(file)


def _add_new_users(token, usd):
    user_settings = {
        "currency": {
            "USD": usd
        },
        "threshold": {
            "USD": args.diff_threshold
        }
    }
    users_from_chats = _get_users_from_chats(token)
    users_from_json = _get_users_from_json(USERS_JSON)
    for key in users_from_chats:
        if key not in users_from_json:
            users_from_chats[key].update({'settings': user_settings})
            users_from_json.update({key: users_from_chats[key]})
            print(f'{time.ctime()} new user added ')
            _write_to_json(users_from_json)
    return users_from_json


def _write_to_json(users_from_json):
    with open(USERS_JSON, 'w', encoding='utf-8') as file:
        json.dump(users_from_json, file, indent=2, ensure_ascii=False)
        print(f'{time.ctime()} * Updated data on users, make changes to users.json')


def _get_users_from_chats(token):
    user_data = dict()
    ret = requests.get(_get_endpoint(token) + '/getUpdates', proxies=proxies)
    if ret.status_code == 200:
        data = json.loads(ret.content)
        if data['ok']:
            messages = data['result']
            for message in messages:
                if 'message' in message:
                    x = message['message']['chat']['id']
                    y = message['message']['from']
                    z = dict()
                    for key, value in y.items():
                        if key != 'id':
                            z.update({key: value})
                    user_data[str(x)] = {'user': z}
        else:
            print(f'{time.ctime()} Error - not Ok')
    else:
        print(f'{time.ctime()} Error status_code !=200')
    return user_data


def _send_message(token, chat_id, message):
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    requests.post(_get_endpoint(token) + '/sendMessage', headers=HEADERS, data=json.dumps(data), proxies=proxies)
    print(f'{time.ctime()} {message}')


def _get_bot_updates(token, offset=None, timeout=30):
    params = {'offset': offset, 'timeout': timeout}
    ret = requests.get(_get_endpoint(token) + '/getUpdates', params, proxies=proxies)
    if ret.status_code == 200:
        data = json.loads(ret.content)
        if data['ok']:
            messages = data['result']
            return messages
        else:
            print(f'{time.ctime()} Error - not Ok')
    else:
        print(f'{time.ctime()} Error status_code !=200')
    messages = []
    return messages


def _get_current_exchange_rate(btc_rate):
    response = requests.get('https://blockchain.info/ticker')
    data = json.loads(response.content)
    for key in btc_rate:
        btc_rate[key][0] = round(data[key]['last'], 2)
    return btc_rate


def _split_threshold(thres_dict):
    thres_cur = list(thres_dict)[0]
    thres_val = thres_dict[thres_cur]
    return(thres_cur, thres_val)


def _calculate_difference_rates(btc_rate, token):
    # print(f'{time.ctime()} run _calculate_difference_rates')
    users_from_json = _get_users_from_json(USERS_JSON)
    for key in users_from_json:
        diff_cur = {}
        if key == '125702814':
            message = f'{random.choice(koteyka)}, текущий курс: \n'
        else:
            message = ''
        prev_value_dict = users_from_json[key]['settings']['currency']
        for cur in prev_value_dict:
            diff = round(btc_rate[cur][0] - prev_value_dict[cur], 2)
            diff_cur.update({cur: diff})

        thres_cur, thres_val = _split_threshold(users_from_json[key]['settings']['threshold'])

        if abs(diff_cur[thres_cur]) > thres_val:
            for cur in diff_cur:
                if diff_cur[cur] > 0.0:
                    arrow_sign = '\u25B2'
                else:
                    arrow_sign = '\u25BC'
                cur_sign = btc_rate[cur][2]
                cur_val = f'{btc_rate[cur][0]:,.0f} {cur_sign}'
                message += f'`1 {BTC_SIGN} = {cur_val.ljust(15)}{arrow_sign} {diff_cur[cur]:,.0f} {cur_sign}\n`'
            _send_message(token, key, message)
            # update current value in json
            for cur in diff_cur:
                users_from_json[key]['settings']['currency'][cur] = btc_rate[cur][0]
            _write_to_json(users_from_json)
        else:
            pass
            # print(f'{time.ctime()} {key}: very small difference: {diff_cur[thres_cur]}, threshold = {thres_val}')


def main(token, poll_freq):

    def _currentvalue():
        answer = ''
        for currency in list_of_currency:
            answer += f'`1 {BTC_SIGN} = {btc_rate[currency][0]:,.0f} {btc_rate[currency][2]} `\n'
        return answer

    def _setthreshold():
        answer = 'Установи валюту для отслеживания и порог срабатывания оповещения. Например:' \
                 ' *usd 100*, \nЛибо просто введи число, если хочешь изменить значение текущего порога'
        wait_parameter.update({last_chat_id: last_chat_text})
        return answer

    def _addcurrency():
        answer = f'Выбери дополнительную валюту:'
        for key in btc_rate.keys():
            if key not in list_of_currency:
                answer += f'`\n {key} - {btc_rate[key][1]}`'
        wait_parameter.update({last_chat_id: last_chat_text})
        return answer

    def _deletecurrency():
        if len(list_of_currency) > 1:
            answer = f'Выбери валюту, которую следует исключить:'
            for key in list_of_currency:
                answer += f'`\n {key} - {btc_rate[key][1]}`'
            wait_parameter.update({last_chat_id: last_chat_text})
        else:
            answer = f'Удалить единственную валюту? Серьёзно? И что я буду отслеживать? ' \
                     f'Может тогда просто отписаться от меня?'
        return answer

    def _help():
        answer = 'Пока не прикрутили :('
        return answer


    commands = {
        "/currentvalue": _currentvalue,
        "/setthreshold": _setthreshold,
        "/addcurrency": _addcurrency,
        "/deletecurrency": _deletecurrency,
        "/help": _help
    }

    print(f'{time.ctime()} Run, Forrest, Run!!!')
    new_offset = None
    wait_parameter = {}
    timestamp = time.time() - poll_freq
    btc_rate = {
        "USD": [0, 'Американский доллар', 'USD'],
        "EUR": [0, 'Евро', 'EUR'],
        "RUB": [0, 'Российский рубль', 'RUB'],
        "JPY": [0, 'Японская иена', 'JPY'],
        "GBP": [0, 'Фунт стерлингов', 'GBP'],
        "AUD": [0, 'Австралийский доллар', 'AUD'],
        "BRL": [0, 'Бразильский реал', 'BRL'],
        "CAD": [0, 'Канадский доллар', 'CAD'],
        "CHF": [0, 'Швейцарский франк', 'CHF'],
        "CLP": [0, 'Чилийское песо', 'CLP'],
        "CNY": [0, 'Юань', 'CNY'],
        "DKK": [0, 'Датская крона', 'DKK'],
        "HKD": [0, 'Гонконгский доллар', 'HKD']
    }

    btc_rate = _get_current_exchange_rate(btc_rate)
    _calculate_difference_rates(btc_rate, token)

    while True:
        messages = _get_bot_updates(token, new_offset)
        users_from_json = _add_new_users(token, btc_rate["USD"][0])

        for message in messages:
            last_update_id = message['update_id']
            if 'message' in message:
                if 'text' not in message['message']:
                    last_chat_text = '#sticker#'
                else:
                    last_chat_text = message['message']['text']
                last_chat_id = message['message']['chat']['id']
                last_chat_name = message['message']['chat']['first_name']
                last_msg_date = time.ctime(message['message']['date'])
                print(f'{last_msg_date} {last_chat_name}: {last_chat_text}')

                list_of_currency = users_from_json[str(last_chat_id)]['settings']['currency'].keys()
                thres_cur, thres_val = _split_threshold(users_from_json[str(last_chat_id)]['settings']['threshold'])

                # recognize setting
                if wait_parameter.get(last_chat_id):
                    print(f'is this setting! {wait_parameter[last_chat_id]}')

                    if wait_parameter[last_chat_id] == '/setthreshold':
                        # check, in this chat want to set a threshold?
                        input_line = last_chat_text.split()
                        if not input_line[0].isdigit():
                            # check <ISO_CURRENCY_CODE>
                            if input_line[0].upper() not in list_of_currency:
                                answer = f'В твоем перечне нет валюты *{input_line[0]}*. Вот список подключенных валют:'
                                for key in list_of_currency:
                                    answer += f'`\n {key} - {btc_rate[key][1]}`'
                                answer += f'\nПовтори команду /setthreshold и введи корректные значения'
                            else:
                                # check  <threshold>
                                if len(input_line) > 1 and input_line[1].isdigit():
                                    new_currency = input_line[0].upper()
                                    new_threshold = int(input_line[1])
                                    users_from_json[str(last_chat_id)]['settings']['threshold'].clear()
                                    users_from_json[str(last_chat_id)]['settings']['threshold'].update(\
                                        {new_currency: new_threshold})
                                    _write_to_json(users_from_json)
                                    print('base currency & threshold update')
                                    answer = 'Принято. Новые значения: \n'
                                    answer += f'Валюта - {new_currency}, ' \
                                              f'порог - {new_threshold} {btc_rate[new_currency][2]}'
                                else:
                                    answer = 'Порог должен быть целым положительным числом!'
                                    answer += f'\nПовтори команду /setthreshold и введи корректные значения'
                        else:
                            # update only value
                            new_threshold = int(input_line[0])
                            users_from_json[str(last_chat_id)]['settings']['threshold'][thres_cur] = new_threshold
                            _write_to_json(users_from_json)
                            print('threshold update')
                            answer = f'Принято. Новый порог: *{new_threshold} {btc_rate[thres_cur][2]}*'

                    if wait_parameter[last_chat_id] == '/addcurrency':
                        # check <ISO_CURRENCY_CODE>
                        if last_chat_text.upper() not in btc_rate:
                            answer = f'Я не знаю такой валюты *{last_chat_text.upper()}*. Вот список поддерживаемых ' \
                                     f'валют:'
                            for key in btc_rate.keys():
                                answer += f'`\n {key} - {btc_rate[key][1]}`'
                            answer += f'\nПовтори команду {wait_parameter[last_chat_id]} и введи корректные значения'
                        else:
                            # сделать проверку - есть ли уже эта валюта в списке ? Или просто апдейтить поверх?
                            tmpdic = users_from_json[str(last_chat_id)]['settings']['currency']
                            tmpdic.update({last_chat_text.upper(): btc_rate[last_chat_text.upper()][0]})
                            _write_to_json(users_from_json)
                            answer = f'Добавил *{last_chat_text.upper()}* в твой перечень.'

                    if wait_parameter[last_chat_id] == '/deletecurrency':
                        if last_chat_text.upper() not in list_of_currency:
                            answer = f'В твоём перечне нет валюты *{last_chat_text.upper()}*. Вот список подключенных' \
                                     f' валют:'
                            for key in list_of_currency:
                                answer += f'`\n {key} - {btc_rate[key][1]}`'
                            answer += f'\nПовтори команду /deletecurrency и введи корректные значения'
                        elif thres_cur == last_chat_text.upper():
                            answer = f'Не могу удалить отслеживаемую валюту. Используй комманду /setthreshold ' \
                                     f'для смены валюты:'
                        else:
                            tmpdic = users_from_json[str(last_chat_id)]['settings']['currency']
                            tmpdic.pop(last_chat_text.upper())
                            _write_to_json(users_from_json)
                            answer = f'*{last_chat_text.upper()}* удалена из твоего перечня'

                    _send_message(token, last_chat_id, answer)
                    wait_parameter.pop(last_chat_id)

                # recognize text
                if last_chat_text in commands:
                    answer = commands[last_chat_text]()
                    _send_message(token, last_chat_id, answer)

            new_offset = last_update_id + 1

        if time.time() - timestamp > poll_freq:
            btc_rate = _get_current_exchange_rate(btc_rate)
            _calculate_difference_rates(btc_rate, token)
            timestamp = time.time()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tracking of changes of the cryptocurrency course')
    parser.add_argument('--token', required=True, help='Telegram-bot token')
    parser.add_argument('--poll_freq', type=int, help='poll frequency', default=10)
    parser.add_argument('--diff_threshold', type=int, help='data excahnge rate difference threshold', default=10)

    args = parser.parse_args()

    main(args.token, args.poll_freq)
