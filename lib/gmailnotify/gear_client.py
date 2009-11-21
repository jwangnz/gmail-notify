#!/usr/bin/env python

from twisted.python import log
from twisted.internet import protocol, reactor

import json

from gearman import client

gear_client = None

class GearmanClientProtocol(client.GearmanProtocol):
    def makeConnection(self, transport):
        global gear_client
        client.GearmanProtocol.makeConnection(self, transport)
        gear_client = client.GearmanClient(self)

class GearmanClientFactory(protocol.ReconnectingClientFactory):
    def startedConnecting(self, connector):
        log.msg("Started to connect to gearman as client")

    def buildProtocol(self, addr):
        self.resetDelay()
        log.msg("Connected to gearman as client")

        gearman = GearmanClientProtocol()
        return gearman

    def clientConnectionLost(self, connector, reason):
        log.msg("Lost connection of gearman client. Reason: %s" % reason)
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed of gearman client. Reason: %s" % reason)
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

def connect():
    connector = reactor.connectTCP("127.0.0.1", 4730, GearmanClientFactory())

def submit(funcname, data):
    data = json.dumps(data)
    log.msg("submit %s with data: %s" % (funcname, data))
    gear_client.submitBackground(funcname, data)
