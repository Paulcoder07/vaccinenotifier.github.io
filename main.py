import streamlit as st
from PIL import Image
from fake_useragent import UserAgent
import requests
import pandas as pd
import base64
import altair as alt

rad=st.sidebar.radio("Navigation",["Home","Active cases","Developer Info"])

if rad=="Home":
    ua=UserAgent()
    header = {'User-Agent': str(ua.chrome)}
    state_response = requests.get(f"https://cdn-api.co-vin.in/api/v2/admin/location/states",headers=header)
    states = state_response.json()
    states_dict = {}
    states_dict['0'] = 'Select State'
    for i in states['states']:
        states_dict[i['state_id']] = i['state_name']
        states_list = list(states_dict.values())


    def get_key(dict,val):
        for key, value in dict.items():
            if val == value:
                return key
        return "key doesn't exist"

    def get_table_download_link(df,filename,text):
        """Generates a link allowing the data in a given panda dataframe to be downloaded
        in:  dataframe
        out: href string
        """
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
        return href

    def get_districts(key):
        district_response = requests.get(f"https://cdn-api.co-vin.in/api/v2/admin/location/districts/{key}", headers=header)
        district = district_response.json()
        district_dict = {}
        # district_dict['0'] = 'Select District'
        for i in district['districts']:
            district_dict[i['district_id']] = i['district_name']
        return district_dict

    def run():
        st.title("Vaccination-Notifier💉")
        age_display = ['Select Choice','Search by District','Search by Pin']
        choice = st.selectbox("Choose Center",age_display)
        if choice == 'Search by District':
            states_list.remove('Daman and Diu')
            states_box = st.selectbox("Select State",states_list)
            if states_box == 'Select State':
                st.warning('Select State')
            else:
                state_index = states_list.index(states_box)
                district_dict = get_districts(state_index)
                district_list = list(district_dict.values())
                ## Select Districts
                district_list.insert(0,'Select District')
                district_box = st.selectbox("Select District", district_list)
                if district_box == 'Select District':
                    st.warning('Select District')
                else:
                    dist_key = get_key(district_dict,district_box)

                ## Age
                age_display = ['18 & Above', '18-45', '45+']
                age = st.selectbox("Your Age", age_display)
                age_val = 0


                ## Vaccine Type
                vacc_display = ['Covishield','Covaxin', 'Sputnik V']
                vaccine = st.selectbox("Vaccine Type", vacc_display)
                vaccine_type = ''
                if vaccine == 'Covishield':
                    vaccine_type = 'COVISHIELD'
                elif vaccine == 'Covaxin':
                    vaccine_type = 'COVAXIN'
                else:
                    vaccine_type = 'SPUTNIK V'

                ## Fee Type
                fee_display = ['Free','Paid']
                fee = st.selectbox("Vaccine Type", fee_display)

                ## Select Date
                vac_date = st.date_input("Date")
                vac_date = str(vac_date).split('-')
                new_date = vac_date[2] + '-' + vac_date[1] + '-' + vac_date[0]

                if st.button("Search"):
                    # Fetch Center
                    center_response = requests.get(
                        f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={dist_key}&date={new_date}",
                        headers=header)
                    centers_data = center_response.json()
                    centers = pd.DataFrame(centers_data.get('centers'))

                    if centers.empty:
                        st.error('No Center found')
                    else:
                        session_ids = []
                        for j, row in centers.iterrows():
                            session = pd.DataFrame(row['sessions'][0])
                            session['center_id'] = centers.loc[j, 'center_id']
                            session_ids.append(session)

                        sessions = pd.concat(session_ids, ignore_index=True)
                        av_centeres = centers.merge(sessions, on='center_id')

                        ## Age filter
                        if age == '18 & Above':
                            age_val = 18
                            av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                        elif age == '18-45':
                            age_val = 45
                            av_centeres = av_centeres[av_centeres['max_age_limit'] == age_val]
                        else:
                            age_val = 45
                            av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]

                        av_centeres.drop(
                            columns=['sessions', 'session_id', 'lat', 'block_name', 'long', 'date', 'from', 'to', 'state_name',
                                     'district_name','max_age_limit', 'vaccine_fees'
                                     , 'allow_all_age'], inplace=True, errors='ignore')

                        ## Vaccine filter
                        av_centeres = av_centeres[av_centeres['vaccine'] == vaccine_type]

                        ## Fees filter
                        av_centeres = av_centeres[av_centeres['fee_type'] == fee]

                        new_df = av_centeres.copy()
                        new_df.columns = ['Center_ID', 'Name', 'Address', 'Pincode','Fee','Availability', 'Minimum Age', 'Vaccine Type', 'Timing','Dose 1','Dose 2']
                        new_df = new_df[['Center_ID', 'Name', 'Fee','Pincode',
                                         'Availability', 'Minimum Age', 'Vaccine Type', 'Timing', 'Address','Dose 1','Dose 2']]
                        if new_df.empty:
                            st.error("No Center found.")
                        else:
                            st.dataframe(new_df.assign(hack='').set_index('hack'))
                            st.markdown(get_table_download_link(new_df,district_box.replace(' ','_')+'_'+new_date.replace('-','_')+'.csv','Download Report'), unsafe_allow_html=True)
                            href = f'<a href="https://selfregistration.cowin.gov.in/">Book Slot</a>'
                            st.markdown(href,unsafe_allow_html=True)
        elif choice == 'Search by Pin':
                    ## Area Pin
                    area_pin = st.text_input('Enter your Area Pin-Code Eg.380015')
                    ## Age
                    age_display = ['18 & Above','18-45', '45+']
                    age = st.selectbox("Your Age", age_display)
                    age_val = 0
                    ## Vaccine Type
                    vacc_display = ['Covishield', 'Covaxin', 'Sputnik V']
                    vaccine = st.selectbox("Vaccine Type", vacc_display)
                    vaccine_type = ''
                    if vaccine == 'Covishield':
                        vaccine_type = 'COVISHIELD'
                    elif vaccine == 'Covaxin':
                        vaccine_type = 'COVAXIN'
                    else:
                        vaccine_type = 'SPUTNIK V'

                    ## Fee Type
                    fee_display = ['Free', 'Paid']
                    fee = st.selectbox("Vaccine Type", fee_display)

                    ## Select Date
                    vac_date = st.date_input("Date")

                    vac_date = str(vac_date).split('-')
                    new_date = vac_date[2] + '-' + vac_date[1] + '-' + vac_date[0]

                    if st.button("Search"):
                        center_response = requests.get(
                            f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={area_pin}&date={new_date}",
                            headers=header)
                        centers_data = center_response.json()
                        centers = pd.DataFrame(centers_data.get('centers'))
                        if centers.empty:
                            st.error('No Center found')
                        else:
                            session_ids = []
                            for j, row in centers.iterrows():
                                session = pd.DataFrame(row['sessions'][0])
                                session['center_id'] = centers.loc[j, 'center_id']
                                session_ids.append(session)

                            sessions = pd.concat(session_ids, ignore_index=True)
                            av_centeres = centers.merge(sessions, on='center_id')
                            print(av_centeres.columns)
                            ## Age filter
                            if age == '18 & Above':
                                age_val = 18
                                av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                            elif age == '18-45':
                                age_val = 45
                                av_centeres = av_centeres[av_centeres['max_age_limit'] == age_val]
                            else:
                                age_val = 45
                                av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]

                            av_centeres.drop(
                                columns=['sessions', 'session_id', 'lat', 'block_name', 'long', 'date', 'from', 'to', 'state_name',
                                        'district_name', 'max_age_limit', 'vaccine_fees'
                                    , 'allow_all_age'], inplace=True, errors='ignore')

                            ## Vaccine filter
                            av_centeres = av_centeres[av_centeres['vaccine'] == vaccine_type]

                            ## Fees filter
                            av_centeres = av_centeres[av_centeres['fee_type'] == fee]

                            new_df = av_centeres.copy()
                            new_df.columns = ['Center_ID', 'Name', 'Address', 'Pincode', 'Fee', 'Availability', 'Minimum Age',
                                            'Vaccine Type', 'Timing', 'Dose 1', 'Dose 2']
                            new_df = new_df[['Center_ID', 'Name', 'Fee', 'Pincode',
                                            'Availability', 'Minimum Age', 'Vaccine Type', 'Timing', 'Address', 'Dose 1',
                                            'Dose 2']]
                            if new_df.empty:
                                st.error("No Center found.")
                            else:
                                st.dataframe(new_df.assign(hack='').set_index('hack'))
                                st.markdown(get_table_download_link(new_df,area_pin+ '_' + new_date.replace('-',
                                                                                                                            '_') + '.csv',
                                                                    'Download Report'), unsafe_allow_html=True)
                                href = f'<a href="https://selfregistration.cowin.gov.in/">Book Slot</a>'
                                st.markdown(href, unsafe_allow_html=True)
    run()




