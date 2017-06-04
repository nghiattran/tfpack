# https://github.com/MarvinTeichmann/KittiBox/blob/master/optimizer/generic_optimizer.py

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorpack.base import OptimizerBase
import tensorflow as tf

class Optimizer(OptimizerBase):
    def get_learning_rate(self, hypes, step):
        if "learning_rates" not in hypes['solver']:
            lr = hypes['solver']['learning_rate']
            lr_step = hypes['solver']['learning_rate_step']
            if lr_step is not None:
                adjusted_lr = (lr * 0.5 ** max(0, (step / lr_step) - 2))
                return adjusted_lr
            else:
                return lr

        for i, num in enumerate(hypes['solver']['steps']):
            if step < num:
                return hypes['solver']['learning_rates'][i]

    def train(self, hypes, loss, global_step, learning_rate):
        sol = hypes["solver"]
        hypes['tensors'] = {}
        hypes['tensors']['global_step'] = global_step
        total_loss = loss['total_loss']
        with tf.name_scope('training'):

            if sol['opt'] == 'RMS':
                opt = tf.train.RMSPropOptimizer(learning_rate=learning_rate,
                                                decay=0.9, epsilon=sol.get('epsilon', 1e-5))
            elif sol['opt'] == 'Adam':
                opt = tf.train.AdamOptimizer(learning_rate=learning_rate,
                                             epsilon=sol.get('epsilon', 1e-5))
            elif sol['opt'] == 'SGD':
                lr = learning_rate
                opt = tf.train.GradientDescentOptimizer(learning_rate=lr)
            else:
                raise ValueError('Unrecognized opt type')

            grads_and_vars = opt.compute_gradients(total_loss)

            clip_norm = hypes.get('clip_norm', -1)

            if clip_norm > 0:
                grads, tvars = zip(*grads_and_vars)
                clipped_grads, norm = tf.clip_by_global_norm(grads, clip_norm)
                grads_and_vars = zip(clipped_grads, tvars)

            update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)

            with tf.control_dependencies(update_ops):
                train_op = opt.apply_gradients(grads_and_vars,
                                               global_step=global_step)

        return train_op