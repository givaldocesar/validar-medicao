# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsMessageLog, QgsColorUtils

from .resources import *
from .validar_medicao_dialog import ValidarMedicaoDialog
from .tools.bacias_captacao import BaciasCaptacao
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
        self.previous_tool = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ValidarMedicao', message)


    def add_action(
        self,
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

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        self.add_action(
            ':/plugins/validar_medicao/resources/bacias_captacao_6.png',
            text=self.tr(u'Criar Bacia de 6m'),
            callback=self.run_criar_bacia_6,
            parent=self.iface.mainWindow())
        
        self.add_action(
            ':/plugins/validar_medicao/resources/bacias_captacao_12.png',
            text=self.tr(u'Criar Bacia de 12m'),
            callback=self.run_criar_bacia_12,
            parent=self.iface.mainWindow())

        self.first_start = True


    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Validar Medição'),
                action)
            self.iface.removeToolBarIcon(action)


    def run_criar_bacia_6(self):
        canvas = self.iface.mapCanvas()
        self.previous_tool = canvas.mapTool()
        self.current_tool = BaciasCaptacao(self.iface,
                                           canvas, 
                                           radius=6, 
                                           border_color=QgsColorUtils.colorFromString("#7DF9FF"),
                                           previous_tool=self.previous_tool)
        canvas.setMapTool(self.current_tool)
        QgsMessageLog.logMessage("Bacias de Captação com 6m de raio ativada.", "Validar Medição", level=Qgis.Info)

    
    def run_criar_bacia_12(self):
        canvas = self.iface.mapCanvas()
        self.previous_tool = canvas.mapTool()
        self.current_tool = BaciasCaptacao(self.iface,
                                           canvas, 
                                           radius=12, 
                                           border_color=QgsColorUtils.colorFromString("#C70039"),
                                           previous_tool=self.previous_tool)
        canvas.setMapTool(self.current_tool)
        QgsMessageLog.logMessage("Bacias de Captação com 12m de raio ativada.", "Validar Medição", level=Qgis.Info)

