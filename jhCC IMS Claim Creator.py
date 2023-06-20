import sys
import csv
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('jhCC IMS Claim Creator')
        self.setWindowIcon(QIcon('C:\\Users\\cbrichardson\\OneDrive - Jack Henry & Associates\\Documents\\GitHub\\Testing Scripts\\PyQT\\jh.ico'))
        
        main_style = "background-color: #1a3668; color: white; font-family: 'Poppins'; font-size: 16px"
        button_style = "background-color: #1a3668; color: white; font-family: 'Poppins';"
        entry_style = "background-color: white; color: black; font-family: 'Poppins';"
        self.setStyleSheet(main_style)
    
        self.main_widget = QtWidgets.QWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
    
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.addItem('Please select an option')
        self.dropdown.addItems(['Single Agent', 'New Hire Class', 'New FI'])
        self.dropdown.currentIndexChanged.connect(self.initial_update_ui)
        self.dropdown.setStyleSheet(entry_style)
        self.layout.addWidget(self.dropdown)
    
        # Set 'Please select an option' as non-selectable and non-editable
        self.dropdown.model().item(0).setEnabled(False)

        self.stack = QtWidgets.QStackedWidget(self)
        self.layout.addWidget(self.stack)

        # Single Agent widgets
        self.opt1_widget = QtWidgets.QWidget()
        self.opt1_layout = QtWidgets.QVBoxLayout(self.opt1_widget)
        self.stack.addWidget(self.opt1_widget)

        self.agent_email_label = QtWidgets.QLabel('Agent Email')
        self.agent_email_entry = QtWidgets.QLineEdit()
        self.agent_email_entry.setStyleSheet(entry_style)
        self.agent_extension_label = QtWidgets.QLabel('Agent Extension')
        self.agent_extension_entry = QtWidgets.QLineEdit()
        self.agent_extension_entry.setStyleSheet(entry_style)
        self.email_button = QtWidgets.QPushButton('Check Email')
        self.email_button.clicked.connect(self.check_email)
        self.extension_button = QtWidgets.QPushButton('Check Extension')
        self.extension_button.clicked.connect(self.check_extension)
        self.opt1_layout.addWidget(self.agent_email_label)
        self.opt1_layout.addWidget(self.agent_email_entry)
        self.opt1_layout.addWidget(self.email_button)
        self.opt1_layout.addWidget(self.agent_extension_label)
        self.opt1_layout.addWidget(self.agent_extension_entry)
        self.opt1_layout.addWidget(self.extension_button)
        

        
        self.checkbox1 = QtWidgets.QCheckBox('Single Bank Core Claim')
        self.checkbox2 = QtWidgets.QCheckBox('Single Synapsys')
        self.checkbox3 = QtWidgets.QCheckBox('All Bank Core Claim')
        self.checkbox4 = QtWidgets.QCheckBox('All Bank Synapsys Claim')
        self.checkbox5 = QtWidgets.QCheckBox('All CU Synapsys Claim')
        self.checkbox6 = QtWidgets.QCheckBox('Trainer Claim')
        self.opt1_layout.addWidget(self.checkbox1)
        self.opt1_layout.addWidget(self.checkbox2)
        self.opt1_layout.addWidget(self.checkbox3)
        self.opt1_layout.addWidget(self.checkbox4)
        self.opt1_layout.addWidget(self.checkbox5)
        self.opt1_layout.addWidget(self.checkbox6)
        self.clear = QtWidgets.QPushButton('Clear')
        self.opt1_layout.addWidget(self.clear)
        self.clear.clicked.connect(self.clear_options)

        # New Hire Class widgets
        self.opt2_widget = QtWidgets.QWidget()
        self.opt2_layout = QtWidgets.QVBoxLayout(self.opt2_widget)
        self.stack.addWidget(self.opt2_widget)

        self.import_button = QtWidgets.QPushButton('Import CSV')
        self.import_button.clicked.connect(self.import_csv)
        self.opt2_layout.addWidget(self.import_button)

        self.checkboxes2 = [QtWidgets.QCheckBox(f'Checkbox {i+1}') for i in range(3)]
        for cb in self.checkboxes2:
            self.opt2_layout.addWidget(cb)

        # New FI widgets
        self.opt3_widget = QtWidgets.QWidget()
        self.opt3_layout = QtWidgets.QVBoxLayout(self.opt3_widget)
        self.stack.addWidget(self.opt3_widget)

        self.checkboxes3 = [QtWidgets.QCheckBox(f'Checkbox {i+1}') for i in range(3)]
        for cb in self.checkboxes3:
            self.opt3_layout.addWidget(cb)

        # Output queue
        self.queue = QtWidgets.QListWidget()
        self.layout.addWidget(self.queue)
        self.queue.setStyleSheet(entry_style)

        # Buttons for processing and removing queue entries
        self.process_button = QtWidgets.QPushButton('Process Queue')
        self.process_button.clicked.connect(self.process_queue)
        self.remove_button = QtWidgets.QPushButton('Remove Entry')
        self.remove_button.clicked.connect(self.remove_entry)
        self.layout.addWidget(self.process_button)
        self.layout.addWidget(self.remove_button)

        self.setCentralWidget(self.main_widget)

        # Hide stack and process queue initially
        self.stack.hide()
        self.queue.hide()
        self.process_button.hide()
        self.remove_button.hide()

    def initial_update_ui(self, index):
        if index == 0: 
            return
        # disconnect initial signal
        self.dropdown.currentIndexChanged.disconnect(self.initial_update_ui)
        # remove 'Please select an option'
        self.dropdown.removeItem(0)
        # reconnect signal to regular update_ui
        self.dropdown.currentIndexChanged.connect(self.update_ui)
        # call update_ui for initial selection
        self.update_ui(self.dropdown.currentIndex())

    
    def update_ui(self, index):
        self.stack.setCurrentIndex(index)
        self.stack.show()
        self.queue.show()
        self.process_button.show()
        self.remove_button.show()

    def remove_placeholder(self):
    # Remove 'Please select an option' if it is still there
        if self.dropdown.itemText(0) == 'Please select an option':
            self.dropdown.removeItem(0)

    def import_csv(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Import CSV', QtCore.QDir.currentPath(), 'CSV Files (*.csv)')
        if filename:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                print(list(reader))

    def update_ui(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)
            self.stack.show()
            self.queue.show()
            self.process_button.show()
            self.remove_button.show()
    
    def check_email(self):
        pass
    
    def check_extension(self):
        pass
    
    def clear_options(self):
        
        
        
        self.checkbox1.setChecked(False)
        self.checkbox2.setChecked(False)
        self.checkbox3.setChecked(False)
        self.checkbox4.setChecked(False)
        self.checkbox5.setChecked(False)
        self.checkbox6.setChecked(False)
        self.agent_email_entry.clear()
        self.agent_extension_entry.clear()
        self.clear.setText('Undo')
        #QApplication.processEvents()
        pass
    
    def process_queue(self):
        # Add your code to process queue here
        print("Claims processed")
        pass

    def remove_entry(self):
        # Add your code to remove queue entry here
        print("Selected item removed")
        pass
    
    


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
