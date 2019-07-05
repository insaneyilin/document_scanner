# -*- coding: utf-8 -*-
# @Author: yilin
# Python version: 2.7
# reference: https://github.com/lancebeet/imagemicro

import os
import sys
import argparse

from PIL import Image
from PIL import ImageTk
import Tkinter
import tkFileDialog
import numpy as np
import cv2


class SDIImageWindow(object):
    def __init__(self, master, image_filename=None):
        self.master = master
        self.origin_image = Image.new('RGB', (640,480))
        self.image = Image.new('RGB', (640,480))
        self.cv_image = None
        self.file_dir = ""
        self.filename = ""
        self.init_window_size()
        self.init_menubar()

        image_tmp = ImageTk.PhotoImage(self.image)
        self.label_image = Tkinter.Label(self.master, image=image_tmp)
        self.label_image.pack(side="bottom", fill="both", expand="yes")

        if image_filename is not None:
            self.open_file(image_filename)


    def init_window_size(self):
        self._geom='1080x720+0+0'
        pad = 3
        self.master.geometry("{0}x{1}+0+0".format(
            self.master.winfo_screenwidth() - pad,
            self.master.winfo_screenheight() - pad))
        self.master.bind('<Escape>',self.toggle_geom)


    def init_menubar(self):
        menubar = Tkinter.Menu(self.master)
        file_menu = Tkinter.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save as", command=self.save_file)
        file_menu.add_command(label="Quit", command=self.master.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        filter_menu = Tkinter.Menu(menubar, tearoff=0)
        filter_menu.add_command(label="Find Edges", command=self.edge_detect)
        menubar.add_cascade(label="Filter", menu=filter_menu)

        self.master.config(menu=menubar)


    def open_file(self, filename=None):
        if filename is None:
            filename = tkFileDialog.askopenfilename(parent=self.master,title='Choose files')
        if type(filename) is tuple or filename == "":
            return
        self.image = Image.open(filename).convert("RGB")
        self.origin_image = self.image.copy()
        print("filename: {}".format(filename))
        print("image size: [{} {}]".format(self.image.size[0], self.image.size[1]))

        self.file_dir, self.filename = os.path.split(filename)
        self.update()


    def save_file(self):
        filename = tkFileDialog.asksaveasfilename()
        if type(filename) is tuple or filename == "":
            return
        self.image.save(filename)


    def update(self):
        self.master.geometry('{}x{}'.format(self.image.size[0], self.image.size[1]))

        image_tmp = ImageTk.PhotoImage(self.image)
        self.label_image.configure(image=image_tmp)
        self.label_image.image = image_tmp

        self.master.wm_title(self.filename)


    def edge_detect(self):
        self.cv_image = cv2.cvtColor(np.asarray(self.image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(gray, 50, 100)
        self.cv_image = cv2.cvtColor(edged, cv2.COLOR_GRAY2RGB)
        self.image = Image.fromarray(self.cv_image)
        self.update()


    def toggle_geom(self, event):
        geom = self.master.winfo_geometry()
        self.master.geometry(self._geom)
        self._geom=geom


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--image', type=str, help='image filename to open',
            default=None)
    return arg_parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    image_filename = args.image

    root = Tkinter.Tk()
    image_window = SDIImageWindow(root, image_filename)
    root.mainloop()
