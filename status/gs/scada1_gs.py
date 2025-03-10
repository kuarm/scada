import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
#import matplotlib.pyplot as plt
import time  # to simulate a real time data, time loop

#parameter
sheet = ['Scada', 'Location', 'Ava']
sheet1 = ['event', 'map']
option_install = ['สถานีไฟฟ้า', 'ระบบจำหน่าย', 'ระบบสายส่ง', 'VSPP(ผชฟ)', 'VSPP', 'SPP(ผชฟ)']
option_device = ['Substation', 'RCS', 'AVR', 'Recloser', 'LoadBreak115', 'CircuitSwitcher']
cols_select = ['Name', 'SiteID', 'State', 'Description', 'สถานที่', 'การไฟฟ้า', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'Master', 'โครงการติดตั้ง']
option_funct = ['สถานะอุปกรณ์','Highlight','%ความพร้อมใช้งาน & %การสั่งการ','Building', 'ข้อมูลการสั่งการ']
st.set_page_config(page_title='Dashboard‍', page_icon=':bar_chart:', layout="wide", initial_sidebar_state="expanded", menu_items=None)

# CSS Style
with open('style.css')as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)

# ---- READ EXCEL ----
#@st.cache_data
def prepare_data():
    df_scada = get_data(sheet[0])
    df_location = get_data(sheet[1]).drop(['SiteID','Description'], axis='columns')
    df_ava = get_data(sheet[2]).drop(['SiteID','Description'], axis='columns')
    df_display = get_data(sheet[2]).drop(['SiteID','Description'], axis='columns')
    df1 = pd.merge(df_scada, df_location, how="outer", on=['Name'], left_index=False, right_index=False)
    df2 = pd.merge(df1, df_ava, how="outer", on=['Name'], left_index=False, right_index=False)
    df = df2[df2['Use/NotUse'] == 1]
    return df

def prepare_data2(sheet):
    df = get_data2(sheet)
    return df

def rtu_cal(df,inst):
    df_select = df[df['จุดติดตั้ง'] == inst]
    return df_select

def rtu_cal_st(df,st):
    count = df['Name'].loc[df['State'] == st].count()
    return count
    
def get_data(sh) -> pd.DataFrame:
    df = pd.read_excel('scada-info.xlsx', sheet_name=sh)
    #df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
    return df

def get_data1() -> pd.DataFrame:
    df = pd.concat(pd.read_excel('scada-info.xlsx', sheet_name=None), ignore_index=True)
    return df

def get_data2(sh) -> pd.DataFrame:
    df = pd.read_excel('file1.xlsx', sheet_name=sh)
    #df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
    return df

def HomePage(df_sel):
    with st.expander("Tabular"):
        #st.dataframe(df_selection,use_container_width=True)
        showdata = st.multiselect('Filter :', df_sel.columns, default=[])
        st.dataframe(df_sel[showdata],use_container_width=True)

def Analytics(df_sel):
    state_online = df_sel[df_sel['State'] == 'Online']
    #master_ = float(df_sel['Master'].sum())
    #profit = float(df_sel['expected_profit'].sum())
    total1,total2,total3= st.columns(3,gap='small')
    with total1:
            st.info('Substation', icon="🔍")
            st.metric(label = 'จำนวน', value= f"{len(state_online)}")
            
    with total2:
            st.info('SPP/VSPP', icon="🔍")
            st.metric(label='จำนวน', value=f"{selling_price_:,.0f}")

    with total3:
            st.info('Expected Profit', icon="🔍")
            st.metric(label= 'TZS',value=f"{profit:,.0f}")

def display(df):
    cols_drop = {'No'}
    
    #df = df.drop(columns=cols_drop, axis=1)
    #aggrid(df)
    #df_r = df.rename(columns=)
    col1, col2 = st.columns([1,3])
    #df = df.drop(columns={'No'}, axis=1)
    select_1_choice = ['Name', 'State', 'Description', 'จุดติดตั้ง']
    #select_1 = st.sidebar.radio("แบ่งแยกประเภท",select_1_choice)
    df111 = df['จุดติดตั้ง'].drop_duplicates()
    st.write(df111)
    select_2 = st.sidebar.selectbox(label ='จุดติดตั้ง', options = df111)

    select_1 = st.sidebar.selectbox(label ='จำนวน Frtu', options = select_1_choice)

    if select_1:
            with col1:
                df1 = df.groupby(select_1)['Name'].count().reset_index(name='จำนวน(ชุด)')
                st.write(df1)
                #df1.rename(columns={'SiteID': "จำนวน"})
            with col2:
                fig = px.bar(df1, x=select_1, y='จำนวน(ชุด)', color=select_1, title=select_1+' - จำนวน')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("----------")

