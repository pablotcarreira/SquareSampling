# -*- coding: utf-8 -*-

# List comprehensions in canvasMoveEvent functions are
# adapted from Benjamin Bohard`s part of rectovaldiams plugin.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from math import *
from tools.calc import *
from tools.ellipse import *
from advanced_draw_dialog import Ui_AdvancedDrawDialog



class ellipseByCenter2PointsTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self,canvas)
        self.canvas = canvas
        self.nbPoints = 0
        self.angle_exist = 0
        self.rb = None
        self.rb_axis_a, self.rb_axis_b = None, None
        self.xc, self.yc, self.x_p1, self.y_p1, self.x_p2, self.y_p2 = None, None, None, None, None, None
        self.length = 0
        self.axis_a, self.axis_b = 0,0
        self.mCtrl = None
        #our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                      "      c None",
                                      ".     c #FF0000",
                                      "+     c #1210f3",
                                      "                ",
                                      "       +.+      ",
                                      "      ++.++     ",
                                      "     +.....+    ",
                                      "    +.     .+   ",
                                      "   +.   .   .+  ",
                                      "  +.    .    .+ ",
                                      " ++.    .    .++",
                                      " ... ...+... ...",
                                      " ++.    .    .++",
                                      "  +.    .    .+ ",
                                      "   +.   .   .+  ",
                                      "   ++.     .+   ",
                                      "    ++.....+    ",
                                      "      ++.++     ",
                                      "       +.+      "]))


    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True


    def keyReleaseEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False

    def calcPoint(x,y):
        return p.x() + self.length * cos(radians(90) + self.angle_exist), self.p.y() + self.length * sin(radians(90) + self.angle_exist)

    def canvasPressEvent(self,event):
        layer = self.canvas.currentLayer()
        if self.nbPoints == 0:
            color = QColor(255,0,0)
            self.rb = QgsRubberBand(self.canvas, True)
            self.rb.setColor(color)
            self.rb.setWidth(1)

            self.rb_axis_a = QgsRubberBand(self.canvas, False)
            self.rb_axis_b = QgsRubberBand(self.canvas, False)
            self.rb_axis_a.setColor(QColor(0,0,255))
            self.rb_axis_b.setColor(QColor(0,0,255))
            self.rb_axis_a.setWidth(1)
            self.rb_axis_b.setWidth(1)
        elif self.nbPoints == 2:
            self.rb.reset(True)
            self.rb_axis_a.reset(True)
            self.rb_axis_b.reset(True)
            self.rb, self.rb_axis_a, self.rb_axis_b = None, None, None

            self.canvas.refresh()

        x = event.pos().x()
        y = event.pos().y()
        if self.mCtrl:
            startingPoint = QPoint(x,y)
            snapper = QgsMapCanvasSnapper(self.canvas)
            (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)
            if result <> []:
                point = result[0].snappedVertex
            else:
                (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
                if result <> []:
                    point = result[0].snappedVertex
                else:
                    point = self.toLayerCoordinates(layer,event.pos())
        else:
            point = self.toLayerCoordinates(layer,event.pos())
        pointMap = self.toMapCoordinates(layer, point)

        if self.nbPoints == 0:
            self.xc = pointMap.x()
            self.yc = pointMap.y()
        elif self.nbPoints == 1:
            self.x_p1 = pointMap.x()
            self.y_p1 = pointMap.y()
            self.angle_exist = calcAngleExistant(QgsPoint(self.xc, self.yc), QgsPoint(self.x_p1, self.y_p1))
            self.axis_a = QgsDistanceArea().measureLine(QgsPoint(self.xc, self.yc), QgsPoint(self.x_p1, self.y_p1))
            self.rb_axis_a.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(self.xc, self.yc), QgsPoint(self.x_p1, self.y_p1)]), None)
        else:
            self.x_p2, self.y_p2 = self.xc + self.length * cos(radians(90) + self.angle_exist), self.yc + self.length * sin(radians(90) + self.angle_exist)
            self.axis_b = QgsDistanceArea().measureLine(QgsPoint(self.xc, self.yc), QgsPoint(self.x_p2, self.y_p2))


        self.nbPoints += 1

        if self.nbPoints == 3:
            #segments = settings.value("/RectOvalDigit/segments",36,type=int)
            segments = 360
            points = []
            for t in [(2*pi)/segments*i for i in range(segments)]:
                points.append((self.xc + self.axis_a*cos(t)*cos(self.angle_exist) - self.axis_b*sin(t)*sin(self.angle_exist), self.yc + self.axis_a*cos(t)*sin(self.angle_exist) + self.axis_b*sin(t)*cos(self.angle_exist)))
            polygon = [QgsPoint(i[0],i[1]) for i in points]
            geom = QgsGeometry.fromPolygon([polygon])

            self.nbPoints = 0
            self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.xc, self.yc = None, None, None, None, None, None

            self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)

        if self.rb:return

    def canvasMoveEvent(self,event):

        if not self.rb:return
        currpoint = self.toMapCoordinates(event.pos())
        currx = currpoint.x()
        curry = currpoint.y()
        if self.nbPoints == 1:
            self.rb_axis_a.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(self.xc, self.yc), QgsPoint(currx, curry)]), None)
        if self.nbPoints >= 2:
            self.length = QgsDistanceArea().measureLine(QgsPoint(self.xc, self.yc), QgsPoint(currx, curry))
            self.x_p2, self.y_p2 = self.xc + self.length * cos(radians(90) + self.angle_exist), self.yc + self.length * sin(radians(90) + self.angle_exist)
            self.axis_b = QgsDistanceArea().measureLine(QgsPoint(self.xc, self.yc), QgsPoint(self.x_p2, self.y_p2))
           #segments = settings.value("/RectOvalDigit/segments",36,type=int)
            segments = 360
            points = []
            for t in [(2*pi)/segments*i for i in range(segments)]:
                points.append((self.xc + self.axis_a*cos(t)*cos(self.angle_exist) - self.axis_b*sin(t)*sin(self.angle_exist), self.yc + self.axis_a*cos(t)*sin(self.angle_exist) + self.axis_b*sin(t)*cos(self.angle_exist)))
            polygon = [QgsPoint(i[0],i[1]) for i in points]
            geom = QgsGeometry.fromPolygon([polygon])
            self.rb_axis_b.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(self.xc, self.yc), QgsPoint(self.x_p2, self.y_p2)]),None)

            self.rb.setToGeometry(geom, None)

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


