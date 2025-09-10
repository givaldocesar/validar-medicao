from qgis.core import QgsColorUtils
from qgis.PyQt.QtWidgets import QLabel, QDoubleSpinBox
from qgis.PyQt.QtGui import QDoubleValidator
from qgis.PyQt.QtCore import QLocale
from .bacias_captacao import BaciasCaptacao
from .utils import printMessage

class BaciasCaptacaoCustomRadius(BaciasCaptacao):
    def __init__(self, iface):
        super().__init__(iface, radius=9, border_color=QgsColorUtils.colorFromString("#ffcf40"))
    
    def addComboBox(self, toolbar):
        self.diameter = QDoubleSpinBox(self.iface.mainWindow())
        self.diameter.setMinimumWidth(50)
        self.diameter.setMaximumWidth(60)
        self.diameter.setDecimals(2)
        self.diameter.setMinimum(0.01)
        self.diameter.setMaximum(30.0)
        self.diameter.setSingleStep(0.5)
        self.diameter.setValue(self.radius)
        self.diameter.valueChanged.connect(self.changeRadius)
        
        toolbar.addWidget(QLabel("Diâmetro: "))
        toolbar.addWidget(self.diameter)
    
    def changeRadius(self, value):
        self.radius = value
