# -*- coding: utf-8 -*-
# @Author: yilin
# Python version: 2.7
# GUI reference: https://github.com/lancebeet/imagemicro

import os
import sys
import math
import argparse

from PIL import Image
from PIL import ImageTk

import Tkinter
import tkFileDialog

import numpy as np
import cv2

from doc_scanner import (
    get_document_corners,
    apply_four_point_perspective_transform
)


class DocScannerWindow(object):
    def __init__(self, master, image_filename=None):
        self.master = master
        self.origin_image = Image.new('RGB', (640,480), (255, 255, 255))
        self.image = Image.new('RGB', (640,480), (255, 255, 255))
        self.cv_image = None
        self.warped_image = None
        self.file_dir = ""
        self.filename = ""
        self.init_window_size()
        self.init_menubar()

        # for select doc corners
        self.enable_select_corner = False
        self.selected_corner_idx = -1
        self.drawed_lines = [None]*4

        self.image_tmp = ImageTk.PhotoImage(self.image)

        # init four corners of the document
        self.canvas = Tkinter.Canvas(self.master,
                width=self.master.winfo_screenwidth(),
                height=self.master.winfo_screenheight(),
                bd=0, highlightthickness=0)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=Tkinter.NW,
                image=self.image_tmp)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.pack()
        self.paint_ovals = [
                self.canvas.create_oval(0, 0, 0, 0, outline="#f11", fill="#1f1"),
                self.canvas.create_oval(0, 0, 0, 0, outline="#f11", fill="#1f1"),
                self.canvas.create_oval(0, 0, 0, 0, outline="#f11", fill="#1f1"),
                self.canvas.create_oval(0, 0, 0, 0, outline="#f11", fill="#1f1")]

        self.master.bind("<ButtonPress-1>", self.on_left_click)

        if image_filename is not None:
            self.open_file(image_filename)


    def init_window_size(self):
        self._geom='1080x720+0+0'
        pad = 0
        self.master.geometry("{0}x{0}+0+0".format(
                self.master.winfo_screenwidth() - pad,
                self.master.winfo_screenheight() - pad))
        self.master.resizable(False, False)  # disable resizing


    def init_menubar(self):
        menubar = Tkinter.Menu(self.master)
        file_menu = Tkinter.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save as", command=self.save_file)
        file_menu.add_command(label="Export to PDF", command=self.export2pdf)
        file_menu.add_command(label="Quit", command=self.master.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        filter_menu = Tkinter.Menu(menubar, tearoff=0)
        filter_menu.add_command(label="Find Edges", command=self.edge_detect)
        filter_menu.add_command(label="Image Binarization", command=self.image_binarization)
        filter_menu.add_command(label="Restore Image", command=self.restore_image)
        menubar.add_cascade(label="Filter", menu=filter_menu)

        transform_menu = Tkinter.Menu(menubar, tearoff=0)
        transform_menu.add_command(label="Detect Contour", command=self.detect_contour)
        transform_menu.add_command(label="Apply Perspective Transform",
                command=self.apply_perspective_transform)
        menubar.add_cascade(label="Document Scan", menu=transform_menu)

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
        pad = 10
        image_w = self.image.size[0]
        image_h = self.image.size[1]
        self.doc_corners = [[pad, pad],
                [image_w - pad, pad],
                [image_w - pad, image_h - pad],
                [pad, image_h - pad]]
        self.update()


    def save_file(self):
        filename = tkFileDialog.asksaveasfilename()
        if type(filename) is tuple or filename == "":
            return
        self.image.save(filename)


    def export2pdf(self):
        filename = tkFileDialog.asksaveasfilename()
        if type(filename) is tuple or filename == "":
            return
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        self.image.save(filename)


    def update(self):
        self.master.geometry('{}x{}'.format(self.image.size[0], self.image.size[1]))

        self.image_tmp = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfig(self.image_on_canvas, image=self.image_tmp)

        for oval, corner in zip(self.paint_ovals, self.doc_corners):
            x, y = corner[0], corner[1]
            self.canvas.coords(oval, x-5, y-5, x+5, y+5)
        for idx, corner in enumerate(self.doc_corners):
            next_idx = (idx+1) % len(self.doc_corners)
            next_corner = self.doc_corners[next_idx]
            if self.drawed_lines[idx] is not None:
                self.canvas.delete(self.drawed_lines[idx])
            self.drawed_lines[idx] = self.canvas.create_line(corner[0], corner[1],
                    next_corner[0], next_corner[1],
                    dash=(4, 2), fill="#05f")

        self.master.wm_title(self.filename)


    def edge_detect(self):
        self.cv_image = cv2.cvtColor(np.asarray(self.image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(gray, 50, 100)
        self.cv_image = cv2.cvtColor(edged, cv2.COLOR_GRAY2RGB)
        self.image = Image.fromarray(self.cv_image)
        self.update()


    def image_binarization(self):
        self.cv_image = cv2.cvtColor(np.asarray(self.image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
        ret, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        self.cv_image = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2RGB)
        self.image = Image.fromarray(self.cv_image)
        self.update()


    def restore_image(self):
        self.image = self.origin_image.copy()
        self.update()


    def detect_contour(self):
        self.cv_image = cv2.cvtColor(np.asarray(self.image), cv2.COLOR_RGB2BGR)
        corners = get_document_corners(self.cv_image)
        if len(corners) == 4:
            self.doc_corners = [[pt[0], pt[1]] for pt in corners]
        self.update()


    def apply_perspective_transform(self):
        self.cv_image = cv2.cvtColor(np.asarray(self.image), cv2.COLOR_RGB2BGR)
        self.warped_image = apply_four_point_perspective_transform(self.cv_image,
                np.array(self.doc_corners))
        self.cv_image = cv2.cvtColor(self.warped_image, cv2.COLOR_BGR2RGB)
        self.image = Image.fromarray(self.cv_image)
        image_w = self.image.size[0]
        image_h = self.image.size[1]
        self.doc_corners = [[0, 0],
                [image_w, 0],
                [image_w, image_h],
                [0, image_h]]
        self.update()


    def on_mouse_move(self, event):
        x, y = event.x, event.y
        if self.enable_select_corner:
            self.doc_corners[self.selected_corner_idx] = [x, y]
            self.update()


    def on_left_click(self, event):
        # print("({}, {}) clicked".format(event.x, event.y))
        if self.enable_select_corner:
            self.enable_select_corner = False
            self.selected_corner_idx = -1
            return
        x, y = event.x, event.y
        for idx, corner in enumerate(self.doc_corners):
            if math.hypot(x-corner[0], y-corner[1]) < 10:
                self.selected_corner_idx = idx
                self.enable_select_corner = True
                break


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--image', type=str, help='input image filename',
            default=None)
    return arg_parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    image_filename = args.image

    root = Tkinter.Tk()
    doc_scan_window = DocScannerWindow(root, image_filename)
    root.mainloop()
