# -*- coding: utf-8 -*-
"""
Functions to visualize results of the growth of a graph.
"""


import os

import cv2


def plot_growth(
    folder_name,
    G_final,
    array,
    built=True,
    cmap="coolwarm",
):
    pass


def make_growth_video(img_folder_name, video_name, fps=5):
    """
    From a folder of ordered images make a video.
    """
    images = [img for img in os.listdir(img_folder_name) if img.endswith(".png")]
    # dimensions between images need to be constant
    frame = cv2.imread(os.path.join(img_folder_name, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))
    for image in images:
        video.write(cv2.imread(os.path.join(img_folder_name, image)))
    cv2.destroyAllWindows()
    video.release()
