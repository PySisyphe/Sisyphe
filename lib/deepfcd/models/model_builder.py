from keras import backend as K
from keras import layers, models
import warnings

warnings.filterwarnings('ignore')

K.set_image_data_format('channels_first')

def off_the_shelf(input_tensor, options):
    channel_axis = 1 if K.image_data_format() == 'channels_first' else -1

    base_filters = options['base_filters']

    c1 = layers.Conv3D(
        base_filters, (3, 3, 3), padding='same',
        activation=options['activation']
    )(input_tensor)

    b1 = layers.BatchNormalization(axis=channel_axis)(c1)

    if options['dropout_mc']:
        b1 = layers.Dropout(options['dropout_1'])(b1)

    m1 = layers.MaxPooling3D((2, 2, 2))(b1)

    c2 = layers.Conv3D(
        base_filters * 2, (3, 3, 3),
        padding='same',
        activation=options['activation']
    )(m1)

    b2 = layers.BatchNormalization(axis=channel_axis)(c2)

    if options['dropout_mc']:
        b2 = layers.Dropout(options['dropout_2'])(b2)

    m2 = layers.MaxPooling3D((2, 2, 2))(b2)

    return m2

def create_off_the_shelf(options):
    nb_classes = options['nb_classes']
    channels = options['channels']
    shape = options['patch_size']

    if K.image_data_format() == 'channels_first':
        init = layers.Input((channels, *shape))
    else:
        init = layers.Input((*shape, channels))

    x = off_the_shelf(init, options)

    x = layers.Dropout(options['dropout_3'])(x)

    x = layers.Conv3D(nb_classes, (3, 3, 3), padding='same')(x)
    x = layers.MaxPooling3D((4, 4, 4))(x)

    x = layers.Flatten()(x)

    out = layers.Activation('softmax')(x)

    model = models.Model(inputs=init, outputs=out, name='off_the_shelf')

    return model