if rad=="Active cases":
    #Get Covid-19 data by country
    url = "https://raw.githubusercontent.com/datasets/covid-19/main/data/countries-aggregated.csv"
    df = pd.read_csv(url)
    df = df.rename(columns={'Confirmed': 'Confirmed Cases'})

    #Get country population data
    url2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQWDB7LlBd2xZivtvv4T_Wh7Bmqh79Ed6CWAZnyMB23-Q-yHpGGew9_0OLV2xWqVXDywBV07FFe7YhL/pub?gid=1075357968&single=true&output=csv"
    pop = pd.read_csv(url2)
    pop = pop.rename(columns={'Country (or dependency)': 'Country'})

    #dictionary for renaming population data to match covid country names
    dict = {'Myanmar': 'Burma', 'Côte d\'Ivoire':'Cote d\'Ivoire', 'South Korea': 'Korea, South',
            'Saint Kitts & Nevis': 'Saint Kitts and Nevis', 'St. Vincent & Grenadines': 'Saint Vincent and the Grenadines',
            'United States': 'US', 'Czech Republic (Czechia)': 'Czechia', 'DR Congo': 'Congo (Kinshasa)', 'Congo': 'Congo (Brazzaville)'}

    pop['Country'] = pop['Country'].replace(dict)

    df = pd.merge(df, pop[['Country', 'Population (2020)']], on='Country', how='left')

    #Add a number of days count to each set of country data
    df['NumDays'] = pd.to_datetime(df['Date']) - pd.to_datetime('2020-01-22')
    df['NumDays'] = pd.to_numeric(df['NumDays'])/(60*60*12*1000000000)
    df['NumDays'] = df['NumDays'].astype(int)

    #Change Date from string to datetime format
    df['Date'] = pd.to_datetime(df['Date'])

    #Add page title and intro
    st.title("COVID-19 Global Time Series")
    st.write("Select a country or countries and measures from the panel at the left.")

    #Create sidebar widgets
    countries = st.sidebar.multiselect(
        "Select Countries",
        df['Country'].unique()
        )

    statlist = df.columns.drop(['Date', 'Country', 'NumDays', 'Population (2020)'])
    stats = st.sidebar.multiselect("Select Stats", statlist)


    type = st.sidebar.selectbox("Chart Type", ["Compare countries by each measure", "Compare measures for each country"])

    norm = st.sidebar.selectbox("Normalization", ["For Each Person (normalized)", "Count (not normalized)"])

    if countries == []:
            countries = ['India', 'US', 'Mexico']
            
    if stats == []:
            stats = ['Deaths', 'Confirmed Cases']
            
    dropstats = statlist.drop(stats)

    #Apply widget selections to covid dataset
    df_subset = df.loc[lambda d: d['Country'].isin(countries)]
    df_dates = df_subset['Date']
    df_subset = df_subset.groupby(['Country'], as_index = False).rolling(window = 7).mean()
    df_subset = df_subset.join(df_dates)
    df_subset = df_subset.groupby(['Country'], as_index = False).resample('7D', on = 'Date').last()

    if norm == "For Each Peron (normalized)":
            yaxis = 'For Each Person'
    else: yaxis = 'Count'

    if type == "Compare measures for each country":
        for country in countries:
            st.write(country)
            current_df = df_subset.loc[lambda d: d['Country'] == country]
            popn = current_df['Population (2020)'].iloc[1]
            current_df = current_df.drop(columns = dropstats)
            current_df = current_df.drop(columns = ['NumDays', 'Country'])
            current_df = pd.melt(current_df, id_vars = ['Date'], value_vars = stats, var_name = 'Measure', value_name = 'Count')
            current_df['For Each Person'] = (current_df['Count']/popn) * 100000
            
            line_chart = alt.Chart(current_df).mark_line().encode(
                x = 'Date',
                y = yaxis,
                color='Measure',
                strokeDash = 'Measure')
            st.altair_chart(line_chart)
            
    else:
        this_df = pd.melt(df_subset, id_vars = ['Date', 'Country', 'Population (2020)'], value_vars = stats, var_name = 'Measure', value_name = 'Count')

        for stat in stats:
            st.write(stat)
            current_df = this_df.loc[lambda d: d['Measure'] == stat]
            current_df['For Each Person'] = (current_df['Count']/current_df['Population (2020)']) * 100000
            
            line_chart = alt.Chart(current_df).mark_line().encode(
                x = 'Date',
                y = yaxis,
                color = 'Country', 
                strokeDash = 'Country')
            st.altair_chart(line_chart)

    if yaxis == 'For Each Person':
            st.write("For Each Person figure is per 100,000 population")   

