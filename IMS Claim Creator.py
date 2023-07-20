import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
import json
import csv
import os
import sqlite3
from smartsheet import Smartsheet
from smartsheet import sheets
import string

#Name GUI Window
app = Tk()

#get the FI Servicing Sheets and Script sheets with Core user, partition and synapsys numbers and uses the API Token for the jhCC Support Smartsheet User.
os.environ['SMARTSHEET_ACCESS_TOKEN'] = $API_TOKEN
fi_servicing_sheet_ID = 494759136520068 # name: Current FI Servicing
agent_list_sheet_ID = 735036543657860 # name: Agent List
bank_core_sheet_ID = 7891957159618436 # name: IMS PROGRAM 1 Agent : Banking FI Cores
bank_synapsys_sheet_ID = 8999703313442692 #name: IMS PROGRAM 1 Agent : Banking Synapsys
cu_synapsys_sheet_ID = 846684570838916 # name: IMS PROGRAM 1 Agent : CU Synapsys
trainer_fi_sheet_ID = 2405415385360260 # name: IMS PROGRAM Trainer Script Synapsys

# create db in memory Connection and Cursor objects
db = sqlite3.connect(':memory:')
cur = db.cursor()

#setup operations list index
#global jsonArray
global opindex
global op_list
op_list = Listbox(app, height=8, width=80, border=0)
opindex = 0
#global v
v = StringVar()
jsonArray = []
alphabet = string.ascii_lowercase + string.digits

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

# create bank list table in database
cur.execute("CREATE TABLE banks (ID INTEGER PRIMARY KEY, fi_name TEXT, fi_syn TEXT, fi_type TEXT, bank_core TEXT, partition TEXT)")
db.commit()

#create column map for relevant columns to use for bank sql import
column_indices = {col.title: i for i, col in enumerate(fi_sheet.columns)}

#return the core user and partition information from the corresponding smartsheet for the bank name input
def get_bank_core_data(fi_name):
    column_indices = {col.title: i for i, col in enumerate(bank_core_sheet.columns)}
    for row in bank_core_sheet.rows:
        if row.cells[column_indices['Bank Name']].value == fi_name:
            return row.cells[column_indices['FI Core']].value, row.cells[column_indices['Bank ID']].value
    return None, None

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
        cur.execute("INSERT INTO banks VALUES (NULL, ?, ?, ?, ?, ?)", (values[0], values[1], values[2], values[3], values[4]))
    db.commit()
    print(f"Loaded {bankcount} Banks and {cucount} from Current FI Servicing Smartsheet")
except:
    messagebox.showerror('DATABASE WARNING','Please reopen program!')

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

#fill in scrollbar list of banks from SQL table
def populate_list():
    bank_list.delete(0, END)
    cur.execute("SELECT * FROM banks")
    for row in cur.fetchall():
        bank_list.insert(END, row)

#open CSV and set the file path as a string variable
def import_csv_data():
    global v
    csv_file_path = askopenfilename()
    v.set(csv_file_path)

def custom_bank_list():
    b = StringVar
    banklist_file_path = askopenfilename()
    b.banklist_file_path

#load selected bank into fields
def select_item(event):
    try:
        global selected_item
        index = bank_list.curselection()[0]
        selected_item = bank_list.get(index)

        fi_Name_entry.delete(0, END)
        fi_Name_entry.insert(END, selected_item[1])
        fi_syn_entry.delete(0, END)
        fi_syn_entry.insert(END, selected_item[2])
        FI_type_entry.delete(0,END)
        FI_type_entry.insert(END, selected_item[3])
        bank_core_entry.delete(0, END)
        bank_core_entry.insert(END, selected_item[4])
        bank_partition_entry.delete(0, END)
        bank_partition_entry.insert(END, selected_item[5])

    except IndexError:
        pass

#not used
"""
#select claim from operation queue
def select_claim(event):
    try:
        global selected_claim
        index = op_list.curselection()[0]
        selected_claim = op_list.get(index)
        return selected_claim
    except IndexError:
        pass
"""
"""
def (jsonArray, op_list):

    index = op_list.curselection()
    if not index:
        messagebox.showerror('Error', 'Please select an item to delete')
        return
    selected_claim = op_list.get(index)
    selected_claim_name = op_list.get(index)
    selected_claim = selected_claim.rsplit(" ",1)[-1]
    jsonArray = str(jsonArray)
    json_string = json.loads(jsonArray)
    #for i in range(len(json_data)):
    start = json_string.find('{"id":"' + selected_item + '"')
    end = json_string.find("}", start) + 1
    json_string = json_string[:start] + json_string[end:]
    print(json_string)  
    
    selected_claim = op_list.get(index)
    selected_claim_name = op_list.get(index)
    selected_claim = selected_claim.rsplit(" ",1)[-1]
    print(selected_claim)
    jsonArray = [item for item in jsonArray if item.get("id") != selected_claim]
    messagebox.showinfo('Operation Completed', f'{selected_claim_name} has been deleted from the queue!')
    op_list.delete(index)
    print(jsonArray)"""

#functions for creating and deleting claims from processing queue, create claim function worked as intended. Delete claim needs further refining.
"""
def delete_claim(jsonArray, selected_item):
    print(jsonArray)
    index = op_list.curselection()
    if not index:
        messagebox.showerror('Error', 'Please select an item to delete')
        return
    selected_claim = op_list.get(index)
    jsonArray = [obj for obj in jsonArray if obj[{}] == {}]
    print(jsonArray_without_id)
    return json.dumps(jsonArray)

def create_claim(jsonArray):
    with open("IMS CLAIMS.json", "w") as outfile:
        if jsonArray == []:
            messagebox.showerror('Operation Warning', 'The file you are trying to create would be empty. Please complete an operation and retry!')
            return
        # remove the 'id' key from each dictionary
        jsonArray_without_id = [{k: v for k, v in d.items() if k != 'id'} for d in jsonArray]
        outfile.write(json.dumps(jsonArray_without_id, indent=4))
        messagebox.showinfo('Operation Completed', f'The claims in the Operation Completed list have been created in file IMS CLAIMS.json in the same directory as this program!')
        print(op_list.get(0, END))
        jsonArray = []
        op_list.delete(0,END)
"""

#clear input from bank fields
def clear_text():
    fi_Name_entry.delete(0, END)
    fi_syn_entry.delete(0, END)
    FI_type_entry.delete(0, END)
    bank_core_entry.delete(0, END)
    bank_partition_entry.delete(0, END)

def get_extension():
    found = False
    for row in agent_list_sheet.rows:
        citjha_email = row.cells[citjha_email_col_index].value
        citjha_email = str(citjha_email)
        if citjha_email.lower() == email_entry.get():
            found = True
            extension = row.cells[extension_col_index].value
            extension = int(extension)
            extension_entry.delete(0,END)
            extension_entry.insert(0, extension)
            break
    if not found:
            messagebox.showerror('Smartsheet Lookup Error', f'No extension found for the email address {email_text.get()} on the Agent List Smartsheet!')
            return

