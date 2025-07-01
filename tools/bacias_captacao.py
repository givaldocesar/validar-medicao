from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.core import Qgis, QgsMapLayer, QgsGeometry, QgsField, QgsFeature, QgsMessageLog
from PyQt5.QtCore import Qt, QVariant

DIAMETRO = "diametro"
FIELD = QgsField(DIAMETRO, QVariant.Int)

class BaciasCaptacao(QgsMapToolEmitPoint):
    def __init__(self, iface, canvas, radius=6, border_color=Qt.red):
        self.iface = iface
        self.canvas = canvas
        super().__init__(self.canvas)
        
        self.rubberBand = QgsRubberBand(self.canvas, Qgis.GeometryType.Polygon)
        self.rubberBand.setWidth(3)
        self.rubberBand.setColor(border_color)
        self.setCursor(Qt.CrossCursor)

        self.radius = radius
        self.active_layer = self.canvas.currentLayer()
        self.preview_geometry = None

        self.canvas.currentLayerChanged.connect(self.checkLayer)
        self.checkLayer(self.active_layer)
    
    def canvasMoveEvent(self, event):
        self.active_layer = self.canvas.currentLayer()
        point = self.toLayerCoordinates(self.active_layer, event.pos())

        if self.active_layer.crs().isGeographic():
            return

        try:
            self.preview_geometry = QgsGeometry.fromPointXY(point).buffer(self.radius, 36)
            self.rubberBand.reset()
            self.rubberBand.addGeometry(self.preview_geometry, self.active_layer.crs())
            self.rubberBand.show()
        except Exception as e:
            self.printMessage(e) 
            self.clear()

    def canvasReleaseEvent(self, event):
        if not self.checkLayer(self.active_layer):
            return
        
        if event.button() == Qt.LeftButton:
            self.active_layer = self.canvas.currentLayer()
            
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
                self.printMessage(f"Erro ao inserir feição: {e}", push=True, level=Qgis.MessageLevel.Critical)
            finally:
                self.rubberBand.hide()
                self.preview_geometry = None
        
        elif event.button() == Qt.RightButton:
            self.preview_geometry = None
            self.rubberBand.hide()
            QgsMapToolEmitPoint.deactivate(self)
            self.canvas.unsetMapTool(self)
            self.printMessage(f"Bacias de Captação com {self.radius}m de raio desativada.", level=Qgis.MessageLevel.Info)
    
    def checkLayer(self, layer):
        isValid = True

        # VERIFICA SE A CAMADA ESTÁ ATIVA
        if(not layer):
            self.printMessage("Por favor, selecione uma camada válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False
        
        # VERIFICA SE A CAMADA É VETORIAL
        elif(layer.type() != QgsMapLayer.VectorLayer):
            self.printMessage("Por favor, selecione uma camada válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False

        # VERIFICA SE A CAMADA ESTÁ EM GEOGRAFICA
        elif layer.crs().isGeographic():
            self.printMessage("O SRC da camda deve ser projetado, para maior precisão. Utilize UTM.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False

        # VERIFICA SE A CAMADA É DO TIPO POLIGONO
        elif layer.geometryType() !=  Qgis.GeometryType.Polygon:
            self.printMessage("Por favor, selecione uma camada de POLÍGONOS válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False
        
        if not isValid:
            self.clear()

        return isValid
    
    def clear(self):
        self.rubberBand.hide()
        self.preview_geometry = None

    def deactivate(self):
        self.printMessage(f"Bacias de captação com {self.radius}m desativada.", level=Qgis.MessageLevel.Info)
        self.rubberBand.hide()
        QgsMapToolEmitPoint.deactivate(self)
    
    def printMessage(self, message, push=False, level=Qgis.MessageLevel.Warning):
        QgsMessageLog.logMessage(str(message), "Validar Medição", level)
        if push:
            self.iface.messageBar().pushMessage("Validar Medição", str(message), level=level, duration=5)
