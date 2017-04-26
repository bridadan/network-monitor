#!/usr/bin/env python

"""A simple python script template.
"""

from __future__ import print_function
import os
import sys
import argparse
import logging
import socket

import select
from threading import Thread
from SocketServer import BaseRequestHandler, TCPServer, UDPServer
from time import sleep

tcp_current_count = None
udp_current_count = None

class TCPEchoClientHandler(BaseRequestHandler):
    def handle(self):
        """
        Handles a connection. Test starts by client(i.e. mbed) connecting to server.
        This connection handler receives data and echoes back to the client util
        {{end}} is received. Then it sits on recv() for client to terminate the
        connection.

        Note: reason for not echoing data back after receiving {{end}} is that send
              fails raising a SocketError as client closes connection.
        """
        global tcp_current_count
        while self.server.isrunning():
            try:
                data = self.recv()
                if not data: break
                number_strings = data.splitlines()

                for number_string in number_strings:
                    number_string = number_string.strip()
                    logging.debug('TCP: Received "%s" from "%s"' % (number_string, self.client_address))
                    count = int(number_string)

                    if count == 0:
                        logging.info('TCP: resetting count to 0')
                    elif count != tcp_current_count + 1:
                        logging.error('TCP: expected count of %d, received %d. Resetting to new value' % (tcp_current_count + 1, count))

                    tcp_current_count = count

            except Exception as e:
                break

    def recv(self):
        """
        Try to receive until server is shutdown
        """
        while self.server.isrunning():
            rl, wl, xl = select.select([self.request], [], [], 1)
            if len(rl):
                return self.request.recv(1024)

    def send(self, data):
        """
        Try to send until server is shutdown
        """
        while self.server.isrunning():
            rl, wl, xl = select.select([], [self.request], [], 1)
            if len(wl):
                self.request.sendall(data)
                break


class TCPServerWrapper(TCPServer):
    """
    Wrapper over TCP server to implement server initiated shutdown.
    Adds a flag:= running that a request handler can check and come out of
    recv loop when shutdown is called.
    """

    def __init__(self, addr, request_handler):
        # hmm, TCPServer is not sub-classed from object!
        self.request_queue_size = 0
        if issubclass(TCPServer, object):
            super(TCPServerWrapper, self).__init__(addr, request_handler)
        else:
            TCPServer.__init__(self, addr, request_handler)

        self.running = False

    def serve_forever(self):
        self.running = True
        if issubclass(TCPServer, object):
            super(TCPServerWrapper, self).serve_forever()
        else:
            TCPServer.serve_forever(self)

    def shutdown(self):
        self.running = False
        if issubclass(TCPServer, object):
            super(TCPServerWrapper, self).shutdown()
        else:
            TCPServer.shutdown(self)

    def isrunning(self):
        return self.running

class UDPEchoClientHandler(BaseRequestHandler):
    def handle(self):
        """ UDP packet handler. Echoes data back to sender's address.
        """
        global udp_current_count
        data, sock = self.request
        number_strings = data.splitlines()

        for number_string in number_strings:
            number_string = number_string.strip()
            logging.debug('UDP: Received "%s" from "%s"' % (number_string, self.client_address))
            count = int(number_string)

            if count == 0:
                udp_current_count = 0
                logging.info('UDP: resetting count to 0')
            elif count != udp_current_count + 1:
                logging.error('UDP: expected count of %d, received %d' % (udp_current_count + 1, count))

            udp_current_count = count

def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--tcp-port', help="TCP Server port", default=2342,
                        type=int, dest='tcp_port')
    parser.add_argument('--udp-port', help="UDP Server port", default=2343,
                        type=int, dest='udp_port')
    parser.add_argument('--log-level', help="Python logging level", default='INFO',
                        dest='log_level')

    args = parser.parse_args(arguments)
    logging_format = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=args.log_level.upper(), format=logging_format)
    servers = []

    host = socket.gethostname()

    # TCP server setup
    tcp_server = TCPServerWrapper((host, args.tcp_port), TCPEchoClientHandler)
    tcp_server.allow_reuse_address = True
    tcp_server_thread = Thread(target=tcp_server.serve_forever)
    tcp_server_thread.start()
    servers.append((tcp_server, tcp_server_thread))
    logging.info('Listening for TCP connections on port %d' % args.tcp_port)

    udp_server = UDPServer((host, args.udp_port), UDPEchoClientHandler)
    udp_server.allow_reuse_address = True
    udp_server_thread = Thread(target=udp_server.serve_forever)
    udp_server_thread.start()
    servers.append((udp_server, udp_server_thread))
    logging.info('Listening for UDP packets on port %d' % args.udp_port)

    logging.info('Press Ctrl+C to shutdown the servers')

    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('Shutting down servers')
        for server, thread in servers:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
