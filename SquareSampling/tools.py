# -*- coding: utf-8 -*-

# List comprehensions in canvasMoveEvent functions are 
# adapted from Benjamin Bohard`s part of rectovaldiams plugin.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


# noinspection PyMethodMayBeStatic
class SquareFromCenterTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.rb = None
        self.xc = None
        self.yc = None
        self.mCtrl = None
        # our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                       "      c None",
                                       ".     c #FF0000",
                                       "+     c #800080",
                                       "                ",
                                       "       +.+      ",
                                       "      ++.++     ",
                                       "     +.....+    ",
                                       "    +.  .  .+   ",
                                       "   +.   .   .+  ",
                                       "  +.    .    .+ ",
                                       " ++.    .    .++",
                                       " ... ...+... ...",
                                       " ++.    .    .++",
                                       "  +.    .    .+ ",
                                       "   +.   .   .+  ",
                                       "   ++.  .  .+   ",
                                       "    ++.....+    ",
                                       "      ++.++     ",
                                       "       +.+      "]))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False

    def canvasPressEvent(self, event):
        layer = self.canvas.currentLayer()
        color = QColor(255, 0, 0)
        self.rb = QgsRubberBand(self.canvas, True)
        self.rb.setColor(color)
        self.rb.setWidth(1)
        point = self.toLayerCoordinates(layer, event.pos())
        point_map = self.toMapCoordinates(layer, point)
        xc = point_map.x()
        yc = point_map.y()

        offset = 100

        pt1 = (-offset, -offset)
        pt2 = (-offset, offset)
        pt3 = (offset, offset)
        pt4 = (offset, -offset)
        points = [pt1, pt2, pt3, pt4]

        polygon = [QgsPoint(i[0] + xc, i[1] + yc) for i in points]
        # noinspection PyCallByClass,PyArgumentList
        self.rb.setToGeometry(QgsGeometry.fromPolygon([polygon]), None)
        geom = self.rb.asGeometry()
        self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)
        self.canvas.refresh()

    # noinspection PyPep8Naming
    def showSettingsWarning(self):
        pass

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