def get_email():
    found = False
    for row in agent_list_sheet.rows:
        extension = row.cells[extension_col_index].value
        if extension == int(extension_entry.get()):
            found = True
            citjha_email = row.cells[citjha_email_col_index].value
            citjha_email = str(citjha_email.lower())
            email_entry.delete(0, END)
            email_entry.insert(0, citjha_email)
            break
    if not found:
        messagebox.showerror('Smartsheet Lookup Error', f'No email address found for the extension {extension_text.get()} on the Agent List Smartsheet!')

        

#Create single Bank Claim
def create_bank_core_claim():
    global opindex
    jsonArray = []
    emailentry = email_text.get()  
    if fi_Name_text.get() == '' or fi_syn_text.get() == '' or FI_type_text.get() =='':
        messagebox.showerror('Data Input Error', 'Please select an FI first')
        return
    elif email_text.get() == '' or extension_text.get() == '':
        messagebox.showerror('Data Input Error', 'Please input Agent information')
        return
    elif emailentry[len(emailentry)-11:len(emailentry)] != '@citjha.com':
        messagebox.showerror('Data Input Error', 'Please check email for accuracy')
        return
    else:
        template = {
            "userName": email_text.get(),
            "appliesTo": "http://jackhenry.com/application/core",
            "default": False,
            "description": fi_Name_text.get(),
            "routingId": "1",
            "name": bank_core_text.get(),
            "context": f"iAdapter={bank_partition_text.get()};"
        }
        with open(f"{email_text.get()} {fi_Name_text.get()} Core claim.json", "w") as outfile:
            outfile.write(json.dumps(template, indent=4))
            messagebox.showinfo('Operation Completed', f'{email_text.get()} {fi_Name_text.get()} Core claim has been created!')
        op_list.insert(opindex, f'{fi_Name_text.get()} {email_text.get()} Core claim')
        opindex = (opindex+1)
    

#create single synapsys claim
def create_synapsys_claim():
    global opindex
    jsonArray = []
    template = {
                "userName": email_text.get(),
                "appliesTo": "http://jackhenry.com/application/synapsys",
                "default": False,
                "description": fi_Name_text.get(),
                "routingId": "1",
                "name":f"JHA{extension_text.get()}",
                "context": f"BANK={fi_syn_text.get()};"
                }
    emailentry = email_text.get()
    ext = extension_text.get()
    emaillist=[]
    if fi_Name_text.get() == '' or fi_syn_text.get() == '' or FI_type_text.get() =='':
        messagebox.showerror('Data Input Error', 'Please select an FI first')
        return
    elif email_text.get() == '' or extension_text.get() == '':
        messagebox.showerror('Data Input Error', 'Please input Agent information')
        return
    elif len(ext) != 4 or (not ext.isdigit() or (ext[0] != '4' and ext[0] != '5')):
        messagebox.showerror('Data Input Error', 'Please check extension for accuracy')
        return
    elif emailentry[len(emailentry)-11:len(emailentry)] != '@citjha.com':
        messagebox.showerror('Data Input Error', 'Please check email for accuracy')
        return
    else:    
        for row in agent_list_sheet.rows:
            email = str(row.cells[citjha_email_col_index].value).lower()
            if row.cells[citjha_email_col_index].value is None:
                continue
            emaillist.append(email)
        if emailentry not in emaillist:
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not on the Agent List Smartsheet, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':                    
                with open(f"{email_text.get()} {fi_Name_text.get()} Synapsys claim.json", "w") as outfile:
                    outfile.write(json.dumps(template, indent=4))
                    messagebox.showinfo('Operation Completed', f'{email_text.get()} {fi_Name_text.get()} Synapsys claim has been created!')
                    op_list.insert(opindex, f'{email_text.get()} {fi_Name_text.get()} Synapsys claim')
                    opindex = (opindex+1)    
                    
        else:
                with open(f"{email_text.get()} {fi_Name_text.get()} Synapsys claim.json", "w") as outfile:
                    outfile.write(json.dumps(template, indent=4))
                    messagebox.showinfo('Operation Completed', f'{email_text.get()} {fi_Name_text.get()} Synapsys claim has been created!')
                    op_list.insert(opindex, f'{email_text.get()} {fi_Name_text.get()} Synapsys claim')
                    opindex = (opindex+1)


#create all Bank Core for one agent
def create_single_agent_all_bank_core_claim():
    global opindex
    global skill
    jsonArray = []
    emailentry = email_text.get()
    ext = extension_text.get()
    emaillist=[]
    if email_text.get() == '' or extension_text.get() == '':
        messagebox.showerror('Data Input Error', 'Please input Agent information')
        return
    elif emailentry[len(emailentry)-11:len(emailentry)] != '@citjha.com':
        messagebox.showerror('Data Input Error', 'Please check email for accuracy')
        return
    else:    
        for row in agent_list_sheet.rows:
            email = str(row.cells[citjha_email_col_index].value).lower()
            if emailentry == email:
                skill = row.cells[skill_col_index].value
            if row.cells[citjha_email_col_index].value is None:
                continue
            emaillist.append(email)  
        if emailentry not in emaillist:
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not on the Agent List Smartsheet, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':

        #elif fi_Name_text.get() != ''
                                # Select all rows from the database
                        query = "SELECT fi_name, fi_syn, bank_core, partition FROM banks WHERE fi_type = 'Bank'"
                        cur.execute(query)
                            # Iterate through the rows in the database
                        for (db_column1, db_column2, db_column3, db_column4) in cur:
                            data = {
                                "userName": email_text.get(),
                                "appliesTo": "http://jackhenry.com/application/core",
                                "default": False,
                                "description": db_column1,
                                "routingId": "1",
                                "name": db_column3,
                                "context":f"iAdapter={db_column4};"
                            }
                            if db_column3 == 'null':
                                print(f'No Core User found for {db_column1}, skipping!')
                                continue
                            if db_column4 is None:
                                print(f'No Partition data found for {db_column1}, skipping!')
                                continue
                            # Create a dictionary with the data
                            #open a file to put the object(s) with our requested info in to a json file
                            with open(f'All_Bank_Core_{email_text.get()}.json', 'w') as json_file:
                                jsonArray.append(data)
                                json_file.write(json.dumps(jsonArray, indent=4)) 
                        messagebox.showinfo('Operation Completed', f'The All Bank Core claim for {email_text.get()} have been created!')
                        op_list.insert(opindex, f'{email_text.get()} all Bank Core claims')
                        opindex = (opindex+1)   
            
        elif skill != 'Banking':
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not listed as a Banking agent, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':
                                # Select all rows from the database
                        query = "SELECT fi_name, fi_syn, bank_core, partition FROM banks WHERE fi_type = 'Bank'"
                        cur.execute(query)
                            # Iterate through the rows in the database
                        for (db_column1, db_column2, db_column3, db_column4) in cur:
                            data = {
                                "userName": email_text.get(),
                                "appliesTo": "http://jackhenry.com/application/core",
                                "default": False,
                                "description": db_column1,
                                "routingId": "1",
                                "name": db_column3,
                                "context":f"iAdapter={db_column4};"
                            }
                            if db_column3 == 'null':
                                print(f'No Core User found for {db_column1}, skipping!')
                                continue
                            if db_column4 is None:
                                print(f'No Partition data found for {db_column1}, skipping!')
                                continue
                            # Create a dictionary with the data
                            #open a file to put the object(s) with our requested info in to a json file
                            with open(f'All_Bank_Core_{email_text.get()}.json', 'w') as json_file:
                                jsonArray.append(data)
                                json_file.write(json.dumps(jsonArray, indent=4)) 
                        messagebox.showinfo('Operation Completed', f'The All Bank Core claim for {email_text.get()} have been created!')
                        op_list.insert(opindex, f'{email_text.get()} all Bank Core claims')
                        opindex = (opindex+1)                
        else:
                        # Select all rows from the database
                query = "SELECT fi_name, fi_syn, bank_core, partition FROM banks WHERE fi_type = 'Bank'"
                cur.execute(query)
                    # Iterate through the rows in the database
                for (db_column1, db_column2, db_column3, db_column4) in cur:
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/core",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": db_column3,
                        "context":f"iAdapter={db_column4};"
                    }
                    if db_column3 == 'null':
                        print(f'No Core User found for {db_column1}, skipping!')
                        continue
                    if db_column4 is None:
                        print(f'No Partition data found for {db_column1}, skipping!')
                        continue
                    # Create a dictionary with the data
                    #open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_Bank_Core_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4))              
                messagebox.showinfo('Operation Completed', f'The All Bank Core claim for {email_text.get()} have been created!')
                op_list.insert(opindex, f'{email_text.get()} all Bank Core claims')
                opindex = (opindex+1)

