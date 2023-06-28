import sys
import csv
from PyQt5 import QtWidgets, QtCore, QtGui, QtSql
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QAction, QMenu
import json
import os
import sqlite3
from smartsheet import Smartsheet
from smartsheet import sheets

#get the FI Servicing Sheets and Script sheets with Core user, partition and synapsys numbers and uses the API Token for the jhCC Support Smartsheet User.
os.environ['SMARTSHEET_ACCESS_TOKEN'] = '8RfGAA0rhPQr6K6P6hBNsEHBESXiyZpCN5wkd'
fi_servicing_sheet_ID = 494759136520068 # name: Current FI Servicing
agent_list_sheet_ID = 735036543657860 # name: Agent List
bank_core_sheet_ID = 7891957159618436 # name: IMS PROGRAM 1 Agent : Banking FI Cores
bank_synapsys_sheet_ID = 8999703313442692 #name: IMS PROGRAM 1 Agent : Banking Synapsys
cu_synapsys_sheet_ID = 846684570838916 # name: IMS PROGRAM 1 Agent : CU Synapsys
trainer_fi_sheet_ID = 2405415385360260 # name: IMS PROGRAM Trainer Script Synapsys


# create db in memory Connection and Cursor objects
db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
db.setDatabaseName(':memory:')  # For an in-memory database
db.open()
query = QtSql.QSqlQuery()

if not db.open():
    QtWidgets.QMessageBox.critical(None, "Cannot open database",
                                   "Unable to establish a database connection.\n"
                                   "Click Cancel to exit.", QtWidgets.QMessageBox.Cancel)

#db = sqlite3.connect(':memory:')
#cur = db.cursor()



# Initialize Smartsheet client
smart = Smartsheet()
smart.errors_as_exceptions(True)

# retrieve sheet with specified ID from variables above
fi_sheet = smart.Sheets.get_sheet(fi_servicing_sheet_ID)
bank_synapsys_sheet = smart.Sheets.get_sheet(bank_synapsys_sheet_ID)
bank_core_sheet = smart.Sheets.get_sheet(bank_core_sheet_ID)
cu_synapsys_sheet = smart.Sheets.get_sheet(cu_synapsys_sheet_ID)
agent_list_sheet = smart.Sheets.get_sheet(agent_list_sheet_ID)
trainer_fi_sheet = smart.Sheets.get_sheet(trainer_fi_sheet_ID)

def show_warning(title, body, event = None):

    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.setText(body)
    msgBox.setWindowTitle(title)
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    returnValue = msgBox.exec()

    if returnValue == QMessageBox.Ok:
            print('Warning message OK clicked')

#create column map for relevant columns to use for bank sql import
column_indices = {col.title: i for i, col in enumerate(fi_sheet.columns)}

#return the core user and partition information from the corresponding smartsheet for the bank name input
def get_bank_core_data(fi_name):
    column_indices = {col.title: i for i, col in enumerate(bank_core_sheet.columns)}
    for row in bank_core_sheet.rows:
        if row.cells[column_indices['Bank Name']].value == fi_name:
            return row.cells[column_indices['FI Core']].value, row.cells[column_indices['Bank ID']].value
    return None, None

# create bank list table in database
query.exec_("CREATE TABLE banks (ID INTEGER PRIMARY KEY, fi_name TEXT, fi_syn TEXT, fi_type TEXT, bank_core TEXT, partition TEXT)")
db.commit()

#iterate through both synapsys script sheets and return the synapsys bank number from the corresponding smartsheet for the FI name input
def get_synapsys_data(fi_name, fi_type):
    if fi_type == 'Bank':
        sheet = bank_synapsys_sheet
    elif fi_type == 'CU':
        sheet = cu_synapsys_sheet
    else:
        return None
    column_indices = {col.title: i for i, col in enumerate(sheet.columns)}
    for row in sheet.rows:
        if row.cells[column_indices['Bank Name']].value == fi_name:
            return row.cells[column_indices['Bank ID']].value
    return None

