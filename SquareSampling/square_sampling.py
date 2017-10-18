# coding: utf-8
# -----------------------------------------------------------
# 
# Square Sampling
# Copyright (C) 2017 Pablo Carreira
#
# Code adopted/adapted from:
#  RectangleOval Plugin (Pavol Kapusta) : https://github.com/vinayan/RectOvalDigitPlugin
#
# -----------------------------------------------------------
# 
# licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
# ---------------------------------------------------------------------


from qgis.core import *

# Import the PyQt and the QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import own classes and tools
from tools import SquareFromCenterTool


# initialize Qt resources from file resources.py


# Our main class for the plugin
class SquareSampling:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

    def initGui(self):
        settings = QSettings()
        # Add button
        self.toolBar = self.iface.addToolBar("Square Sampling")
        self.toolBar.setObjectName("SquareSampling")

        # Add actions
        self.squarefromcenter = QAction(QIcon(":/plugins/SquareSampling/icons/squarefromcenter.png"),
                                        "Square from center", self.iface.mainWindow())
        self.toolBar.addActions([self.squarefromcenter])
        self.squarefromcenter.setCheckable(True)
        self.squarefromcenter.setEnabled(False)
        self.toolBar.addSeparator()

        # Add spinbox - vai ser utilizado para determinar o tamanho do ratângulo.
        self.spinBox = QSpinBox(self.iface.mainWindow())
        self.spinBox.setMinimum(3)
        self.spinBox.setMaximum(72)
        segvalue = settings.value("/RectOvalDigit/segments", 36, type=int)
        if not segvalue:
            settings.setValue("/RectOvalDigit/segments", 36)
        self.spinBox.setValue(segvalue)
        self.spinBox.setSingleStep(1)
        self.spinBoxAction = self.toolBar.addWidget(self.spinBox)
        self.spinBox.setToolTip("Square size in map units")
        self.spinBoxAction.setEnabled(False)

        # Connect to signals for button behaviour
        QObject.connect(self.squarefromcenter, SIGNAL("activated()"), self.squarefromcenterdigit)
        QObject.connect(self.spinBox, SIGNAL("valueChanged(int)"), self.segmentsettings)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer*)"), self.toggle)
        QObject.connect(self.canvas, SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)

        # Get the tools
        self.squarefromcentertool = SquareFromCenterTool(self.canvas)

    def squarefromcenterdigit(self):
        self.canvas.setMapTool(self.squarefromcentertool)
        self.squarefromcenter.setChecked(True)
        QObject.connect(self.squarefromcentertool, SIGNAL("rbFinished(PyQt_PyObject)"), self.createFeature)

    def selectionchanged(self):
        raise RuntimeError("Selecao alterada")

    def segmentsettings(self):
        settings = QSettings()
        settings.setValue("/RectOvalDigit/segments", self.spinBox.value())

    def toggle(self):
        mc = self.canvas
        layer = mc.currentLayer()
        # Decide whether the plugin button/menu is enabled or disabled
        if layer is not None:
            if layer.isEditable() and layer.geometryType() == 2:
                self.squarefromcenter.setEnabled(True)
                self.spinBoxAction.setEnabled(True)
                QObject.connect(layer, SIGNAL("editingStopped()"), self.toggle)
                QObject.disconnect(layer, SIGNAL("editingStarted()"), self.toggle)
            else:
                self.squarefromcenter.setEnabled(False)
                self.spinBoxAction.setEnabled(False)
                QObject.connect(layer, SIGNAL("editingStarted()"), self.toggle)
                QObject.disconnect(layer, SIGNAL("editingStopped()"), self.toggle)

    def deactivate(self):
        self.squarefromcenter.setChecked(False)
        QObject.disconnect(self.squarefromcentertool, SIGNAL("rbFinished(PyQt_PyObject)"), self.createFeature)

    def createFeature(self, geom):
        settings = QSettings()
        mc = self.canvas
        layer = mc.currentLayer()
        renderer = mc.mapRenderer()
        layerCRSSrsid = layer.crs().srsid()
        projectCRSSrsid = renderer.destinationCrs().srsid()
        provider = layer.dataProvider()
        f = QgsFeature()

        # On the Fly reprojection.
        if layerCRSSrsid != projectCRSSrsid:
            geom.transform(QgsCoordinateTransform(projectCRSSrsid, layerCRSSrsid))

        f.setGeometry(geom)

        # add attribute fields to feature
        fields = layer.pendingFields()

        # vector api change update

        f.initAttributes(fields.count())
        for i in range(fields.count()):
            f.setAttribute(i, provider.defaultValue(i))

        if not (settings.value("/qgis/digitizing/disable_enter_attribute_values_dialog")):
            self.iface.openFeatureForm(layer, f, False)

        layer.beginEditCommand("Feature added")
        layer.addFeature(f)
        layer.endEditCommand()

    def changegeom(self, result):
        mc = self.canvas
        layer = mc.currentLayer()
        renderer = mc.mapRenderer()
        layerCRSSrsid = layer.crs().srsid()
        projectCRSSrsid = renderer.destinationCrs().srsid()
        geom = result[0]
        fid = result[1]
        if layerCRSSrsid != projectCRSSrsid:
            geom.transform(QgsCoordinateTransform(projectCRSSrsid, layerCRSSrsid))
        layer.beginEditCommand("Feature rotated")
        layer.changeGeometry(fid, geom)
        layer.endEditCommand()

    def unload(self):
        self.toolBar.removeAction(self.squarefromcenter)
        self.toolBar.removeAction(self.spinBoxAction)
        del self.toolBar