#create all Bank Synapsys for one agent
def create_single_agent_all_bank_synapsys_claim():
    global opindex
    global skill
    jsonArray = []
    emailentry = email_text.get()
    ext = extension_text.get()
    emaillist=[]
    if email_text.get() == '' or extension_text.get() == '':
        messagebox.showerror('Data Input Error', 'Please input Agent information')
        return
    elif len(ext) != 4 or (not ext.isdigit() or (ext[0] != '4' and ext[0] != '5')):
        messagebox.showerror('Data Input Error', 'Please check extension for accuracy')
        return
    elif emailentry[len(emailentry)-11:len(emailentry)] != '@citjha.com':
        messagebox.showerror('Data Input Error', 'Please check email for accuracy')
        return
    else:    
        for row in agent_list_sheet.rows:
            email = str(row.cells[citjha_email_col_index].value).lower()
            if emailentry == email:
                skill = row.cells[skill_col_index].value
            if row.cells[citjha_email_col_index].value is None:
                continue
            emaillist.append(email)  
        if emailentry not in emaillist:
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not on the Agent List Smartsheet, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':
            # This is the row that we want
                # Select all rows from the database
                query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'Bank'"
                cur.execute(query)
                # Iterate through the rows in the database
                for (db_column1, db_column2) in cur:
                    # Create a dictionary with the data
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": f"JHA{extension_text.get()}",
                        "context":f"BANK={db_column2};"
                    }
                    if db_column2 is None:
                        print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                        continue
                    # open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_Bank_Synapsys_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4))      
                messagebox.showinfo('Operation Completed', f'{email_text.get()} All Banks Synapsys claim has been created!')
                op_list.insert(opindex, f'{email_text.get()} All Banks Synapsys claim')
                opindex = (opindex+1)
        elif skill != 'Banking':
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not listed as a Banking agent, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':
                # Select all rows from the database
                query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'Bank'"
                cur.execute(query)
                # Iterate through the rows in the database
                for (db_column1, db_column2) in cur:
                    # Create a dictionary with the data
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": f"JHA{extension_text.get()}",
                        "context":f"BANK={db_column2};"
                    }
                    if db_column2 is None:
                        print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                        continue
                    # open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_Bank_Synapsys_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4))
                messagebox.showinfo('Operation Completed', f'{email_text.get()} All Banks Synapsys claim has been created!')
                op_list.insert(opindex, f'{email_text.get()} All Banks Synapsys claim')
                opindex = (opindex+1)
        else:
                # Select all rows from the database
                query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'Bank'"
                cur.execute(query)
                # Iterate through the rows in the database
                for (db_column1, db_column2) in cur:
                    # Create a dictionary with the data
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": f"JHA{extension_text.get()}",
                        "context":f"BANK={db_column2};"
                    }
                    if db_column2 is None:
                        print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                        continue
                    # open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_Bank_Synapsys_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4))
                messagebox.showinfo('Operation Completed', f'{email_text.get()} All Banks Synapsys claim has been created!')
                op_list.insert(opindex, f'{email_text.get()} All Banks Synapsys claim')
                opindex = (opindex+1)

#create all CU Synapsys for one agent
def create_single_agent_all_CU_synapsys_claim():
    global opindex
    global skill
    jsonArray = []
    emailentry = email_text.get()
    ext = extension_text.get()
    emaillist=[]
    if email_text.get() == '' or extension_text.get() == '':
        messagebox.showerror('Data Input Error', 'Please input Agent information')
        return
    elif len(ext) != 4 or (not ext.isdigit() or (ext[0] != '4' and ext[0] != '5')):
        messagebox.showerror('Data Input Error', 'Please check extension for accuracy')
        return
    elif emailentry[len(emailentry)-11:len(emailentry)] != '@citjha.com':
        messagebox.showerror('Data Input Error', 'Please check email for accuracy')
        return
    else:    
        for row in agent_list_sheet.rows:
            email = str(row.cells[citjha_email_col_index].value).lower()
            if emailentry == email:
                skill = row.cells[skill_col_index].value
            if row.cells[citjha_email_col_index].value is None:
                continue
            emaillist.append(email) 
        if emailentry not in emaillist:
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not on the Agent List Smartsheet, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':
            # This is the row that we want
                # Select all rows from the database
                query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'CU'"
                cur.execute(query)
                # Iterate through the rows in the database
                for (db_column1, db_column2) in cur:
                    # Create a dictionary with the data
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": f"JHA{extension_text.get()}",
                        "context":f"BANK={db_column2};"
                    }
                    if db_column2 is None:
                        print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                        continue
                    # open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_CU_Synapsys_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4))  
                messagebox.showinfo('Operation Completed', f'{email_text.get()} All CU Synapsys claim has been created!')
                op_list.insert(opindex, f'{email_text.get()} All CU Synapsys claim')
                opindex = (opindex+1)
        elif skill != 'CU':
            msg_box = messagebox.askquestion("Please Confirm","The agent info input is not listed as a CU agent, are you sure you want to continue?", icon='warning')
            if msg_box == 'no':
                messagebox.showerror('Operation Cancelled', 'No Claims Created!')
                return
            elif msg_box == 'yes':
                # Select all rows from the database
                query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'CU'"
                cur.execute(query)
                # Iterate through the rows in the database
                for (db_column1, db_column2) in cur:
                    # Create a dictionary with the data
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": f"JHA{extension_text.get()}",
                        "context":f"BANK={db_column2};"
                    }
                    if db_column2 is None:
                        print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                        continue
                    # open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_CU_Synapsys_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4)) 
            messagebox.showinfo('Operation Completed', f'{email_text.get()} All CU Synapsys claim has been created!')
            op_list.insert(opindex, f'{email_text.get()} All CU Synapsys claim')
            opindex = (opindex+1)             
        else:
                # Select all rows from the database
                query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'CU'"
                cur.execute(query)
                # Iterate through the rows in the database
                for (db_column1, db_column2) in cur:
                    # Create a dictionary with the data
                    data = {
                        "userName": email_text.get(),
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": db_column1,
                        "routingId": "1",
                        "name": f"JHA{extension_text.get()}",
                        "context":f"BANK={db_column2};"
                    }
                    if db_column2 is None:
                        print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                        continue
                    # open a file to put the object(s) with our requested info in to a json file
                    with open(f'All_CU_Synapsys_{email_text.get()}.json', 'w') as json_file:
                        jsonArray.append(data)
                        json_file.write(json.dumps(jsonArray, indent=4))      
                messagebox.showinfo('Operation Completed', f'{email_text.get()} All CU Synapsys claim has been created!')
                op_list.insert(opindex, f'{email_text.get()} All CU Synapsys claim')
                opindex = (opindex+1)