class ellipseByCenter3PointsTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self,canvas)
        self.canvas = canvas
        self.nbPoints = 0
        self.rb = None
        self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.x_p3, self.y_p3, self.x_p4, self.y_p4 = None, None, None, None, None, None, None, None
        self.length = 0
        self.mCtrl = None
        #our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                      "      c None",
                                      ".     c #FF0000",
                                      "+     c #1210f3",
                                      "                ",
                                      "       +.+      ",
                                      "      ++.++     ",
                                      "     +.....+    ",
                                      "    +.     .+   ",
                                      "   +.   .   .+  ",
                                      "  +.    .    .+ ",
                                      " ++.    .    .++",
                                      " ... ...+... ...",
                                      " ++.    .    .++",
                                      "  +.    .    .+ ",
                                      "   +.   .   .+  ",
                                      "   ++.     .+   ",
                                      "    ++.....+    ",
                                      "      ++.++     ",
                                      "       +.+      "]))


    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True


    def keyReleaseEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False

    def calcPoint(x,y):
        return p.x() + self.length * cos(radians(90) + self.angle_exist), self.p.y() + self.length * sin(radians(90) + self.angle_exist)

    def canvasPressEvent(self,event):
        layer = self.canvas.currentLayer()
        if self.nbPoints == 0:
            color = QColor(255,0,0)
            self.rb = QgsRubberBand(self.canvas, True)
            self.rb.setColor(color)
            self.rb.setWidth(1)
        elif self.nbPoints == 2:
            self.rb.reset(True)
            self.rb=None

            self.canvas.refresh()

        x = event.pos().x()
        y = event.pos().y()
        if self.mCtrl:
            startingPoint = QPoint(x,y)
            snapper = QgsMapCanvasSnapper(self.canvas)
            (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)
            if result <> []:
                point = result[0].snappedVertex
            else:
                (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
                if result <> []:
                    point = result[0].snappedVertex
                else:
                    point = self.toLayerCoordinates(layer,event.pos())
        else:
            point = self.toLayerCoordinates(layer,event.pos())
        pointMap = self.toMapCoordinates(layer, point)

        if self.nbPoints == 0:
            self.x_p1 = pointMap.x()
            self.y_p1 = pointMap.y()
        elif self.nbPoints == 1:
            self.x_p2 = pointMap.x()
            self.y_p2 = pointMap.y()
            self.angle_exist = calcAngleExistant(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2))
        else:
            self.x_p3, self.y_p3 = self.x_p2 + self.length * cos(radians(90) + self.angle_exist), self.y_p2 + self.length * sin(radians(90) + self.angle_exist)
            self.x_p4, self.y_p4 = self.x_p1 + self.length * cos(radians(90) + self.angle_exist), self.y_p1 + self.length * sin(radians(90) + self.angle_exist)


        self.nbPoints += 1

        if self.nbPoints == 3:
            geom = QgsGeometry.fromPolygon([[QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), QgsPoint(self.x_p3, self.y_p3), QgsPoint(self.x_p4, self.y_p4)]])

            self.nbPoints = 0
            self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.x_p3, self.y_p3, self.x_p4, self.y_p4 = None, None, None, None, None, None, None, None

            self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)

        if self.rb:return

    def canvasMoveEvent(self,event):

        if not self.rb:return
        currpoint = self.toMapCoordinates(event.pos())
        currx = currpoint.x()
        curry = currpoint.y()
        if self.nbPoints == 1:
            self.rb.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(self.x_p1, self.y_p1), QgsPoint(currx, curry)]), None)
        if self.nbPoints >= 2:
            side = calc_isCollinear(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), currpoint) # check if x_p2 > x_p1 and inverse side
            if self.x_p1 < self.x_p2:
                side *= -1
            self.length = QgsDistanceArea().measureLine(QgsPoint(self.x_p2, self.y_p2), QgsPoint(currx, curry)) * side
            self.x_p3, self.y_p3 = self.x_p2 + self.length * cos(radians(90) + self.angle_exist), self.y_p2 + self.length * sin(radians(90) + self.angle_exist)
            self.x_p4, self.y_p4 = self.x_p1 + self.length * cos(radians(90) + self.angle_exist), self.y_p1 + self.length * sin(radians(90) + self.angle_exist)
            geom = QgsGeometry.fromPolygon([[QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), QgsPoint(self.x_p3, self.y_p3), QgsPoint(self.x_p4, self.y_p4)]])
            self.rb.setToGeometry(geom, None)

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


