#-*- coding:utf-8 -*-
from qgis.core import *
from calc import *
from math import *

def geom_ellipse(center, axis_a, axis_b, angle_exist):
    #segments = settings.value("/RectOvalDigit/segments",36,type=int)
    segments = 360
    points = []
    for t in [(2*pi)/segments*i for i in range(segments)]:
        points.append((center.x() + axis_a*cos(t)*cos(angle_exist) - axis_b*sin(t)*sin(angle_exist), center.y() + axis_a*cos(t)*sin(angle_exist) + axis_b*sin(t)*cos(angle_exist)))
        polygon = [QgsPoint(i[0],i[1]) for i in points]
        geom = QgsGeometry.fromPolygon([polygon])

    return geom

def ellipseFromFoci(f1, f2, f3):
    dist_f1f2 = QgsDistanceArea().measureLine(f1, f2)
    dist_tot = QgsDistanceArea().measureLine(f1, f3) + QgsDistanceArea().measureLine(f2, f3)
    angle_exist = calcAngleExistant(f1, f2)
    center_f1f2 = calc_milieuLine(f1, f2)

    axis_a = dist_tot / 2.0
    axis_b = sqrt((dist_tot/2.0)**2.0 - (dist_f1f2/2.0)**2.0)

    if axis_a < axis_b:
        axis_a,axis_b = axis_b, axis_a

    return geom_ellipse(center_f1f2, axis_a, axis_b, angle_exist)
