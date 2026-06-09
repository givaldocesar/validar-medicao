import os
from qgis.core import QgsApplication, QgsSettings
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QLineEdit, QPushButton, QTabWidget, QWidget, QFileDialog)

class ConfigMapServerDialog(QDialog):
    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.server = server
        self.setWindowTitle(self.tr("Configurações do MapServer"))
        self.resize(550, 350)
        
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # Aba 1: Diretórios de Trabalho
        self.dirs_tabs = QWidget()
        self.setup_directories()
        self.tabs.addTab(self.dirs_tabs, self.tr("Diretórios de Imagens"))
        
        # Aba 2: Avançado / Debug
        self.debug_tab = QWidget()
        self.setup_debug_tab()
        self.tabs.addTab(self.debug_tab, self.tr("Avançado (Debug)"))
        
        main_layout.addWidget(self.tabs)
        
        layout_buttons = QHBoxLayout()
        btn_save = QPushButton(self.tr("Salvar Configurações"))
        btn_save.clicked.connect(self.save_config)
        btn_cancel = QPushButton(self.tr("Cancelar"))
        btn_cancel.clicked.connect(self.reject)
        
        layout_buttons.addStretch()
        layout_buttons.addWidget(btn_cancel)
        layout_buttons.addWidget(btn_save)
        main_layout.addLayout(layout_buttons)
        
        self.load_config()
    
    def load_config(self):
        settings = QgsSettings()
        self.input_orto.setText(settings.value("validar_medicao/dir_orto", ""))
        self.input_mdt.setText(settings.value("validar_medicao/dir_mdt", ""))
        self.input_mds.setText(settings.value("validar_medicao/dir_mds", ""))
        self.input_contours.setText(settings.value("validar_medicao/dir_contours", ""))
    
    def search_dir(self, input_field):
        starter_dir = input_field.text() if os.path.exists(input_field.text()) else ""
        dir = QFileDialog.getExistingDirectory(self, self.tr("Selecione o Diretório"), starter_dir)
        if dir:
            input_field.setText(dir.replace("/", "\\"))

    def create_row_dir(self, label_text, parent_layout):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(140)
        layout.addWidget(label)
        
        input_text = QLineEdit()
        btn_search = QPushButton("...")
        btn_search.setFixedWidth(40)
        btn_search.clicked.connect(lambda: self.search_dir(input_text))
        
        layout.addWidget(input_text)
        layout.addWidget(btn_search)
        parent_layout.addLayout(layout)
        return input_text
    
    def setup_directories(self):
        layout = QVBoxLayout(self.dirs_tabs)
        
        self.input_orto = self.create_row_dir(self.tr("Pasta de Ortofotos:"), layout)
        self.input_mdt = self.create_row_dir(self.tr("Pasta de MDT:"), layout)
        self.input_mds = self.create_row_dir(self.tr("Pasta de MDS:"), layout)
        self.input_contours = self.create_row_dir(self.tr("Pasta de Curvas de Nível:"), layout)
        layout.addStretch()

    def setup_debug_tab(self):
        layout = QVBoxLayout(self.debug_tab)
        
        lbl_info = QLabel(self.tr("<b>Atalhos Rápidos de Manutenção:</b><br> ") +
                          self.tr("Utilize os botões abaixo para acessar os arquivos base do servidor."))
        layout.addWidget(lbl_info)
        
        btn_mapserv_dir = QPushButton(self.tr("Abrir Pasta Raiz do MapServer"))
        btn_mapserv_dir.clicked.connect(lambda: os.startfile(self.server.directory) if os.path.exists(self.server.directory) else None)
        
        btn_mapserv_mapconfig = QPushButton(self.tr("Abrir config.map"))
        arquivo_config = os.path.join(self.server.directory, "config.map")
        btn_mapserv_mapconfig.clicked.connect(lambda: os.startfile(arquivo_config) if os.path.exists(arquivo_config) else None)
        
        btn_mapserv_conf = QPushButton(self.tr("Abrir mapserv.conf"))
        arquivo_conf = os.path.join(self.server.directory, "mapserv.conf")
        btn_mapserv_conf.clicked.connect(lambda: os.startfile(arquivo_conf) if os.path.exists(arquivo_conf) else None)

        btn_mapserv_error = QPushButton(self.tr("Abrir ms_error.txt"))
        arquivo_error = os.path.join(self.server.directory, "ms_error.txt")
        btn_mapserv_error.clicked.connect(lambda: os.startfile(arquivo_error) if os.path.exists(arquivo_error) else None)

        btn_mapserv_gdal = QPushButton(self.tr("Abrir ms_gdal_log.txt"))
        arquivo_gdal = os.path.join(self.server.directory, "ms_gdal_log.txt")
        btn_mapserv_gdal.clicked.connect(lambda: os.startfile(arquivo_gdal) if os.path.exists(arquivo_gdal) else None)

        #BUTTONS PLAY/STOP/REBOOT
        play_button = QPushButton()
        play_button.setIcon(QgsApplication.getThemeIcon("/mActionPlay.svg"))
        play_button.setStyleSheet("QPushButton { font-weight: bold; color: #155724; background-color: #d4edda; }")
        play_button.setFixedWidth(80)
        play_button.setToolTip("Iniciar o servidor")
        play_button.clicked.connect(self.server.start)
        
        stop_button = QPushButton()
        stop_button.setIcon(QgsApplication.getThemeIcon("/mActionStop.svg"))
        stop_button.setStyleSheet("QPushButton { font-weight: bold; color: #721c24; background-color: #f8d7da; }")
        stop_button.setFixedWidth(80)
        stop_button.setToolTip("Parar o servidor")
        stop_button.clicked.connect(self.server.stop)
        
        reboot_button = QPushButton()
        reboot_button.setIcon(QgsApplication.getThemeIcon("/mActionRefresh.svg"))
        reboot_button.setFixedWidth(80)
        reboot_button.setToolTip("Reiniciar o servidor")
        reboot_button.clicked.connect(self.server.reboot)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(play_button)
        buttons_layout.addWidget(stop_button)
        buttons_layout.addWidget(reboot_button)
        buttons_layout.addStretch()

        buttons_label = QLabel("Alterar estado do Mapserver:")
        buttons_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(btn_mapserv_dir)
        layout.addWidget(btn_mapserv_mapconfig)
        layout.addWidget(btn_mapserv_conf)
        layout.addWidget(btn_mapserv_error)
        layout.addWidget(btn_mapserv_gdal)
        layout.addSpacing(25)
        layout.addWidget(buttons_label)
        layout.addLayout(buttons_layout)
        layout.addStretch()
    
    def save_config(self):
        settings = QgsSettings()
        settings.setValue("validar_medicao/dir_orto", self.input_orto.text())
        settings.setValue("validar_medicao/dir_mdt", self.input_mdt.text())
        settings.setValue("validar_medicao/dir_mds", self.input_mds.text())
        settings.setValue("validar_medicao/dir_curvas", self.input_contours.text())
        
        self.accept()