def create_trainer_scripts_claim():
    global opindex
    jsonArray = []
    banklist = []
    emailentry = email_text.get()
    ext = extension_text.get()
    if email_text.get() == '' or extension_text.get() == '':
        messagebox.showerror('Data Input Error', 'Please input Agent information')
        return
    elif len(ext) != 4 or (not ext.isdigit() or (ext[0] != '4' and ext[0] != '5')):
        messagebox.showerror('Data Input Error', 'Please check extension for accuracy')
        return
    elif emailentry[len(emailentry)-11:len(emailentry)] != '@citjha.com':
        messagebox.showerror('Data Input Error', 'Please check email for accuracy')
        return
    for row in trainer_fi_sheet.rows:
        if row.cells[trainer_banks_col_index].value is None:
            continue
        else:
            banklist.append(row.cells[trainer_banks_col_index].value)
    for i in banklist:
        query = "SELECT fi_name, fi_syn FROM banks WHERE fi_name = ?"
        cur.execute(query, (i,))
        # Iterate through the rows in the database
        for (db_column1, db_column2) in cur:
            # Create a dictionary with the data
            data = {
                "userName": email_text.get(),
                "appliesTo": "http://jackhenry.com/application/synapsys",
                "default": False,
                "description": db_column1,
                "routingId": "1",
                "name": f"JHA{extension_text.get()}",
                "context": f"BANK={db_column2};"  # Use the value from the second column of the retrieved row
            }
            if db_column2 is None:
                print(f'No Synapsys Bank Number found for {db_column1}, skipping!')
                continue
            # Append the dictionary to the list
            jsonArray.append(data)
    for i in banklist:
        query2 = "SELECT fi_name, bank_core, partition FROM banks WHERE fi_type = 'Bank' AND fi_name = ?"
        cur.execute(query2, (i,))
            # Iterate through the rows in the database
        for (db_column1, db_column2, db_column3) in cur:
            # Create a dictionary with the data 
            data = {
                "userName": email_text.get(),
                "appliesTo": "http://jackhenry.com/application/core",
                "default": False,
                "description": db_column1,
                "routingId": "1",
                "name": db_column2,
                "context": f"iAdapter={db_column3};"  # Use the value from the second column of the retrieved row
            }
            if db_column2 == 'null':
                print(f'No Core User found for {db_column1}, skipping!')
                continue
            if db_column3 is None:
                print(f'No Partition found for {db_column1}, skipping!')
                continue
            # Append the dictionary to the list
            jsonArray.append(data)
        with open(f'{email_text.get()} Trainer Claim.json', 'w') as json_file:
            json_file.write(json.dumps(jsonArray, indent=4)) 
    # Write the list of dictionaries to the JSON file

    messagebox.showinfo('Operation Completed', f'{email_text.get()} Trainer claim has been created!')
    op_list.insert(opindex, f'{email_text.get()} Trainer claim')
    opindex = (opindex+1)





#create all CU Synapsys claim from CSV file
def create_all_CU_synapsys_csv_claim():
    jsonArray = []
    global opindex
    if v.get() == '':
        messagebox.showerror('Attention', 'Please select a CSV file!')

    else:

        # Open the CSV file
        with open(v.get(), 'r') as csv_file:
            # Create a CSV reader
            reader = csv.reader(csv_file)
            rowcount = 1

            # Iterate through the rows in the CSV file
            for row in reader:
                # Get the data from the CSV file
                csv_column1 = row[0]  # userName
                csv_column2 = row[1]  # extension
                
                if row[0][len(row[0])-11:len(row[0])] != '@citjha.com':
                    messagebox.showerror('Data Input Error', f'Please check email column for accuracy. On row {rowcount}, the field {row[0]} is not formatted correctly!')
                    return
                #check that all extensions are valid and if not return the row with the bad data
                elif len(row[1]) != 4 or (not row[1].isdigit() or (row[1][0] != '4' and row[1][0] != '5')):
                    messagebox.showerror('Data Input Error', f'Please check extension column for accuracy. On row {rowcount}, the field {row[1]} is not formatted correctly!')
                    return
                else:
                # Select all rows from the database
                    rowcount += 1

                    query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'CU'"
                    cur.execute(query)
                    for row[0] in csv_column1:
                        # Iterate through the rows in the database
                        for (db_column1, db_column2) in cur:
                            # Create a dictionary with the data
                            data = {
                                "userName": csv_column1,
                                "appliesTo": "http://jackhenry.com/application/synapsys",
                                "default": False,
                                "description": db_column1,
                                "routingId": "1",
                                "name": f"JHA{csv_column2}",
                                "context":f"BANK={db_column2};"
                            }
                            #open a file to put the object(s) with our requested info in to a json file

                            jsonArray.append(data)
        rowcount -= 1        
        with open(f'{v.get()} ALL CU Synapsys Claim.json', 'w') as json_file:
            json_file.write(json.dumps(jsonArray, indent=4))
        messagebox.showinfo('Operation Completed', f'{rowcount} agents from {v.get()} have had All CU Synapsys claims created!')
        op_list.insert(opindex, 'CSV import All CU Synapsys claim')
        opindex = (opindex+1)