if rad=="Developer Info":
    col1,col2=st.columns([1,3])
    col2.markdown("""<b>DEBDATTA SINGHA ROY</b>, MCA 2ND YEAR, RCCIIT""",unsafe_allow_html=True)
    col1.image("Debdatta.jpeg",width=60)

    col1,col2=st.columns([1,3])
    col2.markdown("""<b>NILANJANA SAHA</b>, MCA 2ND YEAR, RCCIIT""",unsafe_allow_html=True)
    col1.image("Nilanjana.jpg",width=60)

    col1,col2=st.columns([1,3])
    col2.markdown("""<b>SHANKAPRIYA DHALI</b>, MCA 2ND YEAR, RCCIIT""",unsafe_allow_html=True)
    col1.image("Shankapriya.jpeg",width=60)

    col1,col2=st.columns([1,3])
    col2.markdown("""<b>AHINDRI DUTTA</b>, MCA 2ND YEAR, RCCIIT""",unsafe_allow_html=True)
    col1.image("Ahindri.jpeg",width=60)

    col1,col2=st.columns([1,3])
    col2.markdown("""<b>KOUSHIK DEY</b>, MCA 2ND YEAR, RCCIIT""",unsafe_allow_html=True)
    col1.image("Koushik.jpeg",width=60)

    st.image("https://www.cowin.gov.in/assets/images/vaccin-childrens-img.svg",width=400)


footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p><a style='display: block; text-align: center;'target="_blank">Copyright © 2022 Vaccination-Notifier. All Rights Reserved</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True) 