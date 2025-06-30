from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.core import Qgis, QgsGeometry, QgsField, QgsFields, QgsFeature, QgsMessageLog
from PyQt5.QtCore import Qt, QVariant

DIAMETRO = "diametro"
FIELD = QgsField(DIAMETRO, QVariant.Int)

class BaciasCaptacao(QgsMapToolEmitPoint):
    def __init__(self, iface, canvas, radius=6, border_color=Qt.red, fill_color=Qt.green, previous_tool=None):
        self.iface = iface
        self.canvas = canvas
        super().__init__(self.canvas)
        
        self.rubberBand = QgsRubberBand(self.canvas, Qgis.GeometryType.Polygon)
        self.rubberBand.setWidth(3)
        self.rubberBand.setStrokeColor(border_color)
        self.rubberBand.setFillColor(fill_color)
        self.rubberBand.setWidth(radius)

        self.setCursor(Qt.CrossCursor)

        self.radius = radius
        self.active_layer = None
        self.preview_geometry = None
        self.previous_tool = previous_tool # Para restaurar a ferramenta anterior
    
    def canvasMoveEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.active_layer = self.canvas.currentLayer()

        if self.active_layer.crs().isGeographic():
            return
        
        try:
            self.preview_geometry = QgsGeometry.fromPointXY(point).buffer(self.radius, 36)
            self.rubberBand.reset()
            self.rubberBand.addGeometry(self.preview_geometry, self.active_layer.crs())
            self.rubberBand.show()
        except Exception as e:
            self.rubberBand.hide()
            self.preview_geometry = None

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.active_layer = self.canvas.currentLayer()

            # VERIFICA SE A CAMADA ESTÁ ATIVA E É DO TIPO POLIGONO
            if not self.active_layer or self.active_layer.geometryType() !=  Qgis.GeometryType.Polygon:
                self.printMessage("Por favor, selecione uma camada de POLÍGONOS válida.", level=Qgis.MessageLevel.Critical)
                self.preview_geometry = None
                return

            # VERIFICA SE A CAMADA ESTÁ EM GEOGRAFICA
            if self.active_layer.crs().isGeographic():
                self.printMessage("O SRC da camda deve ser projetado, para maior precisão.", level=Qgis.MessageLevel.Critical)
                self.preview_geometry = None
                return

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.preview_geometry and self.active_layer:
            try:
                self.active_layer.startEditing()
                field_idx = self.active_layer.fields().indexOf(DIAMETRO)
                
                if field_idx == -1:
                    response = self.active_layer.dataProvider().addAttributes([FIELD])
                    if(response):
                        self.active_layer.updateFields()
                        field_idx = self.active_layer.fields().indexOf(DIAMETRO)
                    else:
                        self.printMessage("Erro ao criar campo >>diametro<<")
                        return
                
                layer_fields = self.active_layer.fields()
                feat = QgsFeature(layer_fields)
                feat.setGeometry(self.preview_geometry)
                feat[DIAMETRO] = self.radius*2
                self.active_layer.addFeature(feat)
                self.active_layer.commitChanges()
            except Exception as e:
                self.active_layer.rollBack()
                self.printMessage(f"Erro ao inserir feição: {e}", level=Qgis.MessageLevel.Critical)
            finally:
                self.rubberBand.hide()
                self.preview_geometry = None
        
        elif event.button() == Qt.RightButton:
            self.preview_geometry = None
            self.rubberBand.hide()
            QgsMapToolEmitPoint.deactivate(self)
            self.canvas.unsetMapTool(self)
            self.printMessage(f"Bacias de Captação com {self.radius}m de raio desativada.", push=False, level=Qgis.MessageLevel.Info)
    
    def deactivate(self):
        self.rubberBand.hide()
        QgsMapToolEmitPoint.deactivate(self)
    
    def printMessage(self, message, push=True, level=Qgis.MessageLevel.Warning):
        QgsMessageLog.logMessage(str(message), "Validar Medição", level)
        if push:
            self.iface.messageBar().pushMessage("Validar Medição", str(message), level=level, duration=5)