#create all banks synapsys claim for CSV file
def create_all_bank_synapsys_csv_claim():
    jsonArray = []
    global opindex
    if v.get() == '':
        messagebox.showerror('Attention', 'Please select a CSV file!')
    else:

        # Open the CSV file
        with open(v.get(), 'r') as csv_file:

            # Create a CSV reader
            reader = csv.reader(csv_file)
            rowcount = 1
            # Iterate through the rows in the CSV file
            for row in reader:
                # Get the data from the CSV file
                csv_column1 = row[0]  # userName
                csv_column2 = row[1]  # extension
                #row[1] = int(row[1])
                #check that all emails are valid and if not return the row with the bad data
                if row[0][len(row[0])-11:len(row[0])] != '@citjha.com':
                    messagebox.showerror('Data Input Error', f'Please check email column for accuracy. On row {rowcount}, the field {row[0]} is not formatted correctly!')
                    return
                #check that all extensions are valid and if not return the row with the bad data
                elif len(row[1]) != 4 or (not row[1].isdigit() or (row[1][0] != '4' and row[1][0] != '5')):
                    messagebox.showerror('Data Input Error', f'Please check extension column for accuracy. On row {rowcount}, the field {row[1]} is not formatted correctly!')
                    return
                else:
                # Select all rows from the database
                    rowcount += 1
                    query = "SELECT fi_name, fi_syn FROM banks WHERE fi_type = 'Bank'"
                    cur.execute(query)
                    for row[0] in csv_column1:
                        # Iterate through the rows in the database
                        for (db_column1, db_column2) in cur:
                            #define our template for the object in the JSON file
                            data = {
                                "userName": csv_column1,
                                "appliesTo": "http://jackhenry.com/application/synapsys",
                                "default": False,
                                "description": db_column1,
                                "routingId": "1",
                                "name": f"JHA{csv_column2}",
                                "context":f"BANK={db_column2};"
                            }
                            #open a file to put the object(s) with our requested info in to a json file
                            jsonArray.append(data)
        rowcount -= 1
        with open(f'{v.get()} ALL Banks Synapsys Claim.json', 'w') as json_file:
            json_file.write(json.dumps(jsonArray, indent=4))
        messagebox.showinfo('Operation Completed', f'{rowcount} agents from {v.get()} have had All Bank Synapsys claims added to the queue for processing!')
        op_list.insert(opindex, 'CSV import All Banks Synapsys claim')
        opindex = (opindex+1)

#create all banks core claim from CSV file
def create_all_bank_core_csv_claim():
    jsonArray = []
    global opindex
    if v.get() == '':
        messagebox.showerror('Attention', 'Please select a CSV file!')
        # Connect to the database
    else:

        # Open the CSV file
        with open(v.get(), 'r') as csv_file:
            # Create a CSV reader
            reader = csv.reader(csv_file)
            rowcount = 1

            # Iterate through the rows in the CSV file
            for row in reader:
                # Get the data from the CSV file
                csv_column1 = row[0]  # userName
                if row[0][len(row[0])-11:len(row[0])] != '@citjha.com':
                    messagebox.showerror('Data Input Error', f'Please check email column for accuracy. On row {rowcount}, the field {row[0]} is not formatted correctly!')
                    return
                else:
                # Select all rows from the database
                    rowcount += 1
                    query = "SELECT fi_name, fi_syn, bank_core, partition FROM banks WHERE fi_type = 'Bank'"
                    cur.execute(query)
                    for row[0] in csv_column1:
                        # Iterate through the rows in the database
                        for (db_column1, db_column2, db_column3, db_column4) in cur:
                            # Create a dictionary with the data
                            data = {
                                "userName": csv_column1,
                                "appliesTo": "http://jackhenry.com/application/core",
                                "default": False,
                                "description": db_column1,
                                "routingId": "1",
                                "name": db_column3,
                                "context":f"iAdapter={db_column4};"
                            }
                            #open a file to put the object(s) with our requested info in to a json file
                            jsonArray.append(data)   
        rowcount -= 1
        with open(f'{v.get()} ALL    Banks Core Claim.json', 'w') as json_file:
            json_file.write(json.dumps(jsonArray, indent=4))
        messagebox.showinfo('Operation Completed', f'{rowcount} agents from {v.get()} have had All Bank Core claims added to the queue for processing!')
        op_list.insert(opindex, 'CSV import All Banks Core claim')
        opindex = (opindex+1)