# insert bank data in to SQL table in memory from Current FI Servicing Smartsheet
try:
    seen_fi_names = set()  # set to store seen fi_name values
    #set variables to store the number of banks and CU's loaded from sheet
    bankcount = 0
    cucount = 0
    for row in fi_sheet.rows:
        # extract values of relevant columns
        values = [row.cells[column_indices[col]].value for col in ('FI Name', 'Synapsys Bank Number', 'FI Type', 'Status', 'Logo')]
        # skip row if fi_name value is blank
        if not values[0]:
            continue
        #skip row if logo is blank
        if not values[4]:
            continue
        # skip row if Status value is not 'Active'
        if not values[3] == 'Active':
            continue
        # set bank_core and partition values based on FI Type
        if values[2] == 'Bank':
            bank_core, partition = get_bank_core_data(values[0])
            values[3] = bank_core
            values[4] = partition
        elif values[2] == 'CU':
            values[3] = ''
            values[4] = ''
        else:
            continue
        # get synapsys data
        values[1] = get_synapsys_data(values[0], values[2])
        # check if values[1] is a float and convert it to an integer if it is
        if isinstance(values[1], float):
            values[1] = int(values[1])
        #if no info for synapsys bank number AND bank core and partition skip row
        if (values[1] == 'None' and values[3] == 'None' and values[4] == 'None'):
            continue
        # skip row if fi_name value has been seen before
        if values[0] in seen_fi_names:
            continue
        # add fi_name value to seen set so we dont duplicate bank names
        seen_fi_names.add(values[0])
        if values[2] == 'CU':
            cucount += 1
            print(f'Loaded {values[0]} with Synapsys Bank Number of {values[1]}')
        if values[2] =='Bank':
            bankcount += 1
            print(f'Loaded {values[0]} with Synapsys Bank Number of {values[1]}, Core User of {values[3]} and Partition of {values[4]}')
        # insert row into table
        query.prepare("INSERT INTO banks VALUES (NULL, :value0, :value1, :value2, :value3, :value4)")
        for i in range(len(values)):
            query.bindValue(f":value{i}", values[i])

        query.exec_()
        db.commit()
    print(f"Loaded {bankcount} Banks and {cucount} CU's from Current FI Servicing Smartsheet")
except:
    #show_warning()
    pass

# Create column indexes for claim functions used
agent_name_col = next(col for col in agent_list_sheet.columns if col.title == 'Agent Name')
extension_col = next(col for col in agent_list_sheet.columns if col.title == 'Extension')
skill_col = next(col for col in agent_list_sheet.columns if col.title == 'Skill')
citjha_email_col = next(col for col in agent_list_sheet.columns if col.title == 'CITJHA Domain')
trainer_banks_col = next(col for col in trainer_fi_sheet.columns if col.title == 'Bank Name')
agent_name_col_index = agent_name_col.index
skill_col_index = skill_col.index
extension_col_index = extension_col.index
citjha_email_col_index = citjha_email_col.index
trainer_banks_col_index = trainer_banks_col.index

