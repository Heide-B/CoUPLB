import streamlit as st
import pandas as pd
import numpy as np
import pendulum
import datetime
import matplotlib
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
clows = df['Location'].unique()
loc = np.insert(clows,0,'Campus View')
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
    
lists = df[(df['Species'].isin(species)) & (df['Location'].isin(locations))]



### Functions    

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
    else:
        st.session_state[key] = 'Not Visited'

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
    query = f"SELECT COUNT(*) from public.record_1 where \"Name\" = '{name}' and \"Timestamp\" = '{time}';"
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
        if col2.button('Submit Record',key = name + '_Record',):
            record(date,clow,name,present,injure,remarks,feeder)
            st.session_state[record_key] = 'Visited'

        if st.session_state[record_key] == 'Visited':
            col2.success('Record Submitted')
        images(name)



def clowder_row(date, feeder, lists):
    clow = lists['Location'].iat[0]
    record_key = f'entire_clow_{clow}'
    with st.expander(f"Report for entire {clow}"):
        present = st.multiselect('Present furbabies', lists['Name'])
        absent = st.multiselect('Absent furbabies', lists['Name'])

        if st.button('Submit Record', key = record_key):
            if len(present) > 0:
                for name in present:
                    record(date=date,clowder=clow,name=name,present='Present',injure="Healthy",remarks="No remarks",feeder=feeder)
            if len(absent) > 0:
                for name in present:
                    record(date=date,clowder=clow,name=name,present='Absent',injure="Healthy",remarks="No remarks",feeder=feeder)
                st.success('Records Submitted')
            
                
def check_sched(conn, start, end):
    query = f"SELECT * FROM public.record_1 WHERE \"Timestamp\" between '{start}' AND '{end}';"
    df = pd.read_sql_query(query, conn)
    
    sched = pd.DataFrame()
    for _, date in week.items():
        for clow in clows:
            if date in df.Timestamp.unique() and clow in df.clowder.unique():
                sched.at[clow, date] = df.feeder.values[0]
            else:
                sched.at[clow, date] = 'unassigned'
    return sched

def req_sched(req_clowder, req_date, username, conn):
    with conn.cursor() as cur:
        for i in req_clowder:
            records = {'req_date':req_date,
                       'i':i,
                       submitted:'submitted',
                       'username':username}
            cur.execute("""INSERT INTO public.feeders("Timestamp",clowder,status,feeder) VALUES (%(req_date)s, %(i)s, %(submitted)s, %(username)s)""", records)
            conn.commit()
            conn.close()

def color_sched(df):
    fs = pd.unique(sched.values.ravel()).tolist()
    fs.remove('unassigned')
    
    colors = dict(zip(fs,
                  (f'background-color: {c}' for c in matplotlib.colors.cnames.values())))
    colors['unassigned'] = 'background-color: gray'
    for name, value in colors.items():
        if value == 'background-color: #000000':
            colors[name] = 'background-color: #FFFFFF'
    return colors

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
    tab1, tab2, tab3 = st.tabs(["Tracking", "Animal Overview", "TBD"])
    with tab1:
        date = st.date_input('Feeding Date')
        clowder_row(date, username, lists)
        for index, vals in lists.iterrows():
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
                report_query = f'SELECT * FROM public.record_1 WHERE "Timestamp" = \'{date}\';'
                conn = init_connection()
                with conn.cursor() as cur:
                    cur.execute(report_query)
                    reps = cur.fetchall()
                    conn.commit()
                    conn.close()            
                message = f"""Feeding Report for {date} - {clow} clowder
                            \nby {username}
                            """
                for items in reps:
                    message += f"""\n{items[1]} - {items[2]}
                                    <br>{items[3]}. Remarks: {items[5]}
                                    \n
                                """
                st.markdown(message, unsafe_allow_html=True)
                
    with tab2:
        today = pendulum.now()
        start = today.start_of('week').strftime('%Y-%m-%d')
        end = today.end_of('week').strftime('%Y-%m-%d')
        st.header(f'Showing Feeding Sched for week {start}')
        week = {'day1':0,'day2':1,'day3':2,'day4':3,'day5':4,'day6':5,'day7':6}
        
        for day, num in week.items():
            week[day] = datetime.datetime.strptime(start, '%Y-%m-%d') + datetime.timedelta(days=num)
            week[day] = week[day].strftime('%Y-%m-%d')
        conn = init_connection()
        with st.expander('Apply for schedule'):
            with st.form('Application'):
                req_clowder = st.multiselect('Clowders', clows)
                req_date = st.date_input('Feeding date')
            submitted = st.form_submit_button("Submit")
            if submitted:
                req_sched(req_clowder, req_date, username, conn)

        sched = check_sched(conn, start, end)
        colors = color_sched(sched)
        st.dataframe(sched.style.applymap(colors.get))
        
    with tab3:
        st.write('Feature coming soon')


conn = init_connection()
query = "SELECT * FROM public.record_1;"
record_df = pd.read_sql_query(query, conn)
csv = record_df.to_csv().encode('utf-8')
st.sidebar.download_button(label='Download Records', data=csv, file_name='CoUPLB Records.csv',mime='text/csv')