#create one CU Synapsys claim for All Agents from Agent list SMARTSHEET
def create_all_agent_CU_synapsys_claim(cusynopt, banksynopt, bankcoreopt):
        print(cusynopt, banksynopt, bankcoreopt)
        jsonArray = []
        global opindex
        seen_agent_name = set()
        agentcount = 0
        skillopt = StringVar
        if fi_Name_text.get() == '' or fi_syn_text.get() == '':
            messagebox.showerror('Data Input Error', 'Please Enter FI Information!')
            return
            # Iterate through the rows in the CSV file
        if cusynopt == 1:
            skillopt == 'CU'
        elif banksynopt == 1:
            skillopt == 'Banking'
        elif (cusynopt == 1 and banksynopt == 1) or (cusynopt == 1 and bankcoreopt == 1):
            messagebox.showerror('Data Input Error', 'Please check selected operations for accuracy!')
            return
        for row in agent_list_sheet.rows[start_row_index:]:
            # Get the values in the "Agent Name" and "Skill" columns
            agent_name = row.cells[agent_name_col_index].value
            skill = row.cells[skill_col_index].value
            extension = row.cells[extension_col_index].value    
            citjha_email = row.cells[citjha_email_col_index].value
            # Check if the skill is "CU"
            if extension is None:
                continue
            if citjha_email is None:
                continue
            if skill == skillopt:
                # Iterate through the rows in the database
                for row in agent_list_sheet.rows:
                    extension = str(extension)
                    extension = extension[len(extension)-6:len(extension)-2]
                    if agent_name in seen_agent_name:
                        continue
                    if citjha_email[len(citjha_email)-11:len(citjha_email)] != '@citjha.com':
                        messagebox.showerror('Smartsheet Data Error', f'Please check the CITJHA Domain column on the Agent list smartsheet and ensure the email is valid for {agent_name}!')
                        return
                    elif len(extension) != 4 or (not extension.isdigit() or (extension[0] != '4' and extension[0] != '5')):
                        messagebox.showerror('Smartsheet Data Error', f'Please check the Extension column on the Agent list smartsheet and ensure the extension is valid for {agent_name}!')
                        return
                    elif seen_agent_name is None:
                        pass
                    agentcount += 1
                # add fi_name value to seen set
                    seen_agent_name.add(agent_name)
                    # Create a dictionary with the data
                    data = {
                        "userName": citjha_email,
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": fi_Name_text.get(),
                        "routingId": "1",
                        "name": f"JHA{int(extension)}",
                        "context": f"BANK={fi_syn_text.get()};"
                    }
                    jsonArray.append(data)
                    if bankcoreopt == 'True':
                        data = {
                        "userName": citjha_email,
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": fi_Name_text.get(),
                        "routingId": "1",
                        "name": bank_core_text.get(),
                        "context": f"iAdapter={bank_partition_text.get()};"
                       }
                        jsonArray.append(data)
                    #open a file to put the object(s) with our requested info in to a json file
                    
            with open(f'ALL CU Agents {fi_Name_text.get()} Synapsys Claim.json', 'w') as json_file:
                json_file.write(json.dumps(jsonArray, indent=4))
        messagebox.showinfo('Operation Completed', f'All CU Agent {fi_Name_text.get()} Synapsys claim for {agentcount} agents from Smartsheet has been created!')
        op_list.insert(opindex, f'All CU Agent {fi_Name_text.get()} Synapsys claim')
        opindex = (opindex+1)
        """
        else:
            for row in agent_list_sheet.rows[start_row_index:]:
                    # Get the values in the "Agent Name" and "Skill" columns
                    agent_name = row.cells[agent_name_col_index].value
                    skill = row.cells[skill_col_index].value
                    extension = row.cells[extension_col_index].value
                    citjha_email = row.cells[citjha_email_col_index].value
                    # Check if the skill is "CU"
                    if extension is None:
                        continue
                    if citjha_email is None:
                        continue
                    if skill == 'CU':
                        # Iterate through the rows in the database
                        extension = str(extension)
                        for row in agent_list_sheet.rows:
                            extension = extension[len(extension)-6:len(extension)-2]
                            if agent_name in seen_agent_name:
                                continue
                            if citjha_email[len(citjha_email)-11:len(citjha_email)] != '@citjha.com':
                                messagebox.showerror('Smartsheet Data Error', f'Please check the CITJHA Domain column on the Agent list smartsheet and ensure the email is valid for {agent_name}!')
                                return
                            elif len(extension) != 4 or (not extension.isdigit() or (extension[0] != '4' and extension[0] != '5')):
                                messagebox.showerror('Smartsheet Data Error', f'Please check the Extension column on the Agent list smartsheet and ensure the extension is valid for {agent_name}!')
                                return
                            elif seen_agent_name is None:
                                pass
                        # add fi_name value to seen set
                            agentcount += 1
                            seen_agent_name.add(agent_name)
                            # Create a dictionary with the data
                            data = {
                                "userName": citjha_email,
                                "appliesTo": "http://jackhenry.com/application/synapsys",
                                "default": False,
                                "description": fi_Name_text.get(),
                                "routingId": "1",
                                "name": f"JHA{int(extension)}",
                                "context": f"BANK={fi_syn_text.get()};"
                            }
                            #open a file to put the object(s) with our requested info in to a json file
                            jsonArray.append(data)
            with open(f'ALL CU Agents {fi_Name_text.get()} Synapsys Claim.json', 'w') as json_file:
                json_file.write(json.dumps(jsonArray, indent=4))
            messagebox.showinfo('Operation Completed', f'All CU Agent {fi_Name_text.get()} Synapsys claim for {agentcount} agents from Smartsheet has been created!')
            op_list.insert(opindex, f'All CU Agent {fi_Name_text.get()} Synapsys claim')
            opindex = (opindex+1)
            """

#create one Bank Synapsys claim from Agent list SMARTSHEET
def create_all_agent_bank_synapsys_claim():
        jsonArray = []
        global opindex
        seen_agent_name = set()
        agentcount = 0
        if fi_Name_text.get() == '' or fi_syn_text.get() == '':
            messagebox.showerror('Data Input Error', 'Please Enter FI Information!')
            return
            # Iterate through the rows in the CSV file
        for row in agent_list_sheet.rows[start_row_index:]:
            # Get the values in the "Agent Name" and "Skill" columns
            agent_name = row.cells[agent_name_col_index].value
            skill = row.cells[skill_col_index].value
            extension = row.cells[extension_col_index].value
            citjha_email = row.cells[citjha_email_col_index].value
            # Check if the skill is "CU"
            if extension is None:
                continue
            if citjha_email is None:
                continue
            if skill == 'Banking':
                # Iterate through the rows in the database
                #for row in agent_list_sheet.rows:
                    extension = str(extension)
                    extension = extension[len(extension)-6:len(extension)-2]
                    if citjha_email[len(citjha_email)-11:len(citjha_email)] != '@citjha.com':
                        messagebox.showerror('Smartsheet Data Error', f'Please check the CITJHA Domain column on the Agent list smartsheet and ensure the email is valid for {agent_name}!')
                        return
                    elif len(extension) != 4 or (not extension.isdigit() or (extension[0] != '4' and extension[0] != '5')):
                        messagebox.showerror('Smartsheet Data Error', f'Please check the Extension column on the Agent list smartsheet and ensure the extension is valid for {agent_name}!')
                        return
                    if agent_name in seen_agent_name:
                        continue
                    elif seen_agent_name == '':
                        pass
                # add fi_name value to seen set
                    agentcount += 1
                    seen_agent_name.add(agent_name)
                     #Create a dictionary with the data
                    data = {
                        "userName": citjha_email,
                        "appliesTo": "http://jackhenry.com/application/synapsys",
                        "default": False,
                        "description": fi_Name_text.get(),
                        "routingId": "1",
                        "name": f"JHA{int(extension)}",
                        "context": f"BANK={fi_syn_text.get()};"
                    }
                    #open a file to put the object(s) with our requested info in to a json file
                    jsonArray.append(data)
        with open(f'ALL BANKING Agents {fi_Name_text.get()} Synapsys Claim.json', 'w') as json_file:
            json_file.write(json.dumps(jsonArray, indent=4))
        messagebox.showinfo('Operation Completed', f'All Bank Agent {fi_Name_text.get()} Core claim for {agentcount} agents from Smartsheet has been created!')
        op_list.insert(opindex, f'All Bank Agent {fi_Name_text.get()} Synapsys claim')
        opindex = (opindex+1)

