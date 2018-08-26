#!/usr/bin/env python
import datetime
import random
import sys
import string
import time
from uuid import uuid4

import conf

import redis


def run(redis_inst):
    app_inst = Handler(redis_inst)

    while True:
        app_inst = app_inst.process_loop()


class Generator:

    def __init__(self, redis_inst):
        self.redis_inst = redis_inst

        self.pub_sub = redis_inst.pubsub()
        self.pub_sub.subscribe('generator')

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
        message_to = self.redis_inst.pubsub_channels('message_for*')

        if not message_to:
            print('А сообщение то отправлять и некому, будем ждать...')

        else:
            message_to = random.choice(message_to)
            self.redis_inst.publish(message_to, message_text)


class Handler:

    def __init__(self, redis_inst):
        self.redis_inst = redis_inst

        self.pub_sub = redis_inst.pubsub()
        self.pub_sub.subscribe(f'message_for_{uuid4()}')

    def check_generator(self):
        if self.redis_inst.incr('checking_generator_lock') == 1:
            generator = None
            if not self.redis_inst.pubsub_channels('generator'):
                generator = self.become_generator()

            self.redis_inst.expire('checking_generator_lock', datetime.timedelta(milliseconds=100))
            return generator

    def process_loop(self):
        new_generator = self.check_generator()
        if new_generator:
            return new_generator

        message = self.pub_sub.get_message()
        if message and message['type'] == 'message':
            self.process_message(message['data'])

        time.sleep(0.02)
        return self

    def become_generator(self):
        print(f'Превращаюсь в генератор')
        self.destroy()

        return Generator(self.redis_inst)

    def process_message(self, message):
        print(f'Получил {message}')

        if random.randint(0, 19) == 0:
            self.redis_inst.rpush('errors', message)

    def destroy(self):
        self.pub_sub.close()


def process_errors(redis_inst):
    error_item = redis_inst.lpop('errors')
    while error_item:
        print(error_item)
        error_item = redis_inst.lpop('errors')


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


