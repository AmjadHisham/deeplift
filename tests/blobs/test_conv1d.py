from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
from unittest import skip
import sys
import os
import numpy as np
import deeplift.blobs as blobs
from deeplift.blobs import DenseMxtsMode, ConvMxtsMode
from deeplift.backend import BorderMode as PaddingMode
from deeplift.backend import PoolMode
from deeplift.backend import function as compile_func
import itertools


class TestConv(unittest.TestCase):

    def setUp(self):
        #swap axes for tensorflow
        self.input_layer = blobs.Input(
                            num_dims=None,
                            shape=(None,2,4))
        #tensorflow, shockingly, does not flip the weights of a conv
        self.w1 = (np.arange(4).reshape(2,2)[:,::-1].astype("float32")-2.0)
        self.w2 = -(np.arange(4).reshape(2,2)[:,::-1].astype("float32")-2.0)
        self.conv_W = (np.array([self.w1, self.w2])
                       .astype("float32"))
        self.conv_b = np.array([-1.0, 1.0]).astype("float32")

    def create_small_net_with_conv_layer(self, conv_layer,
                                               outputs_per_channel):
        self.conv_layer = conv_layer
        self.conv_layer.set_inputs(self.input_layer)

        self.flatten_layer = blobs.Flatten()
        self.flatten_layer.set_inputs(self.conv_layer)

        self.dense_layer = blobs.Dense(
                           W=(np.array(
                              [([1.0]*outputs_per_channel)+
                               ([-1.0]*outputs_per_channel)]).T
                              .astype("float32")),
                           b=np.array([1]).astype("float32"),
                           dense_mxts_mode=DenseMxtsMode.Linear)
        self.dense_layer.set_inputs(self.flatten_layer)

        self.dense_layer.build_fwd_pass_vars()
        self.input_layer.reset_mxts_updated()
        self.dense_layer.set_scoring_mode(blobs.ScoringMode.OneAndZeros)
        self.dense_layer.set_active()
        self.input_layer.update_mxts()

        self.inp = (np.arange(16).reshape((2,2,4))
                    .astype("float32"))-8.0
        
    def test_fprop_border_mode_valid(self): 
        conv_layer = blobs.Conv1D(W=self.conv_W, b=self.conv_b,
                                  stride=1,
                                  border_mode=PaddingMode.valid,
                                  channels_come_last=False,
                                  conv_mxts_mode=ConvMxtsMode.Linear)
        self.create_small_net_with_conv_layer(conv_layer,
                                              outputs_per_channel=3)
        func = compile_func([self.input_layer.get_activation_vars()],
                                self.conv_layer.get_activation_vars())
       #input:
       #      [[[-8,-7,-6,-5],
       #        [-4,-3,-2,-1]],
       #       [[ 0, 1, 2, 3],
       #        [ 4, 5, 6, 7]]]
       # W:
       # [-2,-1
       #   0, 1]
       # 16+7+0+-3 = 20 - bias (1.0) = 19
       # 0+-1+0+5 = 4 - bias (1.0) = 3
        np.testing.assert_almost_equal(func(self.inp),
                               np.array(
                               [[[ 19, 17, 15],
                                 [-19,-17,-15]],
                                [[ 3, 1,-1],
                                 [-3,-1, 1]]]))

    def test_fprop_border_mode_same(self): 
        print(self.conv_W.shape)
        conv_layer = blobs.Conv1D(
            W=self.conv_W,#np.concatenate([np.zeros(4).reshape(2,2,1),
                         #      self.conv_W],axis=2),
            b=self.conv_b,
            stride=1,
            border_mode=PaddingMode.same,
            channels_come_last=False,
            conv_mxts_mode=ConvMxtsMode.Linear)
        self.create_small_net_with_conv_layer(conv_layer,
                                              outputs_per_channel=3)
        func = compile_func([self.input_layer.get_activation_vars()],
                             self.conv_layer.get_activation_vars())
       #input:
       #      [[[-8,-7,-6,-5],
       #        [-4,-3,-2,-1]],
       #       [[ 0, 1, 2, 3],
       #        [ 4, 5, 6, 7]]]
       # W:
       # [-2,-1
       #   0, 1]
       # 16+7+0+-3 = 20 - bias (1.0) = 19
       # 0+-1+0+5 = 4 - bias (1.0) = 3
        np.testing.assert_almost_equal(func(self.inp),
                               np.array(
                               [[[ 3, 19, 17, 15],
                                 [-3,-19,-17,-15]],
                                [[ 3, 3, 1,-1],
                                 [-3,-3,-1, 1]]]))
        
        
    def test_fprop_pos_and_neg_contribs(self): 
        conv_layer = blobs.Conv1D(W=self.conv_W, b=self.conv_b,
                                  stride=1,
                                  border_mode=PaddingMode.valid,
                                  channels_come_last=False,
                                  conv_mxts_mode=ConvMxtsMode.Linear)
        self.create_small_net_with_conv_layer(conv_layer,
                                              outputs_per_channel=3)
        pos_contribs, neg_contribs = self.conv_layer.get_pos_and_neg_contribs() 
        func_pos = compile_func([self.input_layer.get_activation_vars(),
                                 self.input_layer.get_reference_vars()],
                             pos_contribs)
        func_neg = compile_func([self.input_layer.get_activation_vars(),
                                 self.input_layer.get_reference_vars()],
                             neg_contribs)
       #diff from ref:
       #      [[[-9,-8,-7,-6],
       #        [-5,-4,-3,-2]],
       #       [[-1, 0, 1, 2],
       #        [ 3, 4, 5, 6]]]
       # W:
       # [-2,-1
       #   0, 1]
       # 18+8 = 26, -4 = -4
       # 0+-1+0+5 = 4 - bias (1.0) = 3
        np.testing.assert_almost_equal(func_pos(self.inp,
                                                np.ones_like(self.inp)),
                               np.array(
                               [[[ 26, 23, 20],
                                 [  4,  3,  2]],
                                [[  6,  5,  6],
                                 [  0,  1,  4]]]))
        np.testing.assert_almost_equal(func_neg(self.inp,
                                                np.ones_like(self.inp)),
                               np.array(
                               [[[ -4, -3, -2],
                                 [-26,-23,-20]],
                                [[  0, -1, -4],
                                 [ -6, -5, -6]]]))


    def test_dense_backprop(self):
        conv_layer = blobs.Conv1D(W=self.conv_W, b=self.conv_b,
                                  stride=1,
                                  border_mode=PaddingMode.valid,
                                  channels_come_last=False,
                                  conv_mxts_mode=ConvMxtsMode.Linear)
        self.create_small_net_with_conv_layer(conv_layer,
                                              outputs_per_channel=3)
        self.dense_layer.update_task_index(task_index=0)
        func = compile_func([self.input_layer.get_activation_vars(),
                             self.input_layer.get_reference_vars()],
                            self.input_layer.get_mxts())
        np.testing.assert_almost_equal(
            func(self.inp, np.zeros_like(self.inp)),
            np.array(
             [[[ -4, -6, -6, -2],
               [  0,  2,  2,  2]],
              [[ -4, -6, -6, -2],
               [  0,  2,  2,  2]]]))

    def test_fprop_stride(self): 

        conv_layer = blobs.Conv1D(
            W=self.conv_W,
            b=self.conv_b,
            stride=2,
            border_mode=PaddingMode.valid,
            channels_come_last=False,
            conv_mxts_mode=ConvMxtsMode.Linear)
        self.create_small_net_with_conv_layer(conv_layer,
                                              outputs_per_channel=3)
        func = compile_func([self.input_layer.get_activation_vars()],
                                self.conv_layer.get_activation_vars())
       #input:
       #      [[[-8,-7,-6,-5],
       #        [-4,-3,-2,-1]],
       #       [[ 0, 1, 2, 3],
       #        [ 4, 5, 6, 7]]]
       # W:
       # [-2,-1
       #   0, 1]
       # 16+7+0+-3 = 20 - bias (1.0) = 19
       # 0+-1+0+5 = 4 - bias (1.0) = 3
        np.testing.assert_almost_equal(func(self.inp),
                               np.array(
                               [[[ 19, 15],
                                 [-19,-15]],
                                [[ 3, -1],
                                 [-3, 1]]]))

    def test_dense_backprop_stride(self):
        conv_layer = blobs.Conv1D(W=self.conv_W, b=self.conv_b,
                                  stride=2,
                                  border_mode=PaddingMode.valid,
                                  channels_come_last=False,
                                  conv_mxts_mode=ConvMxtsMode.Linear)
        self.create_small_net_with_conv_layer(conv_layer,
                                              outputs_per_channel=2)
        self.dense_layer.update_task_index(task_index=0)
        func = compile_func([self.input_layer.get_activation_vars(),
                             self.input_layer.get_reference_vars()],
                            self.input_layer.get_mxts())
        np.testing.assert_almost_equal(
            func(self.inp, np.zeros_like(self.inp)),
            np.array(
             [[[ -4,  -2,  -4, -2],
               [  0,   2,   0,  2]],
              [[ -4,  -2,  -4, -2],
               [  0,   2,   0,  2]]]))
