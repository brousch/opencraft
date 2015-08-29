# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Instance app models - Logging - Mixins
"""

# Imports #####################################################################

import logging
import traceback

from functools import partial, wraps
from swampdragon.pubsub_providers.data_publisher import publish_data

from django.apps import apps
from django.db import models


# Constants ###################################################################

# TODO: Don't propagate exceptions & debug data to end users
PUBLISHED_LOG_LEVEL_SET = ('info', 'warn', 'error', 'exception')


# Logging #####################################################################

logger = logging.getLogger(__name__)

DEBUG_LEVELV_NUM = 9
logging.addLevelName(DEBUG_LEVELV_NUM, "DEBUGV")
def debugv(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(DEBUG_LEVELV_NUM):
        self._log(DEBUG_LEVELV_NUM, message, args, **kws)
logging.Logger.debugv = debugv


# Functions ###################################################################

def level_to_integer(level):
    """
    Get the integer code for a log level string
    """
    if level == 'exception':
        return logging.__dict__['CRITICAL']
    else:
        return logging.__dict__[level.upper()]

def log_exception(method):
    """
    Decorator to log uncaught exceptions on methods
    Uses the object logging facilities, ie the following method should be defined:
    self.log(<log_level_str>, <log_message>)`
    """
    @wraps(method)
    def wrapper(self, *args, **kwds): #pylint: disable=missing-docstring
        try:
            return method(self, *args, **kwds)
        except:
            self.log('exception', traceback.format_exc())
            raise
    return wrapper


# Classes #####################################################################

class DBHandler(logging.Handler):
    """
    Records log messages in database models
    """
    def emit(self, record, obj=None):
        """
        Handles an emitted log entry and stores it in the database, optionally linking it to the
        model object `obj`
        """
        try:
            log_entry_model = self.get_log_entry_model(obj)
            log_entry = log_entry_model.objects.create(level=record.levelname, text=self.format(record))

            if self.pk is not None:
                self.logentry_set.create(level=level, text=text.rstrip(), **kwargs)
            else:
                level_integer = level_to_integer(level)
                text = '{} [Log not attached to instance, not saved yet]'.format(text)
                logger.log(level_integer, text)

        except Exception: #pylint: disable=broad-except
            self.handleError(record)

    def get_log_entry_model(self, obj):
        """
        Gets the log entry model corresponding to the `obj` model object, if available
        Returns a generic log entry model if not available, or if the `obj` is not saved in the DB yet
        """
        from instance.models.logging import LogEntry, GeneralLogEntry

        if obj is None or not isinstance(models.Model) or obj.pk is None:
            return GeneralLogEntry

        for model in apps.get_models():
            if isinstance(LogEntry, model) and isinstance(model.Meta.log_entry_model, obj):
                return model

        return GeneralLogEntry


class BrowserHandler(logging.Handler):
    def emit(self):
        """
        Publish the log entry to the messaging system, broadcasting it to subscribers
        """
        logger.log(self.level_integer, self.text)

        if self.level in PUBLISHED_LOG_LEVEL_SET:
            publish_data('log', {
                'type': 'instance_log',
                'instance_id': self.instance.pk,
                'log_entry': str(self),
            })


class LoggerMixin(models.Model):
    """
    Logging facilities - Logs stored on the model & shared with the client via websocket
    """
    class Meta:
        abstract = True

    def log(self, level, text, **kwargs):
        """
        Log an entry text at a specified level
        """


class LoggerInstanceMixin(LoggerMixin):
    """
    Logging facilities - Instances
    """
    class Meta:
        abstract = True

    @property
    def log_text(self):
        """
        Combines the instance and server log outputs in chronological order
        Currently only supports one non-terminated server at a time
        Returned as a text string
        """
        current_server = self.active_server_set.get()
        server_logentry_set = current_server.logentry_set.filter(level__in=PUBLISHED_LOG_LEVEL_SET)\
                                                         .order_by('pk')\
                                                         .iterator()
        instance_logentry_set = self.logentry_set.filter(level__in=PUBLISHED_LOG_LEVEL_SET)\
                                                 .order_by('pk')\
                                                 .iterator()

        next_server_logentry = partial(next, server_logentry_set, None)
        next_instance_logentry = partial(next, instance_logentry_set, None)

        log_text = ''
        instance_logentry = next_instance_logentry()
        server_logentry = next_server_logentry()

        while instance_logentry is not None and server_logentry is not None:
            if server_logentry.created < instance_logentry.created:
                log_text += '{}\n'.format(server_logentry)
                server_logentry = next_server_logentry()
            else:
                log_text += '{}\n'.format(instance_logentry)
                instance_logentry = next_instance_logentry()

        while instance_logentry is not None:
            log_text += '{}\n'.format(instance_logentry)
            instance_logentry = next_instance_logentry()

        while server_logentry is not None:
            log_text += '{}\n'.format(server_logentry)
            server_logentry = next_server_logentry()

        return log_text