# Find the row index where the "Agent Name" column starts after "Supervisor" dropdown
total_current_agent_row = next(row for row in agent_list_sheet.rows if row.cells[agent_name_col_index].value == 'Supervisors')
total_current_agent_row_index = total_current_agent_row.row_number
start_row_index = total_current_agent_row_index


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('jhCC IMS Claim Creator')
        self.setWindowIcon(QIcon('C:\\Users\\cbrichardson\\OneDrive - Jack Henry & Associates\\Documents\\GitHub\\Testing Scripts\\PyQT\\jh.ico'))
        
        main_style = "background-color: #1a3668; color: white; font-family: 'Poppins'; font-size: 16px"
        button_style = "background-color: #1a3668; color: white; font-family: 'Poppins';"
        entry_style = "background-color: white; color: black; font-family: 'Poppins';"
        checkbox_style = '''         
            QCheckBox::indicator {
                height: 20px;
                width: 20px;
            }
            QCheckBox:indicator:checked {
                image: url('C:/Users/cbrichardson/OneDrive - Jack Henry & Associates/Documents/GitHub/IMS-Claim-Creator/master/Images/checkmark.png');
            }
        '''
        self.setStyleSheet(main_style)
    
        self.main_widget = QtWidgets.QWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
        
        
    
        self.init_dropdown = QtWidgets.QComboBox()
        self.init_dropdown.addItem('Please select an option')
        self.init_dropdown.addItems(['Single Agent', 'New Hire Class', 'New FI'])
        self.init_dropdown.currentIndexChanged.connect(self.initial_update_ui)
        self.init_dropdown.setStyleSheet(entry_style)
        self.layout.addWidget(self.init_dropdown)
    
        # Set 'Please select an option' as non-selectable and non-editable
        self.init_dropdown.model().item(0).setEnabled(False)

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
        self.email_button = QtWidgets.QPushButton('Get Email')
        self.email_button.clicked.connect(self.get_email)
        self.extension_button = QtWidgets.QPushButton('Get Extension')
        self.extension_button.clicked.connect(self.get_extension)
        self.opt1_layout.addWidget(self.agent_email_label)
        self.opt1_layout.addWidget(self.agent_email_entry)
        self.opt1_layout.addWidget(self.extension_button)
        self.opt1_layout.addWidget(self.agent_extension_label)
        self.opt1_layout.addWidget(self.agent_extension_entry)
        self.opt1_layout.addWidget(self.email_button)
        
        self.checkboxes = [
            QtWidgets.QCheckBox('Single Bank Core Claim'),
            QtWidgets.QCheckBox('Single Synapsys'),
            QtWidgets.QCheckBox('All Bank Core Claim'),
            QtWidgets.QCheckBox('All Bank Synapsys Claim'),
            QtWidgets.QCheckBox('All CU Synapsys Claim'),
            QtWidgets.QCheckBox('Trainer Claim')
        ]
        for checkbox in self.checkboxes:
            self.opt1_layout.addWidget(checkbox)
            checkbox.setStyleSheet(checkbox_style)
        self.clear = QtWidgets.QPushButton('Clear')
        self.opt1_layout.addWidget(self.clear)
        

        # New Hire Class widgets
        self.opt2_widget = QtWidgets.QWidget()
        self.opt2_layout = QtWidgets.QVBoxLayout(self.opt2_widget)
        self.stack.addWidget(self.opt2_widget)
        

        self.import_button = QtWidgets.QPushButton('Import CSV')
        self.import_button.clicked.connect(self.import_csv)
        self.opt2_layout.addWidget(self.import_button)

        self.new_hire_dropdown = QtWidgets.QComboBox()
        self.new_hire_dropdown.addItems(['Banking', 'Credit Unions'])
        self.new_hire_dropdown.setStyleSheet(entry_style)
        #self.init_dropdown.currentIndexChanged.connect(self.initial_update_ui)
        self.opt2_layout.addWidget(self.new_hire_dropdown)

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
        
        self.clear.clicked.connect(self.clear_fields)
        
        # Create the File menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')

        newAction = QAction(QIcon('new.png'), 'Show FI Data Table', self)
        newAction.setShortcut('Ctrl+W')
        newAction.setStatusTip('Create new file')
        newAction.triggered.connect(self.onNew)

        fileMenu.addAction(newAction)

        

        #Show SQL table of data in seperate window
        self.model = self.create_model()
        column_names = ["null", "FI Name", "Synapsys Number", "Bank or CU", "Bank Core User", "Partition"]
        for i in range(self.model.columnCount()):
            self.model.setHeaderData(i, QtCore.Qt.Horizontal, column_names[i])
        
        self.view = self.create_view(self.model)
        self.view.setWindowTitle("FI Data")
        self.view.resize(733, 800)
        self.view.show()

    def onNew(self):
        self.view.show()
        

    def initial_update_ui(self, index):
        if index == 0: 
            return
        # disconnect initial signal
        self.init_dropdown.currentIndexChanged.disconnect(self.initial_update_ui)
        # remove 'Please select an option'
        self.init_dropdown.removeItem(0)
        # reconnect signal to regular update_ui
        self.init_dropdown.currentIndexChanged.connect(self.update_ui)
        # call update_ui for initial selection
        self.update_ui(self.init_dropdown.currentIndex())

    #updates our UI depending on the option selected
    def update_ui(self, index):
        self.stack.setCurrentIndex(index)
        self.stack.show()
        self.queue.show()
        self.process_button.show()
        self.remove_button.show()

    #Remove 'Please select an option' if it is still there
    def remove_placeholder(self):
    
        if self.init_dropdown.itemText(0) == 'Please select an option':
            self.init_dropdown.removeItem(0)

    #Import CSV function
    def import_csv(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Import CSV', QtCore.QDir.currentPath(), 'CSV Files (*.csv)')
        if filename:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                print(list(reader))

    #think this is old
    #def update_ui(self, index):
    #    if index >= 0:
    #        self.stack.setCurrentIndex(index)
    #        self.stack.show()
    #        self.queue.show()
    #        self.process_button.show()
    #        self.remove_button.show()
    
    #look up the email in the email field and get the corresponding extension from the Agent List Smartsheet
    def get_extension(self):
        found = False
        email = self.agent_email_entry.text()
        extension_entry = self.agent_extension_entry
        for row in agent_list_sheet.rows:
            citjha_email = row.cells[citjha_email_col_index].value
            citjha_email = str(citjha_email)
            if citjha_email.lower() == email:
                found = True
                extension = row.cells[extension_col_index].value
                extension = str(extension)
                extension = extension[:-2]
                print(extension)
                extension_entry.setText(extension)
                break
        if not found:
                show_warning("Smartsheet Data Lookup Error", f"No extension found for the email {email}")
                return
    
    #look up the extension in the extension field and get the corresponding email from the Agent List Smartsheet
    def get_email(self):
        found = False
        extension_entry = self.agent_extension_entry
        email_entry = self.agent_email_entry
        for row in agent_list_sheet.rows:
            extension = row.cells[extension_col_index].value
            if extension_entry.text() == '':
                show_warning('Data Input Error', f'Please enter an extension!')
                return
            elif extension == int(extension_entry.text()):
                found = True
                citjha_email = row.cells[citjha_email_col_index].value
                citjha_email = str(citjha_email.lower())
                email_entry.setText(citjha_email)
                break
        if not found:
            show_warning('Smartsheet Lookup Error', f'No email address found for the extension {extension_entry.text()} on the Agent List Smartsheet!')
    
    #Clear our fields out, save them to local variables for the undo function if we need to restore that data
    def clear_fields(self):
        
        self.agent_email_entry.clear()
        self.agent_extension_entry.clear()
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)
        
        #QApplication.processEvents()
        pass
    
    #This function will be to process the claims we have in the queue to one .json file
    def process_queue(self):
        # Add your code to process queue here
        print("Claims processed")
        pass

    #This function will be to remove the selected claim(s) from the processing queue
    def remove_entry(self):
        # Add your code to remove queue entry here
        print("Selected item removed")
        pass
    
    def create_model(self):
        self.model = QtSql.QSqlTableModel()
        self.model.setTable('banks')
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.model.select()
        return self.model


    def create_view(self,model):
        self.view = QtWidgets.QTableView()
        self.view.setModel(model)
        self.view.hideColumn(0)
        self.view.resizeColumnsToContents()
        return self.view

