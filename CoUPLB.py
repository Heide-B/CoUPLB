import streamlit as st
import pandas as pd
import numpy as np
from csv import DictWriter
import base64
import os


#loading data
df = pd.read_csv('couplb.csv', usecols=[0,1,2,3,4])
sp = df['Species'].unique()
sp = np.insert(sp,0,'Cat & Dog')
loc = df['Location'].unique()
loc = np.insert(loc,0,'Campus View')


#Page construction
st.set_page_config(page_title="Cats of UPLB Pawttendance Tracker",page_icon='logo.png')
st.title("Cats of UPLB\n Pawttendance Tracker")
species = [st.sidebar.selectbox("Furrbaby Kind",sp)]
locations = [st.sidebar.selectbox('Clowder Locations',loc)]
main_bg = "main.png"
side_bg = "side.png"
main_bg_ext = "png"
side_bg_ext = "png"
st.markdown(
    f"""
    <style>
    .reportview-container {{
        background: url("data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()}")
    }}
   .sidebar.sidebar-content {{
        background-image: url("data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()}")
    }}
    </style>
    """,
    unsafe_allow_html=True)


#Filtering list shown
if 'Cat & Dog' in species:
    species.clear()
    species.append('Cat')
    species.append('Dog')

if 'Campus View' in locations:
    locations.clear()
    locations = loc
    
list = df[(df['Species'].isin(species)) & (df['Location'].isin(locations))]



#Functions
#Rerun
def rerun():
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
    

#Image loader
def images(pet,col1):
    path = './Photos/'    
    for i in os.listdir(path):
        if i.startswith(str(pet)) and i.endswith('jpg'):
            img = path+i
            col1.markdown(
                f"""
                <div class="container">
                    <img class="logo-img" width="50%" height="50%" src="data:image/png;base64,{base64.b64encode(open(img, "rb").read()).decode()}">
                </div>
                """,
                unsafe_allow_html=True)


    
#Setting up states
def states(key):
    if key not in st.session_state:
        st.session_state[key] = 'Not Visited'
        Status = st.session_state[key]
    elif st.session_state[key] == 'Not Visited':
        Status = st.session_state[key]
    else:
        Status = 'Visited'
    return Status


#Creating record dictionary
def record(date, name,present,injure,remarks,feeder):
    records = {'timestamp':date,
        'name':name,
        'attendance':present,
        'status':injure,
        'remarks':remarks,
        'feeder':feeder}
    return records


#Creating the list and report form
def rows(name,date,status):
    with st.expander(name + ' - ' + str(status)):
        col1, col2 = st.columns([3,1])
        present = col1.selectbox('Attendance',['Absent','Present','Fostered'], key = name + '_Present')
        injure = col1.selectbox('Status',['Healthy','Injured','Sick'], key = name + '_Injured')
        remarks = col1.text_input('Remarks', key = name + '_Remarks')
        images(name,col1)
        feeder = col2.text_input('Feeder', key = name + '_Feeder')
        if col2.button('Submit Record',key = name + '_Record',):
            new_df=record(date, name,present,injure,remarks,feeder)
            st.session_state[record_key] = 'Visited'
            with open('record.csv', 'a',newline='') as f_object:
                dictwriter_object = DictWriter(f_object, fieldnames=['timestamp','name','attendance','status','remarks','feeder'], delimiter=',' )
                dictwriter_object.writerow(new_df)
                f_object.close()
            rerun()

            

                
# Actual page
date = st.date_input('Feeding Date')
for index,vals in list.iterrows():
    name = vals[2]
    stat = vals[4]
    record_key = name+'_'+str(date)
    status = states(record_key)
    rows(name,date,status)
