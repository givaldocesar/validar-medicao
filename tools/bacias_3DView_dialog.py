import os
import numpy as np
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout
from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis, QgsProject
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class Model3DDialog(QDialog):
    def __init__(self, raster, mask, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Validar Medição: Modelo 3D")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(500, 500, 500, 500)
        self.setLayout(QVBoxLayout())

        self.canvas = FigureCanvas(Figure())
        ax = self.createMDTSurface(raster)
        self.createMaskPerimeter(ax, raster, mask)
        
        self.canvas.draw()

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
    
    def createMDTSurface(self, raster):
        provider = raster.dataProvider()
        data = provider.block(1, raster.extent(), raster.width(), raster.height())
        self.Z = data.as_numpy()
        
        x = np.arange(0, self.Z.shape[1])
        y = np.arange(0, self.Z.shape[0])
        X, Y = np.meshgrid(x, y)
        
        ax = self.canvas.figure.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y,  self.Z, cmap="terrain", rstride=5, cstride=5, label='MDT')
        
        ax.set_zlabel('Z (pixels)')
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        #limpeza após o uso
        QgsProject.instance().removeMapLayer(raster.id())

        return ax
    
    def createMaskPerimeter(self, ax, raster, mask):
        transform_x = raster.extent().xMinimum()
        transform_y = raster.extent().yMaximum()
        pixel_size_x = raster.extent().width() / raster.width()
        pixel_size_y = raster.extent().height() / raster.height()

        for feature in mask.getFeatures():
            for part in feature.geometry().asGeometryCollection():
                if part.type() == Qgis.GeometryType.Polygon:
                    points = part.asPolygon()[0]
                    
                    perimeter_x_pixels = []
                    perimeter_y_pixels = []
                    perimeter_z_values = []

                    for qgs_point in points:
                        x_pixel = int((qgs_point.x() - transform_x) / pixel_size_x)
                        y_pixel = int((transform_y - qgs_point.y()) / pixel_size_y)

                        if 0 <= x_pixel < raster.width() and 0 <= y_pixel < raster.height():
                            z_value = self.Z[y_pixel, x_pixel]
                            if not np.isnan(z_value):
                                perimeter_x_pixels.append(x_pixel)
                                perimeter_y_pixels.append(y_pixel)
                                perimeter_z_values.append(z_value)
                            else:
                                pass
                    if perimeter_x_pixels:
                        ax.plot(perimeter_x_pixels, perimeter_y_pixels, perimeter_z_values, color='red', linewidth=3, zorder=10, label='Bacia de captação')
        
        QgsProject.instance().removeMapLayer(mask.id())