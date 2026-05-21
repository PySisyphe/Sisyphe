from keras import losses
from keras import optimizers
import tensorflow as tf

from .model_builder import create_off_the_shelf

def off_the_shelf_model(options):

    use_multi_gpu = options.get('parallel_gpu', False)

    if use_multi_gpu:
        strategy = tf.distribute.MirroredStrategy()
        with strategy.scope():
            model_1 = create_off_the_shelf(options)
            model_1.compile(
                optimizer=optimizers.Adadelta(),
                loss=losses.binary_crossentropy,
                metrics=['accuracy'],
            )

            model_2 = create_off_the_shelf(options)
            model_2.compile(
                optimizer=optimizers.Adadelta(),
                loss=losses.binary_crossentropy,
                metrics=['accuracy'],
            )
    else:
        model_1 = create_off_the_shelf(options)
        model_1.compile(
            optimizer=optimizers.Adadelta(),
            loss=losses.binary_crossentropy,
            metrics=['accuracy'],
        )

        model_2 = create_off_the_shelf(options)
        model_2.compile(
            optimizer=optimizers.Adadelta(),
            loss=losses.binary_crossentropy,
            metrics=['accuracy'],
        )

    return [model_1, model_2]