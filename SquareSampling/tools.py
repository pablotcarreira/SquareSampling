# -*- coding: utf-8 -*-

# List comprehensions in canvasMoveEvent functions are 
# adapted from Benjamin Bohard`s part of rectovaldiams plugin.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import math


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
        x = event.pos().x()
        y = event.pos().y()
        if self.mCtrl:
            startingPoint = QPoint(x, y)
            snapper = QgsMapCanvasSnapper(self.canvas)
            (retval, result) = snapper.snapToCurrentLayer(startingPoint, QgsSnapper.SnapToVertex)
            if result != []:
                point = result[0].snappedVertex
            else:
                (retval, result) = snapper.snapToBackgroundLayers(startingPoint)
                if result != []:
                    point = result[0].snappedVertex
                else:
                    point = self.toLayerCoordinates(layer, event.pos())
        else:
            point = self.toLayerCoordinates(layer, event.pos())
        pointMap = self.toMapCoordinates(layer, point)
        self.xc = pointMap.x()
        self.yc = pointMap.y()
        if self.rb: return

    def canvasMoveEvent(self, event):
        if not self.rb: return
        currpoint = self.toMapCoordinates(event.pos())
        distance = math.sqrt(currpoint.sqrDist(self.xc, self.yc))
        offset = distance / math.sqrt(2)
        self.rb.reset(True)
        pt1 = (-offset, -offset)
        pt2 = (-offset, offset)
        pt3 = (offset, offset)
        pt4 = (offset, -offset)
        points = [pt1, pt2, pt3, pt4]
        polygon = [QgsPoint(i[0] + self.xc, i[1] + self.yc) for i in points]
        # delete [self.rb.addPoint( point ) for point in polygon]
        self.rb.setToGeometry(QgsGeometry.fromPolygon([polygon]), None)

    def canvasReleaseEvent(self, event):
        if not self.rb: return
        if self.rb.numberOfVertices() > 2:
            geom = self.rb.asGeometry()
            self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)

        self.rb.reset(True)
        self.rb = None

        self.canvas.refresh()

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
