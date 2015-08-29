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
Instance app models - Logging
"""

# Imports #####################################################################

import logging

from django.db import models
from django.db.models import query
from django_extensions.db.models import TimeStampedModel

from instance.logging import level_to_integer
from instance.models.instance import OpenEdXInstance
from instance.models.server import OpenStackServer
from instance.models.utils import ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Models ######################################################################

class LogEntryQuerySet(query.QuerySet):
    """
    Additional methods for LogEntry querysets
    Also used as the standard manager for the model (`LogEntry.objects`)
    """
    def create(self, publish=True, *args, **kwargs):
        log_entry = super().create(*args, **kwargs)
        if publish:
            log_entry.publish()


class LogEntry(ValidateModelMixin, TimeStampedModel):
    """
    Single log entry
    """
    LOG_LEVEL_CHOICES = (
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warn', 'Warning'),
        ('error', 'Error'),
        ('exception', 'Exception'),
    )

    text = models.TextField(blank=True)
    level = models.CharField(max_length=9, db_index=True, default='info', choices=LOG_LEVEL_CHOICES)

    objects = LogEntryQuerySet().as_manager()

    class Meta:
        abstract = True
        log_entry_model = None
        log_entry_obj_attribute_name = None
        permissions = (
            ("read_car", "Can read Car"),
        )

    def __str__(self):
        return '{0.created:%Y-%m-%d %H:%M:%S} [{0.level}] {0.text}'.format(self)

    @property
    def level_integer(self):
        """
        Integer code for the log entry level
        """
        return level_to_integer(self.level)

    @property
    def obj(self):
        """
        Returns the object this log entry refers to
        """
        meta = self.__class__.Meta
        if meta.log_entry_obj_attribute_name is None:
            return None
        return getattr(self, meta.log_entry_obj_attribute_name)


class GeneralLogEntry(LogEntry):
    """
    Single log entry that isn't attached to a specific model, such as instances or servers
    """
    class Meta:
        log_entry_model = None
        log_entry_obj_attribute_name = None
        verbose_name_plural = "General Log Entries"


class InstanceLogEntry(LogEntry):
    """
    Single log entry for instances
    """
    instance = models.ForeignKey(OpenEdXInstance, related_name='logentry_set')

    class Meta:
        log_entry_model = OpenEdXInstance
        log_entry_obj_attribute_name = 'instance'
        verbose_name_plural = "Instance Log Entries"


class ServerLogEntry(LogEntry):
    """
    Single log entry for servers
    """
    server = models.ForeignKey(OpenStackServer, related_name='logentry_set')

    class Meta:
        log_entry_model = OpenStackServer
        log_entry_obj_attribute_name = 'server'
        verbose_name_plural = "Server Log Entries"

    @property
    def instance(self):
        """
        Instance of the server
        """
        return self.server.instance