class ellipseBy4PointsTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self,canvas)
        self.canvas = canvas
        self.nbPoints = 0
        self.rb = None
        self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.x_p3, self.y_p3, self.x_p4, self.y_p4 = None, None, None, None, None, None, None, None
        self.length = 0
        self.mCtrl = None
        #our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                      "      c None",
                                      ".     c #FF0000",
                                      "+     c #1210f3",
                                      "                ",
                                      "       +.+      ",
                                      "      ++.++     ",
                                      "     +.....+    ",
                                      "    +.     .+   ",
                                      "   +.   .   .+  ",
                                      "  +.    .    .+ ",
                                      " ++.    .    .++",
                                      " ... ...+... ...",
                                      " ++.    .    .++",
                                      "  +.    .    .+ ",
                                      "   +.   .   .+  ",
                                      "   ++.     .+   ",
                                      "    ++.....+    ",
                                      "      ++.++     ",
                                      "       +.+      "]))


    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True


    def keyReleaseEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False

    def calcPoint(x,y):
        return p.x() + self.length * cos(radians(90) + self.angle_exist), self.p.y() + self.length * sin(radians(90) + self.angle_exist)

    def canvasPressEvent(self,event):
        layer = self.canvas.currentLayer()
        if self.nbPoints == 0:
            color = QColor(255,0,0)
            self.rb = QgsRubberBand(self.canvas, True)
            self.rb.setColor(color)
            self.rb.setWidth(1)
        elif self.nbPoints == 2:
            self.rb.reset(True)
            self.rb=None

            self.canvas.refresh()

        x = event.pos().x()
        y = event.pos().y()
        if self.mCtrl:
            startingPoint = QPoint(x,y)
            snapper = QgsMapCanvasSnapper(self.canvas)
            (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)
            if result <> []:
                point = result[0].snappedVertex
            else:
                (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
                if result <> []:
                    point = result[0].snappedVertex
                else:
                    point = self.toLayerCoordinates(layer,event.pos())
        else:
            point = self.toLayerCoordinates(layer,event.pos())
        pointMap = self.toMapCoordinates(layer, point)

        if self.nbPoints == 0:
            self.x_p1 = pointMap.x()
            self.y_p1 = pointMap.y()
        elif self.nbPoints == 1:
            self.x_p2 = pointMap.x()
            self.y_p2 = pointMap.y()
            self.angle_exist = calcAngleExistant(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2))
        else:
            self.x_p3, self.y_p3 = self.x_p2 + self.length * cos(radians(90) + self.angle_exist), self.y_p2 + self.length * sin(radians(90) + self.angle_exist)
            self.x_p4, self.y_p4 = self.x_p1 + self.length * cos(radians(90) + self.angle_exist), self.y_p1 + self.length * sin(radians(90) + self.angle_exist)


        self.nbPoints += 1

        if self.nbPoints == 3:
            geom = QgsGeometry.fromPolygon([[QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), QgsPoint(self.x_p3, self.y_p3), QgsPoint(self.x_p4, self.y_p4)]])

            self.nbPoints = 0
            self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.x_p3, self.y_p3, self.x_p4, self.y_p4 = None, None, None, None, None, None, None, None

            self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)

        if self.rb:return

    def canvasMoveEvent(self,event):

        if not self.rb:return
        currpoint = self.toMapCoordinates(event.pos())
        currx = currpoint.x()
        curry = currpoint.y()
        if self.nbPoints == 1:
            self.rb.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(self.x_p1, self.y_p1), QgsPoint(currx, curry)]), None)
        if self.nbPoints >= 2:
            side = calc_isCollinear(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), currpoint) # check if x_p2 > x_p1 and inverse side
            if self.x_p1 < self.x_p2:
                side *= -1
            self.length = QgsDistanceArea().measureLine(QgsPoint(self.x_p2, self.y_p2), QgsPoint(currx, curry)) * side
            self.x_p3, self.y_p3 = self.x_p2 + self.length * cos(radians(90) + self.angle_exist), self.y_p2 + self.length * sin(radians(90) + self.angle_exist)
            self.x_p4, self.y_p4 = self.x_p1 + self.length * cos(radians(90) + self.angle_exist), self.y_p1 + self.length * sin(radians(90) + self.angle_exist)
            geom = QgsGeometry.fromPolygon([[QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), QgsPoint(self.x_p3, self.y_p3), QgsPoint(self.x_p4, self.y_p4)]])
            self.rb.setToGeometry(geom, None)

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


class ellipseByFociPointTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self,canvas)
        self.canvas = canvas
        self.nbPoints = 0
        self.rb = None
        self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.x_p3, self.y_p3 = None, None, None, None, None, None # P1 and P2 are foci
        self.distP1P3, self.distP2P3 = 0,0
        self.distTotal = 0
        self.angle_exist = 0
        self.mCtrl = None
        #our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                      "      c None",
                                      ".     c #FF0000",
                                      "+     c #1210f3",
                                      "                ",
                                      "       +.+      ",
                                      "      ++.++     ",
                                      "     +.....+    ",
                                      "    +.     .+   ",
                                      "   +.   .   .+  ",
                                      "  +.    .    .+ ",
                                      " ++.    .    .++",
                                      " ... ...+... ...",
                                      " ++.    .    .++",
                                      "  +.    .    .+ ",
                                      "   +.   .   .+  ",
                                      "   ++.     .+   ",
                                      "    ++.....+    ",
                                      "      ++.++     ",
                                      "       +.+      "]))


    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True


    def keyReleaseEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False

    def canvasPressEvent(self,event):
        layer = self.canvas.currentLayer()
        if self.nbPoints == 0:
            color = QColor(255,0,0)
            self.rb = QgsRubberBand(self.canvas, True)
            self.rb.setColor(color)
            self.rb.setWidth(1)
        elif self.nbPoints == 2:
            self.rb.reset(True)
            self.rb=None

            self.canvas.refresh()

        x = event.pos().x()
        y = event.pos().y()
        if self.mCtrl:
            startingPoint = QPoint(x,y)
            snapper = QgsMapCanvasSnapper(self.canvas)
            (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)
            if result <> []:
                point = result[0].snappedVertex
            else:
                (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
                if result <> []:
                    point = result[0].snappedVertex
                else:
                    point = self.toLayerCoordinates(layer,event.pos())
        else:
            point = self.toLayerCoordinates(layer,event.pos())
        pointMap = self.toMapCoordinates(layer, point)

        if self.nbPoints == 0:
            self.x_p1 = pointMap.x()
            self.y_p1 = pointMap.y()
        elif self.nbPoints == 1:
            self.x_p2 = pointMap.x()
            self.y_p2 = pointMap.y()
            self.angle_exist = calcAngleExistant(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2))
        else:
            self.x_p3 = pointMap.x()
            self.y_p3 = pointMap.y()

        self.nbPoints += 1

        if self.nbPoints == 3:
            geom = ellipseFromFoci(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), QgsPoint(self.x_p3, self.y_p3))
            self.nbPoints = 0
            self.x_p1, self.y_p1, self.x_p2, self.y_p2, self.x_p3, self.y_p3 = None, None, None, None, None, None

            self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)

        if self.rb:return


    def canvasMoveEvent(self,event):

        if not self.rb:return
        currpoint = self.toMapCoordinates(event.pos())
        currx = currpoint.x()
        curry = currpoint.y()
        if self.nbPoints == 1:
            self.rb.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(self.x_p1, self.y_p1), QgsPoint(currx, curry)]), None)

        if self.nbPoints >= 2:
            self.rb.setToGeometry(ellipseFromFoci(QgsPoint(self.x_p1, self.y_p1), QgsPoint(self.x_p2, self.y_p2), QgsPoint(currx, curry)), None)

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


