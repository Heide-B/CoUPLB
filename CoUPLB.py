import streamlit as st
import pandas as pd
import numpy as np
from csv import DictWriter
import psycopg2
import base64
import os

#### DB
def init_connection():
    DATABASE_URL = os.environ['DATABASE_URL']
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# def checking():
#     with conn.cursor() as cur:
#         cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
#         rows = cur.rowcount
#         res = cur.fetchall()
#         print(rows)
#         print(res)
#         if rows >= 9990:
#             try:
#                 current_table = res[-1][-1]
#                 x = current_table
#                 i = x.split("_")
#                 new_table = i[0]+'_'+str(int(i[-1]) + 1)
#                 cur.execute(
#                 """CREATE TABLE public.{0} (
#                 "Timestamp" date NOT NULL, -- Date of the recorded feeding
#                 "Name" varchar NOT NULL, -- Name of the animal being recorded
#                 attendance varchar NOT NULL, -- Absent, Present, Fostered
#                 status varchar NOT NULL, -- Healthy, Injured, Sick
#                 feeder varchar NULL, -- Feeder assigned
#                 remarks varchar NULL);""".format(new_table))
#                 conn.commit()
#                 conn.close()
#             except psycopg2.Error as e:
#                 print(e)
#         else:
#             pass

### Preparation

#loading data
df = pd.read_csv('couplb.csv', usecols=[0,1,2,3,4])
sp = df['Species'].unique()
sp = np.insert(sp,0,'Cat & Dog')
loc = df['Location'].unique()
loc = np.insert(loc,0,'Campus View')
users = os.environ['USERS'].split(",")
pw = os.environ['PASSWORD'].split(",")
creds = {users[i]: pw[i] for i in range(len(users))}


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



### Functions

#Rerun
def rerun():
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
    

#Image loader
def images(pet):
    path = './Photos/'    
    for i in os.listdir(path):
        if i.startswith(str(pet)) and i.endswith('jpg'):
            img = path+i
            st.markdown(
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

#Creating record dictionary
def record(date,clowder,name,present,injure,remarks,feeder):
    records = {'timestamp':date,
        'clowder':clowder,
        'name':name,
        'attendance':present,
        'status':injure,
        'remarks':remarks,
        'feeder':feeder}
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO public.record_1("Timestamp",clowder,"Name",attendance,status,feeder,remarks) VALUES (%(timestamp)s, %(clowder)s, %(name)s, %(attendance)s, %(status)s, %(feeder)s, %(remarks)s)""", records)
        conn.commit()
        conn.close()

def check_status(name, time, key):
    query = f"select COUNT(*) from public.record_1 where 'Name' = '{name}' and 'Timestamp' = '{time}';"
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute(query)
        count = cur.fetchone()
        conn.commit()
        conn.close()
    if count[0] > 0:
        status = 'Visited'
        st.session_state[key] = 'Visited'
    else:
        status = 'Not Visisted'
        st.session_state[key] = 'Not Visited'
    return status

#Creating the list and report form
def rows(clow,name,date,status,feeder, record_key):
    with st.expander(name + ' - ' + str(st.session_state[record_key])):
        col1, col2 = st.columns([3,1])
        present = col1.selectbox('Attendance',['Absent','Present','Fostered'], key = name + '_Present')
        injure = col1.selectbox('Status',['Healthy','Injured','Sick'], key = name + '_Injured')
        remarks = col1.text_input('Remarks', key = name + '_Remarks')
#         feeder = col2.text_input('Feeder', key = name + '_Feeder')
        if col2.button('Submit Record',key = name + '_Record',):
            record(date,clow,name,present,injure,remarks,feeder)
            st.session_state[record_key] = 'Visited'
            rerun()
        if st.session_state[record_key] == 'Visited':
            col2.success('Record Submitted')
        images(name)


                
# Actual page

if 'initializer' not in st.session_state:
    st.session_state.initializer = False
with st.expander('Please Login Here', expanded=not st.session_state.initializer):
    with st.form('Login', True):
        username = st.text_input('Feeder Name')
        password = st.text_input('Password',type='password')
        submitted = st.form_submit_button(label='Login')
        if submitted:
            validation = creds.get(username)
            if validation == password:
                st.session_state.initializer = True
            else:
                st.session_state.initializer = 'Blank'


if st.session_state.initializer == False:
    st.write()
elif st.session_state.initializer == 'Blank':
    st.header('Login credentials incorrect. You are not permitted to access this page.') 
elif st.session_state.initializer == True:
    date = st.date_input('Feeding Date')
    for index,vals in list.iterrows():
        clow = vals[1]
        name = vals[2]
        stat = vals[4]
        record_key = name+'_'+str(date)
        states(record_key)
        status = check_status(name, date, record_key)
        rows(clow,name,date,status,username, record_key)
    with st.sidebar.form('Generate Report'):
        st.info('Generate a report for the currently selected species and location')
        generate = st.form_submit_button("Generate")
        if generate:
            report_query = f"SELECT * FROM public.record_1 WHERE 'Timestamp' = '{date}';"
            conn = init_connection()
            report = pd.read_sql_query(report_query, conn)
            st.dataframe(report)
            rep = zip(report['Name'], report['attendance'], report['status'])
            message = f"""Report for {date} - {clow} clowder
                        \nby {username}
                        """
            for n, a, s in rep:
                message += f"""\n{n} - {a}
                                \n{s}
                                \n
                            """
            st.markdown(message, unsafe_allow_html=True)
    
conn = init_connection()
query = "SELECT * FROM public.record_1;"
record_df = pd.read_sql_query(query, conn)
csv = record_df.to_csv().encode('utf-8')
st.sidebar.download_button(label='Download Records', data=csv, file_name='CoUPLB Records.csv',mime='text/csv')
