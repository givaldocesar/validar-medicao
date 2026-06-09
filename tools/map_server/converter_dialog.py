from qgis.core import QgsSettings
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                 QPushButton, QComboBox, QFileDialog, QProgressBar, QMessageBox)
from .converter_worker import ConverterWorker

class ImportImagesDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Importar e Otimizar Aerolevantamentos (COG)")
        self.resize(500, 250)
        
        self.settings = QgsSettings()
        self.worker = None
        self.is_running = False

        self.initUI()

    def createHorizontalLine(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #aaaaaa; margin-top: 15px; margin-bottom: 10px;")
        layout.addWidget(line)
    
    def initUI(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("1. Qual produto você deseja importar?"))
        self.product = QComboBox()
        self.product.addItems(["Ortofotos", "MDT", "MDS"])
        layout.addWidget(self.product)

        layout.addWidget(QLabel("2. Onde estão os arquivos .tif originais?"))
        input_layout = QHBoxLayout()
        self.lbl_input_dir = QLabel("Nenhuma pasta selecionada...")
        self.btn_search = QPushButton("Procurar...")
        self.btn_search.clicked.connect(self.select_dir)
        input_layout.addWidget(self.lbl_input_dir)
        input_layout.addWidget(self.btn_search)
        layout.addLayout(input_layout)

        self.createHorizontalLine(layout)

        self.lbl_status = QLabel("Aguardando inicio...")
        layout.addWidget(self.lbl_status)

        # BARRAS DE PROGRESSO
        layout.addWidget(QLabel("Conversão:"))
        self.progress_bar_file = QProgressBar()
        self.progress_bar_file.setValue(0)
        self.progress_bar_file.setStyleSheet("QProgressBar { text-align: center; } QProgressBar::chunk { background-color: #3498db; }")
        layout.addWidget(self.progress_bar_file)

        layout.addWidget(QLabel("Progresso total:"))
        self.progress_bar_total = QProgressBar()
        self.progress_bar_total.setValue(0)
        self.progress_bar_total.setStyleSheet("QProgressBar { text-align: center; } QProgressBar::chunk { background-color: #2e8b57; }")
        layout.addWidget(self.progress_bar_total)

        self.createHorizontalLine(layout)

        # BOTOES
        buttons_box = QHBoxLayout()

        self.btn_execute = QPushButton("Iniciar")
        self.btn_execute.clicked.connect(self.execute)
        self.btn_execute.setStyleSheet("background-color: #2e8b57; color: white; font-weight: bold; padding: 8px;")
        buttons_box.addWidget(self.btn_execute)

        self.btn_cancel = QPushButton("Interromper")
        self.btn_cancel.clicked.connect(self.stop)
        self.btn_cancel.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px;")
        self.btn_cancel.setEnabled(False)
        buttons_box.addWidget(self.btn_cancel)

        layout.addLayout(buttons_box)

        self.setLayout(layout)
        self.selected_dir = ""
    
    def closeEvent(self, event):
        if self.is_running:
            QMessageBox.warning(self, "Processamento Ativo", "Por favor, clique em 'Interromper' antes de fechar a janela para não corromper os arquivos em andamento.")
            event.ignore()
        else:
            event.accept()

    def select_dir(self):
        dir = QFileDialog.getExistingDirectory(self, "Selecione a pasta com os .tif originais")
        if dir:
            self.selected_dir = dir
            self.lbl_input_dir.setText(dir)
        
    def execute(self):
        if not self.selected_dir:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione a pasta de origem dos arquivos.")
            return

        product = self.product.currentText()
        
        # Mapeia qual chave buscar no registro baseando no produto escolhido
        keys_settings = {"Ortofotos": "dir_orto", "MDT": "dir_mdt", "MDS": "dir_mds"}
        base_output_dir = self.settings.value(f"validar_medicao/{keys_settings[product]}", "")

        if not base_output_dir:
            QMessageBox.critical(self, "Erro", f"O diretório raiz para {product} não foi configurado.\nVá na engrenagem do plugin e configure o MapServer primeiro!")
            return

        # Trava os botões para o usuário não clicar duas vezes
        self.product.setEnabled(False)
        self.btn_search.setEnabled(False)
        self.btn_execute.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.is_running = True
        
        # Inicia a Thread
        self.worker = ConverterWorker(self.selected_dir, base_output_dir, product)
        self.worker.file_progress_changed.connect(self.progress_bar_file.setValue)
        self.worker.progress_changed.connect(self.progress_bar_total.setValue)
        self.worker.progress_text.connect(self.lbl_status.setText)
        self.worker.finished.connect(self.finished)
        self.worker.start()

    def stop(self):
        if self.worker and self.is_running:
            self.lbl_status.setText("Cancelando operação... Aguardando a finalização da imagem atual.")
            self.btn_cancel.setEnabled(False)
            self.worker.cancel()
    
    def finished(self, success, message):
        self.product.setEnabled(True)
        self.btn_search.setEnabled(True)
        self.btn_execute.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.is_running = False
        
        if success:
            QMessageBox.information(self, "Sucesso", message)
            if not self.worker.is_canceled:
                self.progress_bar_file.setValue(100)
                self.progress_bar_total.setValue(100)
                self.lbl_status.setText("Concluído! O MapServer já pode ser reiniciado.")
        else:
            QMessageBox.critical(self, "Erro na Conversão", message)
            self.lbl_status.setText("Falha no processamento.")