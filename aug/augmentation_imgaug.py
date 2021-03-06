### IMGAUG NONFUNCTIONAL
import cv2
import numpy as np
from imgaug import augmenters as ia
import imgaug as iaa
from imgaug.parameters import Normal as Norm
from imgaug.parameters import Negative


"""
Augumentations:
    - Brightness
    - ContrastNormalization

    - Dropout
    - Salt & Pepper
    - AverageBlur
    - Superpixels
    - AdditiveGaussianNoise

    - Fliplr
    - Affine (reflect)
        - Translate
        - Shear (small)
"""

aug_none = ia.Sequential([
    ia.Noop()
])

# No change to labels
aug_noise_light = ia.Sequential([
    ia.SomeOf((0, 1), [
        ia.AverageBlur(k=((1, 2), (1, 2))),
    ]),
    #ia.Dropout((0.003, 0.009), per_channel=0.5)
])

# No change to labels
aug_color_light = ia.Sequential([
    #ia.Multiply(1.0) # Brightness
    #ia.ContrastNormalization(Norm(1.0, 0.04))
])

# Labels need to be altered in same way (only works for segmentation)
aug_geo_light = ia.Sequential([
    ia.Fliplr(0.5),
    #ia.Flipud(0.2),
    ia.Affine(scale=Norm(1.0, 0.055), translate_percent=Norm(0.0, 0.035), rotate=Norm(0.0, 2.0), shear=Norm(0.0, 3.0), mode="reflect")
])

def combine_aug(*augs):
    arr = []
    for aug in augs:
        arr.append(aug)
    return ia.Sequential(arr)

geo = aug_geo_light
noise = combine_aug(aug_noise_light, aug_color_light)

def augment(images, labels):
    images = np.array(images) * 255.0
    det = geo.to_deterministic()
    out = det.augment_images(images)
    out = noise.augment_images(np.array(out)) / 255.0

    labels = np.array(labels) * 255.0
    out2 = det.augment_images(labels) / 255.0
    out2[out2 > 0.5] = 1.0
    out2[out2 <= 0.5] = 0.0

    return out, out2

def augment2(images, images2, labels):
    images = np.array(images) * 255.0
    det = geo.to_deterministic()
    out = det.augment_images(images)
    out = noise.augment_images(np.array(out)) / 255.0

    labels = np.array(labels) * 255.0
    out2 = det.augment_images(labels) / 255.0
    out2[out2 > 0.5] = 1.0
    out2[out2 <= 0.5] = 0.0

    images2 = np.array(np.array(images2) * 255.0, dtype=np.uint8)
    out1 = det.augment_images(images2) / 255.0

    return out, out1, out2

