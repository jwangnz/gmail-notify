#!/usr/bin/env python
 
from __future__ import with_statement
 
import time
import random
 
from twisted.python import log
from twisted.words.xish import domish
from twisted.words.protocols.jabber.xmlstream import toResponse
 
from wokkel.subprotocols import XMPPHandler, IQHandlerMixin

from gmailnotify import gear_client

NS_GMAIL = "google:mail:notify"
QUERY_MAILBOX = "/iq[@type='result'] /mailbox[@xmlns='" + NS_GMAIL + "']"
QUERY_NOTIFY = "/iq[@type='set'] /new-mail[@xmlns='" + NS_GMAIL + "']"

class GMailNotifierProtocol(XMPPHandler, IQHandlerMixin):

    iqHandlers = { QUERY_MAILBOX: "onGmailQueryResult",
                   QUERY_NOTIFY: "onGmailNotify" }

    def __init__(self, jid):
        self.jid = jid
        self.last_date = None

    def connectionInitialized(self):
        self.xmlstream.addObserver(QUERY_MAILBOX, self.handleRequest)
        self.xmlstream.addObserver(QUERY_NOTIFY, self.handleRequest)
        self.queryMail()

    def onGmailQueryResult(self, iq):
        log.msg("got gmail query result: %s" % iq.toXml())
        for threadinfo in reversed(list(iq.mailbox.elements())):
            email_date = int(threadinfo.getAttribute("date"))
            if self.last_date and self.last_date >= email_date:
                continue

            self.last_date = email_date
            email_sender = None
            email_subject = unicode(threadinfo.subject)
            email_snippet = unicode(threadinfo.snippet)
            email_link = threadinfo.getAttribute("url")
            for sender in threadinfo.senders.elements():
                if sender.getAttribute("originator") == "1":
                    name = sender.getAttribute("name")
                    address = sender.getAttribute("address")
                    email_sender = name and "%s <%s>" % (name, address) or address
                    break
            mail = { "subject": email_subject, "sender" : email_sender, "snippet": email_snippet, "link": email_link }
            self.notifyMail(mail)

    def onGmailNotify(self, iq):
        log.msg("got gmail notify: %s" % iq.toXml())
        response = toResponse(iq, "result")
        self.send(response)

        self.queryMail()

    def queryMail(self):
        iq = domish.Element((None, "iq"))
        iq["to"] = self.jid
        iq["type"] = "get"
        iq.addElement((NS_GMAIL, "query"))
        self.send(iq)

    def notifyMail(self, mail):
        content = "[Mail] %s\nFrom: %s \nSnippet: %s\n%s" % (mail["subject"], mail["sender"], mail["snippet"], mail["link"])
        gear_client.submit("xmpp_message", { "to" : self.jid, "content" : content })

