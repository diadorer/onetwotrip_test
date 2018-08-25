#!/usr/bin/env python
import json
import random
import sys
import string
import time
from uuid import uuid4

import conf

import redis


PROCESS_MESSAGE_EVENT = 'process_message'
BECOME_GENERATOR_EVENT = 'become_generator_event'


def run(redis_inst):
    current_generator = redis_inst.get('generator')
    if current_generator:
        app_inst = Handler(redis_inst)

    else:
        app_inst = Generator(redis_inst)

    try:
        while True:
            app_inst = app_inst.process_loop()
    except KeyboardInterrupt:
        app_inst.on_keyboard_interrupt()


def process_errors(redis_inst):
    error_item = redis_inst.lpop('errors')
    while error_item:
        print(error_item)
        error_item = redis_inst.lpop('errors')


class Generator:

    def __init__(self, redis_inst):
        self.redis_inst = redis_inst

        redis_inst.set('generator', '1')

    def process_loop(self):
        self.send_text_message()
        time.sleep(0.5)

        return self

    @staticmethod
    def get_message_text():
        return ''.join([random.choice(string.ascii_letters)
                        for _ in range(random.randint(1, 88))])

    def send_text_message(self):
        message_text = self.get_message_text()
        message_to = self.redis_inst.srandmember('handlers')

        if not message_to:
            print('А сообщение то отправлять и некому, будем ждать...')

        else:
            self.redis_inst.publish(f'message_for_{message_to}', json.dumps({
                'event': PROCESS_MESSAGE_EVENT,
                'message': message_text
            }))

    def switch_to_other(self):
        print('Переключаем генератор')

        new_generator = self.redis_inst.spop('handlers')
        if not new_generator:
            print('Это было последнее приложение, теперь всему конец')
            self.destroy()
            return

        self.redis_inst.publish(f'message_for_{new_generator}', json.dumps({
            'event': BECOME_GENERATOR_EVENT
        }))

    def on_keyboard_interrupt(self):
        self.switch_to_other()

    def destroy(self):
        self.redis_inst.delete('generator')


class Handler:

    def __init__(self, redis_inst):
        self.name = str(uuid4())
        self.redis_inst = redis_inst

        redis_inst.sadd('handlers', self.name)

        self.pub_sub = redis_inst.pubsub()
        self.pub_sub.subscribe(f'message_for_{self.name}')

    def process_loop(self):
        message = self.pub_sub.get_message()
        if message and message['type'] == 'message':
            generator = self.process_message(message['data'])
            if generator:
                return generator

        return self

    def become_generator(self):
        self.destroy()

        print(f'Я становлюсь генератором')

        return Generator(self.redis_inst)

    def process_message(self, message):
        message = json.loads(message)
        if message['event'] == PROCESS_MESSAGE_EVENT:
            print(f'Сообщение {message["message"]}')

            if random.randint(0, 19) == 0:
                self.redis_inst.rpush('errors', message["message"])

        elif message['event'] == BECOME_GENERATOR_EVENT:
            return self.become_generator()

        else:
            print(f'А я не знаю события {message["event"]}')

    def destroy(self):
        self.redis_inst.srem('handlers', self.name)

    def on_keyboard_interrupt(self):
        self.destroy()


if __name__ == '__main__':
    redis_instance = redis.StrictRedis(**conf.REDIS)

    if len(sys.argv) > 1:
        if len(sys.argv) == 2 and sys.argv[1] == 'getErrors':
            process_errors(redis_instance)

        elif {'-h', '--help'}.intersection(sys.argv):
            print('\nЗапускает приложение, которое может быть как герератором так и обработчиком.'
                  '\n\nВспомогательные подкоманды:'
                  '\n\n    getErrors: выводит все сообщения с ошибками и удаляет их из redis.')

        else:
            print('Таких аргументов мы не знаем:(')

    else:
        run(redis_instance)


