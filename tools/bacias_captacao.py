from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.core import Qgis, QgsMapLayer, QgsGeometry, QgsField, QgsFeature, QgsMessageLog
from qgis.PyQt.QtCore import Qt, QMetaType

DIAMETRO = "diametro"
FIELD = QgsField(DIAMETRO, QMetaType.Int)

class BaciasCaptacao(QgsMapToolEmitPoint):
    def __init__(self, iface, radius, border_color):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)
        
        self.rubberBand = QgsRubberBand(self.canvas, Qgis.GeometryType.Polygon)
        self.rubberBand.setWidth(3)
        self.rubberBand.setColor(border_color)

        self.radius = radius
        self.preview_geometry = None
    
    def activate(self):
        self.setCursor(Qt.CrossCursor)
    
    def canvasMoveEvent(self, event):
        self.active_layer = self.canvas.currentLayer()
        point = self.toLayerCoordinates(self.active_layer, event.pos())

        if not self.active_layer:
            return
        
        if not self.active_layer or self.active_layer.crs().isGeographic():
            return

        try:
            self.preview_geometry = QgsGeometry.fromPointXY(point).buffer(self.radius, 36)
            self.rubberBand.reset()
            self.rubberBand.addGeometry(self.preview_geometry, self.active_layer.crs())
            self.rubberBand.show()
        except Exception as e:
            self.printMessage(e, level=Qgis.MessageLevel.Critical) 
            self.clear()

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.insert()
        
        elif event.button() == Qt.RightButton:
            self.canvas.unsetMapTool(self)

    def setRadius(self, value):
        self.radius = value

    def checkLayer(self, layer):
        isValid = True

        # VERIFICA SE A CAMADA ESTÁ ATIVA
        if not layer:
            self.printMessage("Por favor, selecione uma camada válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False
        
        # VERIFICA SE A CAMADA É VETORIAL
        elif layer.type() != QgsMapLayer.VectorLayer:
            self.printMessage("Por favor, selecione uma camada VETORIAL válida.", push=True, level=Qgis.MessageLevel.Critical)
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
            self.clean()

        return isValid
    
    def clean(self):
        self.rubberBand.hide()
        self.preview_geometry = None

    def deactivate(self):
        self.clean()
        QgsMapToolEmitPoint.deactivate(self)
        self.printMessage(f"Criar Bacias de Captação com {self.radius*2}m de diâmetro desativada.", level=Qgis.MessageLevel.Info)
    
    def insert(self):
        self.active_layer = self.canvas.currentLayer()

        if self.checkLayer(self.active_layer):
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
        
        self.clean()

    def printMessage(self, message, push=False, level=Qgis.MessageLevel.Warning):
        QgsMessageLog.logMessage(str(message), "Validar Medição", level)
        if push:
            self.iface.messageBar().pushMessage("Criar bacia de captação", str(message), level=level, duration=5)