def aggrid(a):
   #sel_mode = st.radio('Selection Type', options = ['single', 'multiple'])
   gd = GridOptionsBuilder.from_dataframe(a)
   gd.configure_pagination(enabled=True)
   gd.configure_default_column(editable=True, groupable=True)
   gd.configure_selection(selection_mode='multiple', use_checkbox=True) #options = ['single', 'multiple'])
   gd.configure_grid_options(rowHeight=50)
   gridoptions = gd.build()
   grid_table = AgGrid(
       a,
       gridOptions=gridoptions,
       enable_enterprise_mudules = False,
       fit_columns_on_grid_load = False,
       update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED | GridUpdateMode.GRID_CHANGED,
       height = 300,
       width ='100%',
       reload_data = True,
       allow_unsafe_jscode=True,
       theme = 'streamlit'
   )
   #sel_row = grid_table["selected_rows"]
   #st.subheader("Output")
   #st.write(sel_row)

#session
if "ava_min" not in st.session_state:
    # set the initial default value of the slider widget
    st.session_state.ava_min = 70.00
    #ava_min = st.session_state.ava_min
    #          
if "ava_max" not in st.session_state:
    # set the initial default value of the slider widget
    st.session_state.ava_max = 90.00
if "S_eventid" not in st.session_state:
    st.session_state.S_eventid = []
#update
def update_ava():
    st.session_state.ava_min = st.session_state.ava_min
    st.session_state.ava_max = st.session_state.ava_max
   
    #st.session_state.master = st.session_state.master

def update_u():
    st.session_state.utility = st.session_state.utility

def update_m():
    st.session_state.master = st.session_state.master

def update_s():
    st.session_state.S_eventid = st.session_state.S_eventid
#query
def query(df):
    df1 = df['การไฟฟ้า'].unique().tolist()
    df2 = df['master'].unique().tolist()
    #st.session_state.utility = df
    return df1,df2 #st.session_state.utility

st.cache_data
def get_chart_44471063():
    dfxxx = px.data.tips()
    fig = px.histogram(dfxxx, x="total_bill")

    tab1, tab2 = st.tabs(["Streamlit theme (default)", "Plotly native theme"])
    with tab1:
        st.plotly_chart(fig, theme="streamlit")
    with tab2:
        st.plotly_chart(fig, theme=None)

def edit(df):
    df.to_excel("file1.xlsx",index=False)

#main
def main():
    st.title("📊 สถานะอุปกรณ์บนระบบ SCADA")
    st.markdown("---------")
    rtu_data = prepare_data()
    oper_data = prepare_data2(sheet1[0])
    map_data = prepare_data2(sheet1[1])
    cols_select = ['State', 'Description', 'สถานที่', 'การไฟฟ้า', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'Master', 'โครงการติดตั้ง']
    st.sidebar.header("Functions:")
    funct_select = st.sidebar.radio(label="", options = option_funct)
    st.sidebar.markdown("---------")