"""
    
class ClearUndo():
    # Use a class variable to keep track of how many times instance has been run
    _instance_count = 0

    def __init__(self):
        # Initialize the class attributes to None
        self.customernamecopy = None
        self.reasoncopy = None
        self.referencecopy = None
        self.contactinfocopy = None
        self.debitcardcopy = None
        self.transactionscopy = None
        
        # Set self.clear based on the value of the _first_run flag
        ClearUndo._instance_count += 1

        if ClearUndo._instance_count % 2 == 1:
            self.clear = True
        else:
            self.clear = False
            
        self.clear_undo()
    
    def clear_undo(self):
        
        if self.clear == True:
            # Assign values to the class attributes
            ClearUndo.agent_email_copy = MainWindow.agent_email_entry.text()
            ClearUndo.agent_extension_copy = MainWindow.agent_extension_entry.text()
            ClearUndo.checkbox1_1_copy = MainWindow.checkbox1_1.isChecked()
            ClearUndo.checkbox1_2_copy = MainWindow.checkbox1_2.isChecked()
            ClearUndo.checkbox1_3_copy = MainWindow.checkbox1_3.isChecked()
            ClearUndo.checkbox1_4_copy = MainWindow.checkbox1_4.isChecked()
            ClearUndo.checkbox1_5_copy = MainWindow.checkbox1_5.isChecked()
            ClearUndo.checkbox1_6_copy = MainWindow.checkbox1_6.isChecked()

            def clear_fields():
                MainWindow.agent_email_entry.clear()
                MainWindow.agent_extension_entry.clear()
                MainWindow.checkbox1_1.setChecked(False)
                MainWindow.checkbox1_2.setChecked(False)
                MainWindow.checkbox1_3.setChecked(False)
                MainWindow.checkbox1_4.setChecked(False)
                MainWindow.checkbox1_5.setChecked(False)
                MainWindow.checkbox1_6.setChecked(False)
                return

            clear_fields()
            self.clear = False
            MainWindow.clear.setText('Undo')
            return

        if self.clear == False:
            MainWindow.clear.setText('Undo')
            # Use the class attributes in the second if statement
            MainWindow.agent_email_entry.setText(ClearUndo.agent_email_copy)
            MainWindow.agent_extension_entry.setText(ClearUndo.agent_extension_copy)
            for i in range[1, 6]:
                checkbox_copy = getattr(ClearUndo, f"checkbox1_{i}_copy")
                if checkbox_copy:
                    MainWindow.checkbox1_[i].setChecked(True)
                else:
                    MainWindow.checkbox1_[i].setChecked(False)
            self.clear = True
            return
"""


#Main loop
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