#create one Bank Core claim from Agent list SMARTSHEET
def create_all_agent_bank_core_claim():
    
        jsonArray = []
        global opindex
        seen_agent_name = set()
        agentcount = 0
        if fi_Name_text.get() == '' or bank_partition_text.get() == '' or bank_core_text.get() == '':
            messagebox.showerror('Data Input Error', 'Please Enter FI Information!')
            return
            # Iterate through the rows in the CSV file
        for row in agent_list_sheet.rows[start_row_index:]:
            # Get the values in the "Agent Name" and "Skill" columns
            agent_name = row.cells[agent_name_col_index].value
            skill = row.cells[skill_col_index].value
            extension = row.cells[extension_col_index].value
            citjha_email = row.cells[citjha_email_col_index].value
            # Check if the skill is "CU"
            if extension is None:
                continue
            if citjha_email is None:
                continue
            if skill == 'Banking':
                # Iterate through the rows in the database
                #for row in agent_list_sheet.rows:
                    if citjha_email[len(citjha_email)-11:len(citjha_email)] != '@citjha.com':
                        messagebox.showerror('Smartsheet Data Error', f'Please check the CITJHA Domain column on the Agent list smartsheet and ensure the email is valid for {agent_name}!')
                        return
                    if agent_name in seen_fi_names:
                        continue
                    elif seen_agent_name == '':
                        pass
                # add fi_name value to seen set
                    agentcount += 1
                    seen_fi_names.add(agent_name)
                    # Create a dictionary with the data
                    data = {
                        "userName": citjha_email,
                        "appliesTo": "http://jackhenry.com/application/core",
                        "default": False,
                        "description": fi_Name_text.get(),
                        "routingId": "1",
                        "name": bank_core_text.get(),
                        "context": f"iAdapter={bank_partition_text.get()};"
                    }
                    #open a file to put the object(s) with our requested info in to a json file
                    jsonArray.append(data)
        with open(f'ALL BANKING Agents {fi_Name_text.get()} Core Claim.json', 'w') as json_file:
            json_file.write(json.dumps(jsonArray, indent=4))
        messagebox.showinfo('Operation Completed', f'All Bank Agent {fi_Name_text.get()} Core claim for {agentcount} agents from Smartsheet has been created!')
        op_list.insert(opindex, f'All Banking Agents {fi_Name_text.get()} Core claims')
        opindex = (opindex+1)        

#single instructions
single_label = Label(app, text='To make a single user claim enter the agents email including citjha.com domain and 4 digit extension, select the FI you would like to create the claim for (if applicable) and select your operation.', font=('bold', 18), wraplength=500, pady=10)
single_label.grid(row=0, column=0, columnspan=3, sticky=W)

#Email entry
email_text = StringVar()
email_label = Label(app, text='Email', font=('bold', 14))
email_label.grid(row=1, column=0, sticky=E)
email_entry = Entry(app, textvariable=email_text)
email_entry.grid(row=1, column=1, sticky=W)

#get extension button from smartsheet
get_extension_btn = ttk.Button(app, text='Get Extension!', width=15, command=get_extension)
get_extension_btn.grid(row=1, column=2, sticky=W)

#Extension Entry
extension_text = StringVar()
extension_label = Label(app, text='Extension', font=('bold', 14))
extension_label.grid(row=2, column=0, sticky=E)
extension_entry = Entry(app, textvariable=extension_text)
extension_entry.grid(row=2, column=1, sticky=W)

#get email button from smartsheet
get_extension_btn = ttk.Button(app, text='Get Email!', width=15, command=get_email)
get_extension_btn.grid(row=2, column=2, sticky=W)
"""
#create single bank core claim button
bank_core_btn = ttk.Button(app, text='Create Single Bank Core Claim!', width=25, command=create_bank_core_claim)
bank_core_btn.grid(row=3, column=0, sticky=N)

#create single synapsys claim button
synapsys_btn = ttk.Button(app, text='Create Single Synapsys Claim!', width=25, command=create_synapsys_claim)
synapsys_btn.grid(row=3, column=1, sticky=N)

#create single agent all core claim button
agent_bank_core_btn = ttk.Button(app, text='Create All Bank Core Claims for this Agent!', width=20, command=create_single_agent_all_bank_core_claim)
agent_bank_core_btn.grid(row=4, column=0, sticky=N)

#create single agent all  bank synapsys claim button
agent_synapsys_btn = ttk.Button(app, text='Create All Bank Synapsys Claims for this Agent!', width=20, command=create_single_agent_all_bank_synapsys_claim)
agent_synapsys_btn.grid(row=4, column=1, sticky=N)

#create single agent all CU synapsys claim button
agent_synapsys_btn = ttk.Button(app, text='Create All CU Synapsys Claims for this Agent!', width=20, command=create_single_agent_all_CU_synapsys_claim)
agent_synapsys_btn.grid(row=5, column=0, sticky=N)

#create trainer scripts button
agent_synapsys_btn = ttk.Button(app, text='Create Trainer Scripts!', width=20, command=create_trainer_scripts_claim)
agent_synapsys_btn.grid(row=5, column=1, sticky=N)
"""

option_1_var = tk.BooleanVar()
option_2_var = tk.BooleanVar()
option_3_var = tk.BooleanVar()
option_4_var = tk.BooleanVar()
option_5_var = tk.BooleanVar()
option_6_var = tk.BooleanVar()


check_button1 = ttk.Checkbutton(app, text="Single Bank Core", variable=option_1_var)
check_button2 = ttk.Checkbutton(app, text="Single Synapsys", variable=option_2_var)
check_button3 = ttk.Checkbutton(app, text="All Bank Core", variable=option_3_var)
check_button4 = ttk.Checkbutton(app, text="All Bank Synapsys", variable=option_4_var)
check_button5 = ttk.Checkbutton(app, text="All CU Synapsys", variable=option_5_var)
check_button6 = ttk.Checkbutton(app, text="Trainer List Core and Synapsys", variable=option_6_var)
check_button1.grid(row=3, column=0)
check_button2.grid(row=3, column=1)
check_button3.grid(row=4, column=0)
check_button4.grid(row=4, column=1)
check_button5.grid(row=5, column=0, sticky=N)
check_button6.grid(row=5, column=1, sticky=N)

#FI Name Entry
fi_Name_text = StringVar()
fi_Name_label = Label(app, text='FI Name', font=('bold', 14))
fi_Name_label.grid(row=7, column=0, sticky=W)
fi_Name_entry = Entry(app, textvariable=fi_Name_text)
fi_Name_entry.grid(row=7, column=1)

#FI Synapsys Number Entry
fi_syn_text = StringVar()
fi_syn_label = Label(app, text='FI Synapsys Number', font=('bold', 14))
fi_syn_label.grid(row=8, column=0, sticky=W)
fi_syn_entry = Entry(app, textvariable=fi_syn_text)
fi_syn_entry.grid(row=8, column=1)

#FI Type Entry
FI_type_text = StringVar()
FI_type_label = Label(app, text='FI type? (Bank or CU)', font=('bold', 14))
FI_type_label.grid(row=9, column=0, sticky=W)
FI_type_entry = Entry(app, textvariable=FI_type_text)
FI_type_entry.grid(row=9, column=1)

#Bank Core User Entry
bank_core_text = StringVar()
bank_core_label = Label(app, text='Bank Core User', font=('bold', 14))
bank_core_label.grid(row=10, column=0, sticky=W)
bank_core_entry = Entry(app, textvariable=bank_core_text)
bank_core_entry.grid(row=10, column=1)

#Bank Partition Entry
bank_partition_text = StringVar()
bank_partition_label = Label(app, text='Bank Partition', font=('bold', 14))
bank_partition_label.grid(row=11, column=0, sticky=W)
bank_partition_entry = Entry(app, textvariable=bank_partition_text)
bank_partition_entry.grid(row=11, column=1)

