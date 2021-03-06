#! python
#-*- coding: utf-8 -*-
#
# Copyright 2013-2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl

from __future__ import division, unicode_literals

import unittest

from jsonschema.exceptions import ValidationError

import numpy.testing as npt
from pandalone import pandata
from pandalone.pandata import PandelVisitor
from pandalone.utils import assertRaisesRegex
import pandas as pd


class TestJsonPath(unittest.TestCase):

    def test_ModelMaker_merge(self):
        class MyMaker(pandata.Pandel):

            def _get_json_schema(self, is_prevalidation):
                return {
                    '$schema': 'http://json-schema.org/draft-04/schema#',
                    'type': ['object'],
                    'required': [] if is_prevalidation else ['a', 'b'],
                    'properties': {
                        'a': {'type': ['number', 'array']},
                        'b': {'type': ['number', 'array']},
                        'c': {'type': ['number', 'array']},
                    }
                }

        # Maps
        mm = MyMaker()

        (s1, s2) = {'a': 1}, {'a': 2}
        mdl = mm._clone_and_merge_submodels(s1, s2)
        self.assertEqual(mdl['a'], 2)

        (s1, s2) = {'a': 1, 'b': 2}, {'a': 11, 'c': 3}
        mdl = mm._clone_and_merge_submodels(s1, s2)
        self.assertEqual(mdl['a'], 11)
        self.assertEqual(mdl['b'], 2)
        self.assertEqual(mdl['c'], 3)

        # DataFranes
        (s1, s2) = pd.DataFrame({'a': [1, 2], 'b': [3, 4]}), {
            'a': [11, 22], 'c': [5, 6]}
        mdl = mm._clone_and_merge_submodels(s1, s2)
        npt.assert_array_equal(mdl['a'], [11, 22])
        npt.assert_array_equal(mdl['b'], [3, 4])
        npt.assert_array_equal(mdl['c'], [5, 6])

        # Series
        (s1, s2) = pd.Series({'a': 1, 'b': 3}), {'a': 11, 'c': 5}
        mdl = mm._clone_and_merge_submodels(s1, s2)
        self.assertEqual(mdl['a'], 11)
        self.assertEqual(mdl['b'], 3)
        self.assertEqual(mdl['c'], 5)

        # Sequences
        l2 = [4, 5]
        (s1, s2) = [1, 2, 3], l2
        mdl = mm._clone_and_merge_submodels(s1, s2)
        npt.assert_array_equal(mdl, l2)

        # Sequences-->Map
        l2 = [4, 5, {'a': 11, 'c': 33}]
        (s1, s2) = [1, 2, {'a': 1, 'b': 2}], l2
        mdl = mm._clone_and_merge_submodels(s1, s2)
        npt.assert_array_equal(mdl, l2)
        obj = mdl[2]
        self.assertEqual(obj['a'], 11)
        self.assertEqual(obj['c'], 33)
        self.assertTrue('b' not in obj)

        # Map-->Sequence
        l2 = [4, 5, {'a': 11, 'c': 3}]
        (s1, s2) = {'a': 1, 'b': [1, 2]}, {'b': l2, 'c': 3}
        mdl = mm._clone_and_merge_submodels(s1, s2)
        self.assertEqual(mdl['a'], 1)
        self.assertEqual(mdl['c'], 3)
        npt.assert_array_equal(mdl['b'], l2)

        # Map-->Map
        (s1, s2) = {'a': 1, 'b': {'aa': -1, 'bb': -2},
                    'c': 3}, {'a': 11, 'b': {'aa': -11, 'cc': -33}, 'd': 44}
        mdl = mm._clone_and_merge_submodels(s1, s2)
        self.assertEqual(mdl['a'], 11)
        self.assertEqual(mdl['c'], 3)
        self.assertEqual(mdl['d'], 44)
        self.assertEqual(mdl['b'], {'aa': -11, 'bb': -2, 'cc': -33})

    def test_ModelMaker_build(self):
        class MyMaker(pandata.Pandel):

            def _get_json_schema(self, is_prevalidation):
                return {
                    '$schema': 'http://json-schema.org/draft-04/schema#',
                    'required': [] if is_prevalidation else ['a', 'b'],
                    'properties': {
                        'a': {'type': 'string'},
                        'b': {'type': 'number'},
                        'c': {'type': 'number'},
                    }
                }

        mm = MyMaker()
        mm.add_submodel({'a': 'foo', 'b': 1})
        mm.add_submodel({'a': 'bar', 'c': 2})

        mdl = mm.build()

        self.assertEqual(mdl['a'], 'bar')
        self.assertEqual(mdl['b'], 1)
        self.assertEqual(mdl['c'], 2)

        mm = MyMaker()  # Invalid submodel['b'], must be a number
        mm.add_submodel({'a': 'foo', 'b': 'string'})
        assertRaisesRegex(
            self, ValidationError, "Failed validating u?'type' in schema\[u?'properties']\[u?'b']", mm.build)

    def test_validate_object_or_pandas(self):
        schema = {
            'type': ['object'],
        }
        pv = PandelVisitor(schema)

        pv.validate({'foo': 'bar'})
        pv.validate(pd.Series({'foo': 'bar', 'foofoo': 'bar'}))
        pv.validate(pd.DataFrame({'foo': [1, 2], 'foofoo': [3, 4]}))

        with assertRaisesRegex(self, ValidationError, "\[1, 2, 3\] is not of type u?'object'"):
            pv.validate([1, 2, 3])

    def test_rule_requiredProperties_rule_for_pandas(self):
        schema = {
            'type': ['object'],
            'required': ['foo']
        }
        pv = PandelVisitor(schema)

        pv.validate({'foo': 'bar'})
        with assertRaisesRegex(self, ValidationError, "'foo' is a required property"):
            pv.validate({'foofoo': 'bar'})

        pv.validate(pd.Series({'foo': 'bar', 'foofoo': 'bar'}))
        with assertRaisesRegex(self, ValidationError, "'foo' is a required property"):
            pv.validate(pd.Series({'foofoo': 'bar'}))

        pv.validate(pd.DataFrame({'foo': [1, 2], 'foofoo': [3, 4]}))
        with assertRaisesRegex(self, ValidationError, "'foo' is a required property"):
            pv.validate(pd.DataFrame({'foofoo': [1, 2], 'bar': [3, 4]}))

    def test_rule_additionalProperties_for_pandas(self):
        schema = {
            'type': ['object'],
            'additionalProperties': False,
            'properties': {
                'foo': {},
            }
        }
        pv = PandelVisitor(schema)

        pv.validate({'foo': 1})
        with assertRaisesRegex(self, ValidationError, "Additional properties are not allowed \(u?'bar' was unexpected\)"):
            pv.validate({'foo': 1, 'bar': 2})

        pv.validate(pd.Series({'foo': 1}))
        with assertRaisesRegex(self, ValidationError, "Additional properties are not allowed \(u?'bar' was unexpected\)"):
            pv.validate(pd.Series({'foo': 1, 'bar': 2}))

        pv.validate(pd.DataFrame({'foo': [1]}))
        with assertRaisesRegex(self, ValidationError, "Additional properties are not allowed \(u?'bar' was unexpected\)"):
            pv.validate(pd.DataFrame({'foo': [1], 'bar': [2]}))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
