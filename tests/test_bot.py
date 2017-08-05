#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hypothesis.strategies as st
import unittest
import unittest.mock as mock
import raid_coordinator.bot as bot

from datetime import datetime, timedelta
from hypothesis import given


class TestRaidExpiration(unittest.TestCase):
    """Tests around whether raid channels are expired."""

    @given(seconds=st.integers(min_value=0))
    def test_is_expired_elapsed(self, seconds):
        """
        Should be expired if the timestamp is older than expiration time ago.
        """
        message_ts = datetime.utcnow() - timedelta(seconds=seconds)
        message = mock.Mock(timestamp=message_ts)
        with mock.patch('raid_coordinator.bot.settings', new=mock.Mock(raid_duration_seconds=seconds)):
            self.assertTrue(bot.is_expired(message))

    @given(seconds=st.integers(min_value=1))
    def test_is_expired_1s(self, seconds):
        """
        Should not be expired with more than 1s left from message timestamp
        """
        message_ts = datetime.utcnow()
        message = mock.Mock(timestamp=message_ts)
        with mock.patch('raid_coordinator.bot.settings', new=mock.Mock(raid_duration_seconds=seconds)):
            self.assertFalse(bot.is_expired(message))
