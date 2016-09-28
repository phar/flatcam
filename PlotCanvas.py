############################################################
# FlatCAM: 2D Post-processing for Manufacturing            #
# http://caram.cl/software/flatcam                         #
# Author: Juan Pablo Caram (c)                             #
# Date: 2/5/2014                                           #
# MIT Licence                                              #
############################################################

from PyQt4 import QtCore

import logging
from VisPyCanvas import VisPyCanvas
from VisPyVisuals import ShapeGroup, ShapeCollection, TextCollection, TextGroup, Cursor
from vispy.scene.visuals import InfiniteLine
import numpy as np
from vispy.geometry import Rect

log = logging.getLogger('base')


class PlotCanvas(QtCore.QObject, VisPyCanvas):
    """
    Class handling the plotting area in the application.
    """

    def __init__(self, container, fcapp):
        """
        The constructor configures the Matplotlib figure that
        will contain all plots, creates the base axes and connects
        events to the plotting area.

        :param container: The parent container in which to draw plots.
        :rtype: PlotCanvas
        """

        super(PlotCanvas, self).__init__()

        VisPyCanvas.__init__(self)

        # VisPyCanvas does not allow new attributes. Override.
        self.unfreeze()

        # self.app collides with VispyCanvas.app
        # Renamed to fcapp.
        self.fcapp = fcapp

        # Parent container <QtCore.QObject>
        self.container = container

        # <VisPyCanvas>
        self.create_native()
        self.native.setParent(self.fcapp.ui)

        # <QtCore.QObject>
        self.container.addWidget(self.native)

        self.vline = InfiniteLine(pos=0, color=(0.0, 0.0, 0.0, 1.0), vertical=True,
                                  parent=self.view.scene)

        self.hline = InfiniteLine(pos=0, color=(0.0, 0.0, 0.0, 1.0), vertical=False,
                                  parent=self.view.scene)

        self.shape_collection = self.new_shape_collection()
        self.fcapp.pool_recreated.connect(self.on_pool_recreated)
        self.text_collection = self.new_text_collection()

        # TODO: Should be setting to show/hide CNC job annotations (global or per object)
        self.text_collection.enabled = False

        # Keep VisPy canvas happy by letting it be "frozen" again.
        # Why the heck is this needed???
        self.freeze()

    def vis_connect(self, event_name, callback):
        return getattr(self.events, event_name).connect(callback)

    def vis_disconnect(self, event_name, callback):
        getattr(self.events, event_name).disconnect(callback)

    def zoom(self, factor, center=None):
        """
        Zooms the plot by factor around a given
        center point. Takes care of re-drawing.

        :param factor: Number by which to scale the plot.
        :type factor: float
        :param center: Coordinates [x, y] of the point around which to scale the plot.
        :type center: list
        :return: None
        """
        self.view.camera.zoom(factor, center)

    def new_shape_group(self):
        """
        Used by every FlatCAMObject to create their own shape
        group attached to this Canvas.

        :return:
        """
        return ShapeGroup(self.shape_collection)

    def new_shape_collection(self, **kwargs):
        """
        Creates a ShapeCollection with parent and pool of this PlotCanvas.

        Used in the constructor and in FlatCAMDraw.__init__().

        :param kwargs:
        :return:
        """

        return ShapeCollection(parent=self.view.scene, pool=self.fcapp.pool, **kwargs)

    def new_cursor(self):
        """
        Know usage:
          * FlatCAMDraw.__init__()

        :return: A Cursor attached to this Canvas.
        """

        c = Cursor(pos=np.empty((0, 2)), parent=self.view.scene)
        c.antialias = 0
        return c

    def new_text_group(self):
        return TextGroup(self.text_collection)

    def new_text_collection(self, **kwargs):
        return TextCollection(parent=self.view.scene, **kwargs)

    def fit_view(self, rect=None):

        # Lock updates in other threads
        self.shape_collection.lock_updates()

        if not rect:
            rect = Rect(0, 0, 10, 10)
            try:
                rect.left, rect.right = self.shape_collection.bounds(axis=0)
                rect.bottom, rect.top = self.shape_collection.bounds(axis=1)
            except TypeError:
                pass

        self.view.camera.rect = rect

        self.shape_collection.unlock_updates()

    def clear(self):
        pass

    def redraw(self):
        """
        Call all collections' redraw() method.

        :return: None
        """
        self.shape_collection.redraw([])
        self.text_collection.redraw()

    def on_pool_recreated(self, pool):
        self.shape_collection.pool = pool