#สถานะอุปกรณ์
    if funct_select == option_funct[0]:
        col1, col2, col3, col4 = st.columns(4)
        #dev_group = st.sidebar.multiselect('เลือกประเภทอุปกรณ์',options=option_device,default=option_device)
        dev_group = st.sidebar.multiselect('เลือกประเภทอุปกรณ์',options=option_device,default=option_device)
        dev_install = st.sidebar.multiselect('เลือกจุดติดตั้ง',options=option_install,default=option_install)
        dev_state = st.sidebar.multiselect('เลือก State',options=rtu_data['State'].unique().tolist(),default=rtu_data['State'].unique().tolist())
        dev_utility = st.sidebar.multiselect('เลือกการไฟฟ้า',options=rtu_data['การไฟฟ้า'].unique().tolist(),default=rtu_data['การไฟฟ้า'].unique().tolist())
        dev_master = st.sidebar.multiselect('เลือก Master',options=rtu_data['Master'].unique().tolist(),default=rtu_data['Master'].unique().tolist())
        df_selection  = rtu_data.query('`ประเภทอุปกรณ์` == @dev_group & `จุดติดตั้ง` == @dev_install & `State` == @dev_state & `การไฟฟ้า` == @dev_utility & `Master` == @dev_master')
        df_display = df_selection[cols_select]
        st.write(df_display)
        st.download_button('Download file สถานะอุปกรณ์ ',data=pd.DataFrame.to_csv(rtu_data,index=False), mime="text/csv")

        with col1:
            df_sub = rtu_cal(df_selection,option_install[0])
            Count_sub = df_sub['Name'].count()
            st.info(f'Substation ({Count_sub})', icon='🔍')
            st.metric('Online', f"{rtu_cal_st(df_sub,'Online')}")
            st.metric('Offline', f"{rtu_cal_st(df_sub,'Offline')}")
            st.metric('Connecting', f"{rtu_cal_st(df_sub,'Connecting')}")  
            st.metric('Initializing', f"{rtu_cal_st(df_sub,'Initializing')}")  
            st.metric('Telemetry Failure', f"{rtu_cal_st(df_sub,'Telemetry Failure')}")      
        with col2:
            df_feed = rtu_cal(df_selection,option_install[1])
            Count_feed = df_feed['Name'].count()
            st.info(f'ระบบจำหน่าย ({Count_feed})', icon='🔍')
            st.metric('Online', f"{rtu_cal_st(df_feed,'Online')}")
            st.metric('Offline', f"{rtu_cal_st(df_feed,'Offline')}")
            st.metric('Connecting', f"{rtu_cal_st(df_feed,'Connecting')}")  
            st.metric('Initializing', f"{rtu_cal_st(df_feed,'Initializing')}")  
            st.metric('Telemetry Failure', f"{rtu_cal_st(df_feed,'Telemetry Failure')}")   
        with col3:
            df_tran = rtu_cal(df_selection,option_install[2])
            Count_tran = df_tran['Name'].count()
            st.info(f'ระบบสายส่ง ({Count_tran})', icon='🔍')
            st.metric('Online', f"{rtu_cal_st(df_tran,'Online')}")
            st.metric('Offline', f"{rtu_cal_st(df_tran,'Offline')}")
            st.metric('Connecting', f"{rtu_cal_st(df_tran,'Connecting')}")  
            st.metric('Initializing', f"{rtu_cal_st(df_tran,'Initializing')}")  
            st.metric('Telemetry Failure', f"{rtu_cal_st(df_tran,'Telemetry Failure')}")      
        with col4:
            df_vspp1 = rtu_cal(df_selection,option_install[3])
            df_vspp2 = rtu_cal(df_selection,option_install[4])
            df_spp = rtu_cal(df_selection,option_install[5])
            df_svspp = pd.concat([df_vspp1, df_vspp2, df_spp], axis=0)
            Count_svspp = df_svspp['Name'].count()
            #spp_vspp_count = df_vspp1['Name'].count() + df_vspp2['Name'].count() + df_spp['Name'].count()
            
            st.info(f'SPP/VSPP ({Count_svspp})', icon="🔍")
            st.metric('Online', f"{rtu_cal_st(df_svspp,'Online')}")
            st.metric('Offline', f"{rtu_cal_st(df_svspp,'Offline')}")
            st.metric('Connecting', f"{rtu_cal_st(df_svspp,'Connecting')}")  
            st.metric('Initializing', f"{rtu_cal_st(df_svspp,'Initializing')}")  
            st.metric('Telemetry Failure', f"{rtu_cal_st(df_svspp,'Telemetry Failure')}")
        st.markdown("---------")

#2
    if funct_select == option_funct[1]:
        col_opt = st.sidebar.selectbox(label ='Select column', options = rtu_data.columns)
        
        #col_opt = st.sidebar.selectbox(label ='Select column', options = df.columns)
        #master = st.sidebar.multiselect('Select Master',options=rtu_data['Master'].unique(),default='CELLULAR')
        #col_opt = st.selectbox(label ='Select column', options = df.columns)

