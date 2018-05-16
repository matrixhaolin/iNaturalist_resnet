"""
Copyright 2018 The Matrix Authors
This file is part of the Matrix library.

The Matrix library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The Matrix library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with the Matrix library. If not, see <http://www.gnu.org/licenses/>.
"""
# -*- coding: UTF-8 -*-
# File: config.py


import tensorflow as tf
import six

from ..graph_builder import ModelDescBase
from ..tfutils import get_default_sess_config
from ..tfutils.tower import TowerFuncWrapper
from ..tfutils.sessinit import SessionInit, JustCurrentSession

__all__ = ['PredictConfig']


class PredictConfig(object):
    def __init__(self,
                 model=None,
                 inputs_desc=None,
                 tower_func=None,

                 input_names=None,
                 output_names=None,

                 session_creator=None,
                 session_init=None,
                 return_input=False,
                 create_graph=True,
                 ):
        """
        You need to set either `model`, or `inputs_desc` plus `tower_func`.
        They are needed to construct the graph.
        You'll also have to set `output_names` as it does not have a default.

        Args:
            model (ModelDescBase): to be used to obtain inputs_desc and tower_func.
            inputs_desc ([InputDesc]):
            tower_func: a callable which takes input tensors and construct a tower.

            input_names (list): a list of input tensor names. Defaults to match inputs_desc.
            output_names (list): a list of names of the output tensors to predict, the
                tensors can be any computable tensor in the graph.

            session_creator (tf.train.SessionCreator): how to create the
                session. Defaults to :class:`tf.train.ChiefSessionCreator()`.
            session_init (SessionInit): how to initialize variables of the session.
                Defaults to do nothing.

            return_input (bool): same as in :attr:`PredictorBase.return_input`.
            create_graph (bool): create a new graph, or use the default graph
                when predictor is first initialized.
        """
        def assert_type(v, tp):
            assert isinstance(v, tp), v.__class__
        if model is not None:
            assert_type(model, ModelDescBase)
            assert inputs_desc is None and tower_func is None
            self.inputs_desc = model.get_inputs_desc()
            self.tower_func = TowerFuncWrapper(model.build_graph, self.inputs_desc)
        else:
            assert inputs_desc is not None and tower_func is not None
            self.inputs_desc = inputs_desc
            self.tower_func = TowerFuncWrapper(tower_func, inputs_desc)

        if session_init is None:
            session_init = JustCurrentSession()
        self.session_init = session_init
        assert_type(self.session_init, SessionInit)

        if session_creator is None:
            self.session_creator = tf.train.ChiefSessionCreator(config=get_default_sess_config())
        else:
            self.session_creator = session_creator

        # inputs & outputs
        self.input_names = input_names
        if self.input_names is None:
            self.input_names = [k.name for k in self.inputs_desc]
        self.output_names = output_names
        assert_type(self.output_names, list)
        assert_type(self.input_names, list)
        assert len(self.input_names), self.input_names
        for v in self.input_names:
            assert_type(v, six.string_types)
        assert len(self.output_names), self.output_names

        self.return_input = bool(return_input)
        self.create_graph = bool(create_graph)

    def _maybe_create_graph(self):
        if self.create_graph:
            return tf.Graph()
        return tf.get_default_graph()