#clear fields
clear_btn = ttk.Button(app, text='Clear Input', width=14, command=clear_text)
clear_btn.grid(row=12, column=1)

#financial institutions label
fi_label = Label(app, text='Financial Institutions', font=('bold', 16), wraplength=200, pady=2)
fi_label.grid(row=12, column=0, sticky=S)
#Bank List
bank_list = Listbox(app, height=8, width=80, border=0)
bank_list.grid(row=13, column=0, columnspan=3, rowspan=6, pady=10, padx=10)
# Create scrollbar
scrollbar = Scrollbar(app)
scrollbar.grid(row=13, column=3, sticky=W)
# Set scroll to listbox
bank_list.configure(yscrollcommand=scrollbar.set)
scrollbar.configure(command=bank_list.yview)
# Bind select
bank_list.bind('<<ListboxSelect>>', select_item)

#multi instructions
multi_label = Label(app, text='To make a multi user claim upload a csv with agent emails in the 1st column with citjha.com domain and 4 digit extensions in the 2nd column and select your operation.', font=('bold', 18), wraplength=500, pady=10)
multi_label.grid(row=0, column=4, columnspan=4, sticky=W+E)

"""
#create all CU synapsys from CSV claim button
bank_core_btn = ttk.Button(app, text='Create ALL CU Synapsys Claim!', width=30, command=create_all_CU_synapsys_csv_claim)
bank_core_btn.grid(row=3, column=5, pady=5)

#create all Bank synapsys from CSV claim button
bank_core_btn = ttk.Button(app, text='Create ALL Bank Synapsys Claim!', width=30, command=create_all_bank_synapsys_csv_claim)
bank_core_btn.grid(row=4, column=5, pady=5)

#create all Bank core from CSV claim button
bank_core_btn = ttk.Button(app, text='Create ALL Bank Core Claim!', width=30, command=create_all_bank_core_csv_claim)
bank_core_btn.grid(row=5, column=5, pady=5, sticky=N)
"""

option_10_var = tk.BooleanVar()
option_11_var = tk.BooleanVar()
option_12_var = tk.BooleanVar()

check_button10 = ttk.Checkbutton(app, text="CSV Agent All CU Synapsys", variable=option_10_var)
check_button11 = ttk.Checkbutton(app, text="CSV Agent All Bank Synapsys", variable=option_11_var)
check_button12 = ttk.Checkbutton(app, text="CSV Agent All Bank Core", variable=option_12_var)

check_button10.grid(row=3, column=5)
check_button11.grid(row=4, column=5)
check_button12.grid(row=5, column=5, sticky=N)

#middle instructions
multi_label = Label(app, text='To make a new FI claim with all corresponding agents inthe Agent List Smartsheet input the FI information and select your operation.', font=('bold', 18), wraplength=500, pady=10)
multi_label.grid(row=5, column=2, columnspan=2, sticky=S)
"""
#create all agent one CU synapsys claim button
cu_agent_btn = ttk.Button(app, text='Create all CU agent Synapsys Claim!', width=30, command=create_all_agent_CU_synapsys_claim)
cu_agent_btn.grid(row=6, column=2, columnspan=2, pady=5)

#create all agent one Bank synapsys claim button
bank_agent_btn = ttk.Button(app, text='Create all Bank agent Synapsys Claim!', width=30, command=create_all_agent_bank_synapsys_claim)
bank_agent_btn.grid(row=7, column=2, columnspan=2, pady=5)

#create all agent one Bank core claim button
bank_core_agent_btn = ttk.Button(app, text='Create all Bank agent Core Claim!', width=30, command=create_all_agent_bank_core_claim)
bank_core_agent_btn.grid(row=8, column=2, columnspan=2, pady=5)
"""
option_7_var = tk.IntVar()
option_8_var = tk.IntVar()
option_9_var = tk.IntVar()

check_button7 = ttk.Checkbutton(app, text="All CU Agents Single CU Synapsys", onvalue='1', offvalue='0', variable=option_7_var)
check_button8 = ttk.Checkbutton(app, text="All Bank Agents Single Bank Synapsys", onvalue='1', offvalue='0', variable=option_8_var)
check_button9 = ttk.Checkbutton(app, text="All Bank Agents Single Bank Core", onvalue='1', offvalue='0', variable=option_9_var)

check_button7.grid(row=6, column=2)
check_button8.grid(row=7, column=2)
check_button9.grid(row=8, column=2)

option_7 = option_7_var.get()
option_8 = option_8_var.get()
option_9 = option_9_var.get()

print(option_7,option_8,option_9)
#browse input file, open CSV button
ttk.Label(app, text='File Path').grid(row=0, column=4,sticky=S)
ttk.Button(app, text='Browse Input File',command=import_csv_data).grid(row=2, column=4)
ttk.Entry(app, textvariable=v, width=80).grid(row=1, column=4, columnspan=3)

#operations to create and delete claims from processing queue, not currently active functionality.

#create claims
create_claim_btn = ttk.Button(app, text='CREATE CLAIMS!', width=30, command=lambda:create_all_agent_CU_synapsys_claim(option_7, option_8, option_9))
create_claim_btn.grid(row=11, column=3, columnspan=2, rowspan=2, pady=5, sticky=NSEW)
"""
#delete claims
delete_claim_btn = ttk.Button(app, text='DELETE SELECTED CLAIM!', width=30, command=lambda:delete_claim(jsonArray, op_list))
delete_claim_btn.grid(row=12, column=6, pady=5)
"""

#operations completed label
op_label = Label(app, text='Operation Queue', font=('bold', 16), wraplength=200, pady=2)
op_label.grid(row=12, column=5, sticky=S)   
#operations List
op_list.grid(row=13, column=4, columnspan=2, rowspan=3, pady=10, padx=10)
# Create scrollbar
opscrollbar = Scrollbar(app)
opscrollbar.grid(row=13, column=6, sticky=W)
# Set scroll to listbox
op_list.configure(yscrollcommand=opscrollbar.set)
opscrollbar.configure(command=op_list.yview)
# Bind select
op_list.bind('<<ListboxSelect>>')


#credits
credits_label = Label(app, text='This program was lovingly made by Chris Richardson.', font=('bold', 8), pady=10)
credits_label.grid(row=12, column=5, columnspan=2, sticky=W+E)

app.title('jhCC Support IMS Claim Creator')
#app.geometry('700x350')

#test = StringVar()
#rb1 = ttk.Radiobutton(app, text='5', variable=test, value=5)
#rb1.grid(row=0, column=0)
#print(test)

#populate bank list in GUI
populate_list()
print("We have started the program successfully, ready to create claims!")
print("This program lovingly created by Chris Richardson for exclusive use of the jhCC Software Support group.")

app.update()

app.mainloop()

db.close()

#mac installer code
#pyinstaller --onefile --add-binary='/System/Library/Frameworks/Tk.framework/Tk':'tk' --add-binary='/System/Library/Frameworks/Tcl.framework/Tcl':'tcl' JSON
