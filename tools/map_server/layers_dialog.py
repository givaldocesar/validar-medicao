from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel
from qgis.PyQt.QtCore import Qt

class LayersDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Mosaicos para Carregar")
        self.resize(350, 400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecione as ortofotos:"))

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        years_dict = {}
        for name, title, year in layers:
            if year not in years_dict:
                years_dict[year] = []
            years_dict[year].append((name, title, year))
        
        for key in sorted(years_dict.keys(), reverse=True):
            parent_item = QTreeWidgetItem(self.tree, [key])
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            parent_item.setCheckState(0, Qt.Unchecked)

            for name, title, year in years_dict[key]:
                child_item = QTreeWidgetItem(parent_item, [title])
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                child_item.setData(0, Qt.UserRole, (name, title, year))
            
            parent_item.setExpanded(False)
        
        layout.addWidget(self.tree)

        self.tree.itemDoubleClicked.connect(self.change_item)

        load = QPushButton("Carregar Camadas")
        load.clicked.connect(self.accept) 
        layout.addWidget(load)

    def change_item(self, item, column):
        if item.checkState(0) == Qt.Checked:
            item.setCheckState(0, Qt.Unchecked)
        else:
            item.setCheckState(0, Qt.Checked)

    def get_layers(self):
        layers = []

        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)

            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    layers.append(child.data(0, Qt.UserRole))

        return layers