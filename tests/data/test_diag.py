"""
Created on Mon Sep 28 14:32:50 2015

@author: Duin
"""

from unittest import TestCase

import rtctools.data.pi as pi

from .data_path import data_path


class TestDiag(TestCase):
    def setUp(self):
        self.diag = pi.Diag(data_path(), "diag")

    def test_read_errors(self):
        self.diag = pi.Diag(data_path(), "diag")
        diag_lines = self.diag.get(self.diag.INFO)
        for child in diag_lines:
            print(child.tag)
        self.assertTrue(self.diag.has_errors)
