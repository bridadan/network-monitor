#!/usr/bin/env python

"""A simple python script template.
"""

from __future__ import print_function
import os
import sys
import argparse
import socket
import logging
from threading import Thread
from time import sleep

running = True

def TCPThread(host, port, period):
    global running
    logging.info('Starting TCP traffic for %s:%d' % (host, port))
    counter = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    while running:
        s.send("%d\n" % counter)
        counter += 1
        sleep(period)

    s.close()
    logging.info('Stopping TCP traffic for %s:%d' % (host, port))

def UDPThread(host, port, period):
    global running
    logging.info('Starting UDP traffic for %s:%d' % (host, port))
    counter = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while running:
        s.sendto("%d\n" % counter, (host, port))
        counter += 1
        sleep(period)

    s.close()
    logging.info('Stopping UDP traffic for %s:%d' % (host, port))

def main(arguments):
    global running
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('hosts', help="Host address", nargs="*")
    parser.add_argument('--tcp-port', help="TCP Server port", default=2342,
                        type=int, dest='tcp_port')
    parser.add_argument('--udp-port', help="UDP Server port", default=2343,
                        type=int, dest='udp_port')
    parser.add_argument('--period', help="The period at which to send packets",
                        type=float, default=0.1)
    parser.add_argument('--log-level', help="Python logging level", default='INFO',
                        dest='log_level')

    args = parser.parse_args(arguments)
    logging_format = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=args.log_level.upper(), format=logging_format)
    threads = []

    for host in args.hosts:
        tcp_thread = Thread(target=TCPThread, args=(host, args.tcp_port, args.period))
        tcp_thread.start()
        threads.append(tcp_thread)

        udp_thread = Thread(target=UDPThread, args=(host, args.udp_port, args.period))
        udp_thread.start()
        threads.append(udp_thread)

    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('Shutting down clients')
        running = False
        for thread in threads:
            thread.join()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
