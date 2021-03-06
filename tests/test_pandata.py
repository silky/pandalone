#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl

from __future__ import division, print_function, unicode_literals

import doctest
import json
import unittest

from jsonschema.exceptions import RefResolutionError

import numpy as np
import numpy.testing as npt
from pandalone import pandata
from pandalone.pandata import JSONCodec
import pandas as pd


class TestDoctest(unittest.TestCase):

    def runTest(self):
        failure_count, test_count = doctest.testmod(
            pandata, optionflags=doctest.NORMALIZE_WHITESPACE)
        self.assertGreater(test_count, 0, (failure_count, test_count))
        self.assertEquals(failure_count, 0, (failure_count, test_count))


class TestJSONCodec(unittest.TestCase):

    def test_lists(self):
        o = [1, 2, '3', 'fdgdg', None, []]
        s = json.dumps(o, cls=JSONCodec.Encoder)
        oo = json.loads(s, cls=pandata.JSONCodec.Decoder)
        self.assertEqual(oo, o)

    def test_dict(self):
        o = {'a': 1, 2: 'bb', 3: [], 4: None}
        s = json.dumps(o, cls=JSONCodec.Encoder)
        oo = json.loads(s, cls=pandata.JSONCodec.Decoder)
        self.assertEqual(oo, o)

    def test_Numpy(self):
        o = np.random.randn(6, 2)
        s = json.dumps(o, cls=JSONCodec.Encoder)
        oo = json.loads(s, cls=pandata.JSONCodec.Decoder)
        npt.assert_array_equal(oo, o)

    def test_DataFrame(self):
        o = pd.DataFrame(np.random.randn(10, 2))
        s = json.dumps(o, cls=JSONCodec.Encoder)
        oo = json.loads(s, cls=pandata.JSONCodec.Decoder)
        npt.assert_array_equal(oo, o)

    def test_Series(self):
        o = pd.Series({'a': 1, 2: 22})
        s = json.dumps(o, cls=JSONCodec.Encoder)
        oo = json.loads(s, cls=pandata.JSONCodec.Decoder)
        npt.assert_array_equal(oo, o)

    @unittest.skip(('TODO: Cannot test for recursive-equality with pandas.'))
    def test_mix(self):
        obj_list = [3.14,
                    {
                        'aa': pd.DataFrame([]),
                        2: np.array([]),
                        33: {'foo': 'bar'},
                    },
                    pd.DataFrame(np.random.randn(10, 2)),
                    ('b', pd.Series({})),
                    ]
        for o in obj_list + [obj_list]:
            s = json.dumps(o, cls=JSONCodec.Encoder)
            oo = json.loads(s, cls=pandata.JSONCodec.Decoder)
            self.assertTrue(pandata.trees_equal(o, oo), (o, oo))


