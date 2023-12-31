import tensorflow as tf
import numpy as np
from skimage.transform import resize
import os

PB_FILE = os.path.join(os.path.dirname(__file__), "models", "graph.pb")
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "models")


class Extractor:

    def __init__(self):
        self.SIZE = 128
        self.load_pb()

    def load_pb(self):
        graph = tf.Graph()
        """
            https://www.tensorflow.org/api_docs/python/tf/compat/v1/Session
            bug compatibility tensorflow v2 version
            original v1 version: self.sess = tf.Session(graph=graph)
            v2 version: self.sess = tf.compat.v1.Session(graph=graph)
        """
        self.sess = tf.compat.v1.Session(graph=graph)
        """
            https://www.tensorflow.org/api_docs/python/tf/compat/v1/Session
            bug compatibility tensorflow v2 version
            original v1 version: tf.gfile.FastGFile(PB_FILE, 'rb')
            v2 version: tf.compat.v1.gfile.FastGFile(PB_FILE, 'rb')
        """
        with tf.compat.v1.gfile.FastGFile(PB_FILE, 'rb') as f:
            """
                https://www.tensorflow.org/api_docs/python/tf/compat/v1/Session
                bug compatibility tensorflow v2 version
                original v1 version: graph_def = tf.GraphDef()
                v2 version: graph_def = tf.compat.v1.GraphDef()
            """
            graph_def = tf.compat.v1.GraphDef()
            graph_def.ParseFromString(f.read())
            with self.sess.graph.as_default():
                """
                    https://www.tensorflow.org/api_docs/python/tf/compat/v1/Session
                    bug compatibility tensorflow v2 version
                    original v1 version: tf.import_graph_def(graph_def)
                    v2 version: tf.graph_util.import_graph_def(graph_def)
                """
                tf.graph_util.import_graph_def(graph_def)

        self.img = graph.get_tensor_by_name("import/img:0")
        self.training = graph.get_tensor_by_name("import/training:0")
        self.dim = graph.get_tensor_by_name("import/dim:0")
        self.prob = graph.get_tensor_by_name("import/prob:0")
        self.pred = graph.get_tensor_by_name("import/pred:0")

    def load_ckpt(self):
        """
            https://www.tensorflow.org/api_docs/python/tf/compat/v1/Session
            bug compatibility tensorflow v2 version
            original v1 version: self.sess = tf.Session(graph=graph)
            v2 version: self.sess = tf.compat.v1.Session(graph=graph)
        """
        self.sess = tf.compat.v1.Session(graph=graph)
        ckpt_path = tf.train.latest_checkpoint(CHECKPOINT_DIR)
        saver = tf.train.import_meta_graph('{}.meta'.format(ckpt_path))
        saver.restore(self.sess, ckpt_path)
        """
            https://www.tensorflow.org/api_docs/python/tf/compat/v1/Session
            bug compatibility tensorflow v2 version
            original v1 version: g = tf.get_default_graph()
            v2 version: g = tf.compat.v1.get_default_graph()
        """
        g = tf.compat.v1.get_default_graph()

        self.img = g.get_tensor_by_name("img:0")
        self.training = g.get_tensor_by_name("training:0")
        self.dim = g.get_tensor_by_name("dim:0")
        self.prob = g.get_tensor_by_name("prob:0")
        self.pred = g.get_tensor_by_name("pred:0")

    def run(self, image):
        shape = image.shape
        img = resize(image, (self.SIZE, self.SIZE, self.SIZE), mode='constant', anti_aliasing=True)
        img = (img / np.max(img))
        img = np.reshape(img, [1, self.SIZE, self.SIZE, self.SIZE, 1])

        prob = self.sess.run(self.prob, feed_dict={self.training: False, self.img: img}).squeeze()
        prob = resize(prob, (shape), mode='constant', anti_aliasing=True)
        return prob


