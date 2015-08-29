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

from functools import partial

from django.db import models

from instance.logging import PUBLISHED_LOG_LEVEL_SET


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Models ######################################################################


class LoggerInstanceMixin(models.Model):
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