class TestJsonPointer(unittest.TestCase):

    def test_resolve_jsonpointer_existing(self):
        doc = {
            'foo': 1,
            'bar': [11, {'a': 222}]
        }

        path = '/foo'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), 1)

        path = '/bar/0'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), 11)

        path = '/bar/1/a'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), 222)

    def test_resolve_jsonpointer_sequence(self):
        doc = [1, [22, 33]]

        path = '/0'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), 1)

        path = '/1'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), [22, 33])

        path = '/1/0'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), 22)
        path = '/1/1'
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), 33)

    def test_resolve_jsonpointer_missing_screams(self):
        doc = {}

        path = '/foo'
        with self.assertRaises(RefResolutionError):
            pandata.resolve_jsonpointer(doc, path)

    def test_resolve_jsonpointer_empty_path(self):
        doc = {}
        path = ''
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), doc)

        doc = {'foo': 1}
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), doc)

    def test_resolve_jsonpointer_examples_from_spec(self):
        def _doc():
            return {
                r"foo": ["bar", r"baz"],
                r"": 0,
                r"a/b": 1,
                r"c%d": 2,
                r"e^f": 3,
                r"g|h": 4,
                r"i\\j": 5,
                r"k\"l": 6,
                r" ": 7,
                r"m~n": 8
            }
        cases = [
            (r"",            _doc()),
            (r"/foo",        ["bar", "baz"]),
            (r"/foo/0",      "bar"),
            (r"/",           0),
            (r"/a~1b",       1),
            (r"/c%d",      2),
            (r"/e^f",      3),
            (r"/g|h",      4),
            (r"/i\\j",      5),
            (r"/k\"l",      6),
            (r"/ ",        7),
            (r"/m~0n",       8),
        ]
        for path, exp in cases:
            doc = _doc()
            self.assertEqual(pandata.resolve_jsonpointer(doc, path), exp)

    def test_set_jsonpointer_empty_doc(self):
        doc = {}
        path = '/foo'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)

        doc = {}
        path = '/foo/bar'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)

    def test_resolve_jsonpointer_root_path_only(self):
        doc = {}
        path = '/'
        with self.assertRaises(RefResolutionError):
            self.assertEqual(pandata.resolve_jsonpointer(doc, path), doc)

        doc = {'foo': 1}
        with self.assertRaises(RefResolutionError):
            self.assertEqual(pandata.resolve_jsonpointer(doc, path), doc)

        doc = {'': 1}
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), doc[''])

    def test_set_jsonpointer_replace_value(self):
        doc = {'foo': 'bar', 1: 2}
        path = '/foo'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

        doc = {'foo': 1, 1: 2}
        path = '/foo'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

        doc = {'foo': {'bar': 1}, 1: 2}
        path = '/foo'
        value = 2
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

    def test_set_jsonpointer_append_path(self):
        doc = {'foo': 'bar', 1: 2}
        path = '/foo/bar'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

        doc = {'foo': 'bar', 1: 2}
        path = '/foo/bar/some/other'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

    def test_set_jsonpointer_append_path_preserves_intermediate(self):
        doc = {'foo': {'bar': 1}, 1: 2}
        path = '/foo/foo2'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        print(doc)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)
        self.assertEqual(pandata.resolve_jsonpointer(doc, '/foo/bar'), 1)

    def test_set_jsonpointer_missing(self):
        doc = {'foo': 1, 1: 2}
        path = '/foo/bar'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

        doc = {'foo': 1, 1: 2}
        path = '/foo/bar/some/other'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(doc[1], 2)

    def test_set_jsonpointer_sequence(self):
        doc = [1, 2]
        path = '/1'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)

        doc = [1, 2]
        path = '/1/foo/bar'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)

    def test_set_jsonpointer_sequence_insert_end(self):
        doc = [0, 1]
        path = '/2'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, path), value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, '/0'), 0)
        self.assertEqual(pandata.resolve_jsonpointer(doc, '/1'), 1)

        doc = [0, 1]
        path = '/-'
        value = 'value'
        pandata.set_jsonpointer(doc, path, value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, '/2'), value)
        self.assertEqual(pandata.resolve_jsonpointer(doc, '/0'), 0)
        self.assertEqual(pandata.resolve_jsonpointer(doc, '/1'), 1)

    def test_set_jsonpointer_sequence_out_of_bounds(self):
        doc = [0, 1]
        path = '/3'
        value = 'value'
        with self.assertRaises(RefResolutionError):
            pandata.set_jsonpointer(doc, path, value)

    def test_set_jsonpointer_sequence_with_str_screams(self):
        doc = [0, 1]
        path = '/str'
        value = 'value'
        with self.assertRaises(RefResolutionError):
            pandata.set_jsonpointer(doc, path, value)

    def test_build_all_jsonpaths(self):
        from jsonschema._utils import load_schema
        schema = dict(properties=dict(a=dict(properties=dict(b={}))))
        paths = pandata.build_all_jsonpaths(schema)
        print('\n'.join(paths))
        # TODO: build and check_all_paths support $ref
        self.assertIn('/a/b', paths)
