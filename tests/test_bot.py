#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import raid_bot.bot


class TestFoo(unittest.TestCase):

    def test_cached_property(self):
        expected = 'expected'

        @raid_bot.bot.cached_attribute
        def foo_bar(server):
            return expected

        self.assertDictEqual(raid_bot.bot.cache, dict())
        server = 'a'
        result = foo_bar(server)
        self.assertEqual(result, expected)
        self.assertDictEqual(raid_bot.bot.cache, {server: {'foo_bar': expected}})
