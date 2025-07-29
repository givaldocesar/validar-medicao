# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsMessageLog, QgsColorUtils
from qgis.gui import QgsMapToolEmitPoint

from .resources import *
from .validar_medicao_dialog import ValidarMedicaoDialog
from .tools.bacias_captacao import BaciasCaptacao
from .tools.terracos import Terracos
import os.path


class ValidarMedicao:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ValidarMedicao_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Validar Medição')

        self.first_start = None
        self.canvas = self.iface.mapCanvas()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ValidarMedicao', message)

    def add_action(
        self,
        tool,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(True)
        tool.setAction(action)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        self.toolbar = self.iface.addToolBar("Validar Medição")
        self.bacias_6 = BaciasCaptacao(self.iface, radius=6, border_color=QgsColorUtils.colorFromString("#7DF9FF"))
        self.bacias_12= BaciasCaptacao(self.iface, radius=12, border_color=QgsColorUtils.colorFromString("#C70039"))
        self.terracos = Terracos(self.iface)
        
        self.add_action(
            self.bacias_6,
            ':/plugins/validar_medicao/resources/bacias_captacao_6.png',
            text=self.tr(u'Criar Bacia de 6m'),
            callback=self.run_criar_bacia_6)
        
        self.add_action(
            self.bacias_12,
            ':/plugins/validar_medicao/resources/bacias_captacao_12.png',
            text=self.tr(u'Criar Bacia de 12m'),
            callback=self.run_criar_bacia_12)
        
        self.add_action(
            self.terracos,
            ':/plugins/validar_medicao/resources/terracos.png',
            text=self.tr(u'Criar Terraço'),
            callback=self.run_criar_terraco
        )

        self.toolbar.addSeparator()

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Validar Medição'), action)
            self.toolbar.removeAction(action)
        
        self.toolbar.deleteLater()

    def run_criar_bacia_6(self):
        self.canvas.setMapTool(self.bacias_6)
        QgsMessageLog.logMessage("Criar Bacias de Captação com 6m de raio ativada.", "Validar Medição", level=Qgis.Info)
 
    def run_criar_bacia_12(self):
        self.canvas.setMapTool(self.bacias_12)
        QgsMessageLog.logMessage("Criar Bacias de Captação com 12m de raio ativada.", "Validar Medição", level=Qgis.Info)
    
    def run_criar_terraco(self):
        self.canvas.setMapTool(self.terracos)
        QgsMessageLog.logMessage("Criar Terraços ativada.", "Validar Medição", level=Qgis.Info)

