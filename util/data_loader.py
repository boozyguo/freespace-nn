from sklearn.model_selection import train_test_split
import os, sys
import glob
import cv2
import numpy as np
import matplotlib.image as mpimg

from ..util.vis import img_stats
from ..config import Config, random_seed

from ..aug.augmentation import augment, augment2
from ..aug.patchwise import get_patch

def load_data(config = Config()):
    """
    Loads and prepares data. Returns generators for (train, test)
    """
    X_train, X_test, Y_train, Y_test = load_files(config)

    train_generator, mean, stddev = prepare_data(X_train, Y_train, config.batch_size, True, config)

    test_generator, _1, _2 = prepare_data(X_test, Y_test, config.test_batch_size, False, config)

    valid_generator, _1, _2 = prepare_data(X_test[::2], Y_test[::2], 1, True, config)

    return train_generator, test_generator, valid_generator, mean, stddev


def load_files(config = Config()):
    images = [f.split("/")[-1] for f in glob.glob(os.path.join(config.labels_location, "*.png"))]

    X = [os.path.join(config.images_location, f) for f in images]
    Y = [os.path.join(config.labels_location, f) for f in images]

    # Use 20% of the dataset for testing, 80% for training 
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=random_seed)

    return X_train, X_test, Y_train, Y_test


def prepare_data(X, Y, batch_size, augment_data, config = Config()):

    X = [mpimg.imread(x) for x in X]
    X = [preprocess_image(cv2.resize(x[int(x.shape[0] * 0.375):], config.image_size[::-1]), config = config) for x in X]

    Y = [mpimg.imread(y) for y in Y]
    Y = [preprocess_label(cv2.resize(y[int(y.shape[0] * 0.375):], config.image_size[::-1]), config = config) for y in Y]

########## NO RESIZE #######################################    
    #X = [preprocess_image(mpimg.imread(x), config = config) for x in X]
    #Y = [preprocess_label(mpimg.imread(y), config = config) for y in Y]

    print("Read all data")


    mean = np.mean(np.array(X, dtype=np.float32).flatten())
    stddev = np.std(np.array(X, dtype=np.float32).flatten())

    def gen():
        # Generate infinite amount of data
        while True:
            i = 0

            images = np.empty([batch_size, config.input_shape[0], config.input_shape[1], 3])
            images2 = np.empty([batch_size, 112, 112, 3])
            labels = np.empty([batch_size, config.input_shape[0], config.input_shape[1], 2])

            # Pick random portion of data 
            for index in np.random.permutation(len(X)):

                image = X[index]

                img2 = cv2.cvtColor(image * 255.0, cv2.COLOR_BGR2GRAY)
                x = cv2.Sobel(img2, cv2.CV_32F, 1, 0, ksize=3)
                x = cv2.convertScaleAbs(x) / 255.0
                x = x.reshape((x.shape[0], x.shape[1], 1))
                y = cv2.Sobel(img2, cv2.CV_32F, 0, 1, ksize=3)
                y = cv2.convertScaleAbs(y) / 255.0
                y = y.reshape((y.shape[0], y.shape[1], 1))
                z = cv2.Laplacian(img2, cv2.CV_32F)
                z = cv2.convertScaleAbs(z) / 255.0
                z = z.reshape((z.shape[0], z.shape[1], 1))
                image2 = np.concatenate((x, y, z), axis=2)
                image2 = cv2.resize(image2, (112, 112))

                label = Y[index]

                #image, label = get_patch(config.image_size, image, label, 0.5, 1.2)

                image, label = postprocess(image, label, config)

                images[i] = 2 * (image - 0.5)
                images2[i] = 2 * (image2 - 0.5)
                labels[i] = label

                # Limit number of images to batch_size
                i += 1
                if i == batch_size:
                    break

            if augment_data:
                images, images2, labels = augment2(images, images2, labels)

            yield [images, images2], labels

    return gen(), mean, stddev

def preprocess_image(image, config = Config()):
    #image = (image - 0.4574565) / 0.3043379 # hard-coded
    return image

def reverse_preprocess(image, config = Config()):
    #image = (image * 0.3043379) + 0.4574565 # hard-coded
    return image

def preprocess_label(label, config = Config()):
    return label

def postprocess(image, label, config = Config()):
    # TODO convert data to proper format for neural network (normalize, etc)
    label = cv2.cvtColor(label, cv2.COLOR_RGB2GRAY)[:, :, np.newaxis]
    newLabel = np.zeros([config.input_shape[0], config.input_shape[1], 2], dtype=np.float32)

    newLabel[np.where((label < 0.5).all(axis=2))] = (1, 0)
    newLabel[np.where((label > 0.5).all(axis=2))] = (0, 1)

    newImage = np.array(image, dtype=np.float32)

    return newImage, newLabel