#ความพร้อมใช้งาน & การสั่งการ
    if funct_select == option_funct[2]:
        st.subheader('%ค่าความพร้อมใช้งาน (Availability)')
        col1, col2 = st.columns(2)
        col3 = st.columns(1)
        ava_range_fix = ['Availability <= 80', '80 < Availability <= 90', '90 < Availability <= 100']
        ava_cols_select = ['การไฟฟ้า', 'Master', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'โครงการติดตั้ง']
        ava_cols_display = ['Availability', 'Name', 'State', 'Description', 'การไฟฟ้า', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'Master', 'โครงการติดตั้ง']
        
        
        
        #['Availability', 'State', 'Name', 'Description', 'สถานที่', 'การไฟฟ้า', 'Address', 'Master', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'โครงการติดตั้ง', 'Lat/Long']
        #'Avaiability','TotalCountDown','TdownUnit','TotalTime','TotalDis','Master'
        #ava_range = ['Availability > 90', 'Availability <= 100', 'Availability > 80', 'Availability <= 90', 'Availability <= 80']
        
        df_ava1 = rtu_data.loc[(rtu_data['Availability'] > 90) & (rtu_data['Availability'] <= 100)]
        df_ava2 = rtu_data.loc[(rtu_data['Availability'] > 80) & (rtu_data['Availability'] <= 90)]
        df_ava3 = rtu_data.loc[(rtu_data['Availability'] <= 80)]
        df_ava = pd.DataFrame(
            [
                {'ช่วงค่า Availability':ava_range_fix[0],'จำนวน frtu (ชุด)':df_ava3['Name'].count()},
                {'ช่วงค่า Availability':ava_range_fix[1],'จำนวน frtu (ชุด)':df_ava2['Name'].count()},
                {'ช่วงค่า Availability':ava_range_fix[2],'จำนวน frtu (ชุด)':df_ava1['Name'].count(),}
            ]
        )

        fig = px.bar(df_ava, x='ช่วงค่า Availability', y='จำนวน frtu (ชุด)', color='ช่วงค่า Availability', text_auto=True)
        fig.update_layout(title="% ค่า Availability") 
        st.plotly_chart(fig, use_container_width=True)     
        st.markdown("---------")

        #aggrid(rtu_data)
        #df_ava = get_data(sheet[2]).drop(['SiteID'], axis='columns')
        #ava_group = st.sidebar.multiselect('ค่า Availability ตามประเภท',options=cols_select,default=cols_select)
        #rana = ['เลือกช่วง Ava','เลือก รหัสสั่งการ, SiteID, Master, การไฟฟ้า"']
        #cols = ['AVAILABILITY(%)', 'จำนวนครั้งที่ Down รวม', 'Master']
        #cols1 = ['AVAILABILITY(%)', 'SiteID', 'รหัสสั่งการ', 'สถานที่', 'การไฟฟ้า', 'Master']
        #dev_install = st.sidebar.multiselect('เลือกจุดติดตั้ง',options=rtu_data['จุดติดตั้ง'].unique(),default=rtu_data['จุดติดตั้ง'].unique())
        #df_selection = rtu_data.query('ประเภทอุปกรณ์ == @select_group & จุดติดตั้ง == @dev_install')

        #select_1_choice = ['การไฟฟ้า', 'ประเภทอุปกรณ์', 'จุดติดตั้ง', 'Master', 'Media']
        #select_1 = st.sidebar.selectbox(label ='ค่า availability ตามประเภท', options = select_1_choice)
        #sel_ava = st.sidebar.radio('กำหนดค่า Ava', options = ['auto', 'manual'])
        #range_ava1 = ['Ava <= 80', '80 < Ava <= 90', '90 < Ava <= 100']
        #ava_group = st.selectbox(label='เลือกค่า Availability ตามประเภท',options=ava_cols_select)

        with st.sidebar:
            st.caption(f'ช่วง Availability')
            st.number_input('Availability Min', min_value = 0.00, max_value = 100.00, value=st.session_state.ava_min, step=0.5, key='ava_min', on_change=update_ava)
            st.number_input('Availability Max', min_value = 0.00, max_value = 100.00, value=st.session_state.ava_max, step=0.5, key='ava_max', on_change=update_ava)
            df_selection = rtu_data.query('Availability >= @st.session_state.ava_min & Availability <= @st.session_state.ava_max')

            utility = st.multiselect(label = 'filter การไฟฟ้า',options=df_selection['การไฟฟ้า'].unique().tolist(),default=df_selection['การไฟฟ้า'].unique().tolist(), key='utility', on_change=update_u)
            master = st.multiselect(label = 'filter master',options=df_selection['Master'].unique().tolist(),default=df_selection['Master'].unique().tolist(), key='master', on_change=update_m)
            
            df_selection1 = df_selection.query('`การไฟฟ้า` == @st.session_state.utility or `Master` == @st.session_state.master')
            ava_display_Bar = st.radio('เลือกกราฟแสดงผล', options = ['ฺBar Plot', 'Scatter Plot'])

        #st.caption('ความสัมพันธ์ Availability กับ {}'.format(', '.join(ava_group_multi1)))
        #df_selection  = rtu_data.query('`ประเภทอุปกรณ์` == @dev_group & `จุดติดตั้ง` == @dev_install & `State` == @dev_state & `การไฟฟ้า` == @dev_utility & `Master` == @dev_master')
        
        countRtu = len(df_selection1['Name'])
        #countMaster = len(df_selection1['Master'].drop_duplicates())
        countUtility = len(df_selection1['การไฟฟ้า'].drop_duplicates())
        #st.write(f'ช่วง %Avaiability {st.session_state.ava_min} - {st.session_state.ava_max }, Frtu = {countRtu}, Master = {countMaster}, การไฟฟ้า = {countUtility}')
        
        # creating a single-element container
        placeholder = st.empty()

        for seconds in range(200):
            bins = int((st.session_state.ava_max - st.session_state.ava_min) // 10)
            fig_histo = px.histogram(df_selection1, x="Availability", nbins=bins, text_auto=True, title='FRTU แต่ละช่วง Availability')
            tab1, tab2 = st.tabs(["Streamlit theme (default)", "Plotly native theme"])
            with placeholder.container():
                with tab1:
                    st.plotly_chart(fig_histo, theme="streamlit")
                with tab2:
                    st.plotly_chart(fig_histo, theme=None)  
                st.download_button('Download file',data=pd.DataFrame.to_csv(rtu_data,index=False), mime="text/csv")  

                st.write(df_selection1[ava_cols_display])

        #st.caption(f'Scatter Plot Avaiability vs {ava_group_multi1}')
        #fig = px.scatter(df_selection, x=ava_group_multi1, y='Avaiability', color='Master', hover_name='Master', size_max=100)
        #fig.update_layout(title=f'% ค่า Avaiability vs {ava_group_multi1}') 
        #fig.update_layout(width=800,height=400)
        #st.plotly_chart(fig, use_container_width=True)
        #st.write(df_selection1)
        #st.download_button('Download file',data=pd.DataFrame.to_csv(df_selection1,index=False), mime='text/csv', key='1')
        
        if ava_display_Bar == 'ฺBar Plot':
            ava_group = st.sidebar.selectbox('Plot Avaiability กับ',options=ava_cols_select)
            #df_selection1 = df_selection.groupby(ava_group)['Availability'].mean().reset_index()
            #st.download_button('Download file',data=pd.DataFrame.to_csv(df_selection1,index=False), mime="text/csv", key='2')
            #fig = px.bar(df_selection1, x=ava_group, y='Availability', color=ava_group, title='', hover_data=['Name'])
            fig = px.bar(df_selection1, x='Description', y='Availability', color=ava_group, title='', hover_data=['Master'])
            fig.update_layout(title=f'% ค่า Availability vs {ava_group}') 
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---------")
        else:
            ava_group = st.sidebar.selectbox('Plot Avaiability กับ',options=ava_cols_select)
            #df_selection1 = df_selection.groupby(ava_group)['Availability'].mean().reset_index()
            fig = px.scatter(df_selection1, x=ava_group, y='Availability', color=ava_group, hover_data=['Name','Description'], size_max=100)
            fig.update_layout(title=f'% ค่า Availability vs {ava_group}') 
            fig.update_layout(width=800,height=400)
            st.plotly_chart(fig, use_container_width=True)
            #fig1 = px.scatter(df_selection, x=ava_group, y='Avaiability', color='Master', hover_name='Master', size_max=100)
            #fig1.update_layout(width=800,height=400)
            #st.plotly_chart(fig1, use_container_width=True)
            st.markdown("---------")

        st.sidebar.markdown("---------")
        st.sidebar.caption(f'Filter ต่างๆ')
        ava_group_multi = st.sidebar.multiselect(label = 'ตามรหัสสั่งการ',options=rtu_data['Description'].unique().tolist(),default=[], key='my_multiselect')
        time.sleep(1)
        #ava_group = st.selectbox('เลือก Scatter Plot',options=ava_cols_select)     
            #df_selection = rtu_data.groupby(ava_group)['Avaiability'].max().reset_index(name='%Avaiability (max)')
            #df_selection = rtu_data.groupby(ava_group)['Avaiability'].describe()
            #df_selection = rtu_data.filter([ava_group[0], 'Avaiability'])
            #fig = px.bar(df_selection, x=ava_group, y='Avaiability', color=ava_group, title=f'{ava_group} - Avaiability-mean')
            #st.plotly_chart(fig, use_container_width=True)
            #fig = px.bar(df_selection, x='Master', y='Avaiability', color='Master', title='')
            #fig = px.scatter(df_selection1, x='Master', y='การไฟฟ้า', color='Master', hover_name='Master', size_max=100)
            #fig.update_layout(title="% ค่า Avaiability") 
            #fig.update_layout(width=800,height=400)
            #st.plotly_chart(fig, use_container_width=True)
            #st.caption(f'You selected: Min Ava : {ava1_choice} และ Max Ava : {ava2_choice}')
        

        
        


        #if ava_auto_man == 'auto':
            #_funct_ava = st.sidebar.multiselect(label ='เลือกช่วง Ava', options = ava_range_fix)
            #st.caption("You selected: {}".format(", ".join(_funct_ava)))
            #df_selection = df_ava.query("Range == @_funct_ava")

            #  

        

        #if submit_button:  
            #st.session_state.selected_education_levels = selected_education_levels
    #HomePage(df_selection)
    #Analytics(df_selection)

    #st.sidebar.markdown("----------")
    #fig111 = px.histogram(df_selection1, x="Availability", nbins=10)
    if funct_select == option_funct[4]:
        st.subheader("ปัญหาการใช้งานระบบ SCADA/TDMS")
        col1, col2, col3, col4 = st.columns(4)
        
        oper_data['ID'] = oper_data.index+1
        eventid = 'event' + str(oper_data['ID'].max()+1).zfill(5)
        #df_oper  = oper_data.query('eventid == @S_eventid')

        with st.sidebar:
            func1 = st.selectbox('เลือกแสดงผล',options = ['สถานะข้อขัดข้อง', 'เพิ่ม event', 'แก้ไข event'])
            form = st.form(key='form1', clear_on_submit=True)
            #add_name = form.text_input(label=f"{name_label}", value='input some name')
            #add_age = form.text_input(label=f"{age_label}")
            #add_ref = df['eventid'].max() + 1
            #S_eventid = form.text_input(label='Search eventid')
            #df_oper  = oper_data.query('eventid == @S_eventid')
            #button_press = form.form_submit_button(label='Search', on_click=update_s)

        if 'สถานะข้อขัดข้อง' in func1:
            with col1:
                Count_sub1 = oper_data['eventid'].count()
                st.info(f'สถานีไฟฟ้า หรือ SPP', icon='🔍')
                st.metric('จำนวน',Count_sub1) 
            with col2:
                Count_feed1 = oper_data['eventid'].count()
                st.info(f'ระบบ', icon='🔍')
                st.metric('จำนวน',Count_feed1) 
            #st.write(oper_data)
            

        if  func1 == 'เพิ่ม event':
            func11 = st.sidebar.selectbox('พื้นที่ขัดข้อง', options = ['สถานีไฟฟ้า', 'ระบบ'])
            if func11 == 'สถานีไฟฟ้า':
                options_form=st.form("เพิ่ม event")
                eventid=options_form.text_input('EventID',value=eventid,disabled=True)
                datetime=options_form.date_input('วันที่',format=('DD/MM/YYYY'))
                utility=options_form.selectbox('การไฟฟ้า',options='PBA')
                location=options_form.radio('พื้นที่ขัดข้อง', options = ['สถานีไฟฟ้า หรือ SPP', 'ระบบจำหน่าย หรือ VSPP หรือ สายส่ง'])
        #if button_press:
            #new_data = {'eventid':add_ref,'การไฟฟ้า':add_name,'สถานีไฟฟ้า':add_age}
            #df1 = pd.DataFrame([new_data])
            #df = df.append(new_data, ignore_index=True)
            #df = pd.concat([df, df1])
            #df.to_csv('file.csv',index=False)
        #else:
        #    st.write(f"กรอกรายละเอียดในฟอร์ม")
        
        #edited_df = st.data_editor(df, num_rows="dynamic")
        #favorite_command = edited_df.loc[edited_df["สถานีไฟฟ้า"].idxmax()]["การไฟฟ้า"]
        #st.dataframe(edited_df,use_container_width=True)
        
        
        #st.write(df['eventid'].index())
        #st.write(eventid1)
        

        
                if location == 'สถานีไฟฟ้า หรือ SPP':
                    substation=options_form.selectbox('สถานีไฟฟ้า',options=['PBB'])
                    typedevice=options_form.selectbox('ประเภทอุปกรณ์',options={'CircuitBreaker','Relay'})
                    execcode=options_form.text_input('รหัสอุปกรณ์')

                    add_data=options_form.form_submit_button(label="Add new record")
                    

                if add_data:
                    df = pd.concat([oper_data, pd.DataFrame.from_records([{
                        'eventid':eventid,
                        'datetime':datetime,
                        'การไฟฟ้า':utility,
                        'พื้นที่ขัดข้อง':location,
                        'สถานีไฟฟ้า':substation,
                        'ประเภทอุปกรณ์':typedevice,
                        'รหัสอุปกรณ์':execcode,
                        'ID':oper_data['ID'].max()
                        }])])
                    try:
                        df.to_excel("file1.xlsx",index=False)
                    except:
                        st.warning("Unable to write, Please close your dataset !!")
                        with st.expander("Records"):
                            shwdata = st.multiselect('Filter :', df.columns, default=['product_name','type','category','serialNo','date_added','purchasing_price','selling_price','expected_profit'])
                            st.dataframe(df[shwdata],use_container_width=True)
                        with st.expander("Cross Tab"):
                            tab=pd.crosstab([df.category],df.type, margins=True)
                            st.dataframe(tab)       
        
        if func1 == 'แก้ไข event':
            #aggrid(oper_data, editable=True)
            #oper_data.to_excel("file1.xlsx",index=False)
            form2 = st.form(key='form2', clear_on_submit=True)
            edited_df = form2.data_editor(oper_data)
            Edit_data = form2.form_submit_button(label='Edit')
            
            if Edit_data:
                try:
                    edited_df.to_excel("file1.xlsx", index=False)
                except:
                    st.warning("Unable to write, Please close your dataset !!")
            #favorite_command = edited_df.loc[edited_df["eventid"].idxmax()]["การไฟฟ้า"]
            #st.markdown(f"Your favorite command is **{favorite_command}** 🎈")

        #row_index = st.number_input("เลือก EventID ที่ต้องการแก้ไข", 0, len(df)-1, step=1)
        #new_name = st.text_input("รหัสสั่งการ", df.loc[row_index, 'การไฟฟ้า'])
        #new_age = st.text_input("สถานที่", df.loc[row_index, 'สถานีไฟฟ้า'])

        # ปรับปรุงข้อมูลในตาราง
        #df.loc[row_index, 'Name'] = new_name
        #df.loc[row_index, 'Age'] = new_age

        # แสดงตารางหลังการแก้ไข
        #AgGrid(df)

if __name__ == '__main__':
    main()
