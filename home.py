import openai
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.stateful_button import button
import re
import streamlit as st
from prompts import get_system_prompt
from snowflake.snowpark import Session
from config import conn_params
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from ml import fun_ml
import altair as alt
from linear import linear_ml
from snowflake.snowpark.functions import col
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import date
from test_price import test_price
st.set_page_config(layout = 'wide' , initial_sidebar_state = 'expanded')

st.markdown(
    """
    <div style="display: flex; justify-content: center; margin-top: -20px;">
        <img src="https://yash1505.blob.core.windows.net/imagecnt/SnowPilot%20Logo.png" width="500" />
    </div>
    """,
    unsafe_allow_html=True
)

page_selected = option_menu(
	            menu_title = None,
	            options = ['Home', 'New User Insurance Price Prediction'],
	            default_index = 0,
	            icons=None,
	            menu_icon=None,
	            orientation='horizontal',
	            styles={

	            
	            "container": {"padding": "0!important", "background-color": "#fafafa"},
	            # "icon": {"color": "orange", "font-size": "25px"},
	            "icon":{"display":"none"},
	            "nav": {"background-color":"#f2f5f9"},
	            "nav-link": {"font-size": "14px",
	            "font-weight":"bold", 
	            "color":"#00568D",
	            "border-right":"1.5px solid #00568D",
				"border-left":"1.5px solid #00568D",
				"border-top":"1.5px solid #00568D",
				"border-bottom":"1.5px solid #00568D",
	            "padding":"10px", 
	            "text-transform": "uppercase",
	            "border-radius":"0px",
	            "margin":"5px",
	            "--hover-color": "#e1e1e1"},
	            "nav-link-selected": {"background-color":"#00568d", "color":"#ffffff"},
	            }
	            )

if page_selected == 'New User Insurance Price Prediction':
	test_price()

def calculate_age_adjustment(age):
    age = int(age)
    age_ranges = {
        (0, 3): 0.01,
        (4, 4): 0.015,
        (5, 5): 0.02,
        (6, 6): 0.025,
        (7, 7): 0.03,
        (8, 8): 0.04,
        (9, 9): 0.05,
        (10, 10): 0.06,
        (11, 14): 0.075,
        (15, 20): 0.1,
        (21, 30): 0.15,
        (31, 40): 0.2,
        (41, float('inf')): 0.3
    }
    for age_range, adjustment in age_ranges.items():
        start, end = age_range
        if start <= age <= end:
            return basic_price + basic_price * adjustment
    return 0




# if "status" not in st.session_state:
#      st.session_state.status = "system"



if "show_result" not in st.session_state:
    st.session_state.show_result = 0
if "data_query" not in st.session_state:
    st.session_state.data_query = ""
    


# Initialize the chat messages history
openai.api_key = conn_params["OPENAI_API_KEY"]
# print("generate prompt part ")
if "messages" not in st.session_state:
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
    st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]
if "intt" not in st.session_state:
     st.session_state.intt=0

st.sidebar.title("Know Your Premium")
VIN = st.sidebar.text_input("VIN:", placeholder= "Please provide the Vehicle Number:")



# Add checkboxes for showing/hiding SQL and result
# show_sql = st.sidebar.checkbox("Show SQL Query",    )


sql_displayed = False   
print("taking the prompt part and appending")
# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.intt=1
    st.session_state.messages.append({"role": "user", "content": prompt})

print("for message loop")
#display the existing chat messages
for message in st.session_state.messages:
    if message["role"] == "system":
        continue


    with st.chat_message(message["role"],avatar=("https://yash1505.blob.core.windows.net/imagecnt/Assistant.png" if message["role"] == "assistant" else "🧑")):

        # if message["content"][0]=="#":
        #     x=0
        # else:
        st.write(f'<span style="font-size: 22px;">{message["content"]}</span>', unsafe_allow_html=True)

        # if "results" in message:
        #     st.dataframe(message["results"])

# If last message is not from assistant, we need to generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant",avatar='https://yash1505.blob.core.windows.net/imagecnt/Assistant.png'):
        response = ""
        resp_container = st.empty()
        for delta in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            response += delta.choices[0].delta.get("content", "")       
            resp_container.markdown(f"""<div style="
                     font-size: 20px;
                     ">{response}</div>""",unsafe_allow_html=True)


        print(response)
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
        # response = "##"+ response
        # response = response.replace(sql_match.group(0), "")
        if st.session_state.intt == 0:    
            message = {"role": "assistant", "content": response}
        else:
             message = {"role": "assistant", "content": response}
        

        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)

        message["results"]=[]

        if sql_match:
            st.session_state.data_query=sql_match.group(1)
            sql = sql_match.group(1)
            st.session_state.show_result=1
            
            session = Session.builder.configs(conn_params).create()
            message["results"] = session.sql(sql).collect()
            print(message["results"])
            
        st.session_state.messages.append(message)

# df=message["results"].toPandas()
show_result = st.sidebar.checkbox("Show Result", True)
show_graph=0
if(  message["results"] == [] ):
    x=0
else:
    show_graph = st.sidebar.checkbox("Show Graph", False)
    graph_type = st.sidebar.multiselect("Select graph type:", ["Bar chart","Double Bar Chart", "Line chart", "3D Scatter Plot","Scatter Plot", "Pie chart"],default="Bar chart")

if show_result:
    print(type(message["results"]))
    if(st.session_state.show_result==0):
        st.write("")
    elif message["results"]== []:
        st.write(f'<span style="font-size: 20px;">We didn''t find any result regarding you prompt</span>', unsafe_allow_html=True)
        # st.dataframe(message["results"])
    else:

        # st.write(f"{message['results'][0][0]}") # gets the value
        data_frame = message["results"]
# Get the column names from the DataFrame
        column_names = data_frame[0].asDict().keys()
# Print or display the column names
        column_names_list = list(column_names)
        # st.write(column_names_list[0]) # gets the column naem
        # st.dataframe(message["results"])
        if(column_names_list[0].upper() == "ML_PRICE" or column_names_list[0].upper() == "PREMIUM_PRICE" or  column_names_list[0].upper() == "INSURANCE_PRICE") or column_names_list[0].upper() == "DISCOUNT_PREMIUM_PRICE":
            formatted_number = "{:.2f}".format(message["results"][0][0])
            centered_markdown = f'\n\nThe Premium Price for this vehicle is {formatted_number}\n\n'
            st.markdown(f"""<div style="                        
                     text-align: center;                     
                     font-size: 22px;
                     color: #4018f5;">The Premium Price for this vehicle is {formatted_number}</div>""",unsafe_allow_html=True)
            #  st.write(f'<span style="font-size: 50px;">{centered_markdown}</span>', unsafe_allow_html=True)
            # st.write(f"The Premium Price for this vehicle is {message['results'][0][0]}")
        else:  
            st.dataframe(message["results"])
else:
    st.write("")

# if show_sql:
#         # Display st.session_state.data_query with Markdown decoration
#     if st.session_state.data_query:
#         # f'<span style="font-size: 24px;">{var}</span>', unsafe_allow_html=True
#         centered_markdown = f'<div style="text-align: center;">\n\n**SQL Query:**\n\n```sql\n{st.session_state.data_query}\n```\n\n</div>'
#         st.markdown(centered_markdown, unsafe_allow_html=True)
#         # st.markdown(f"**SQL Query:**\n```sql\n{st.session_state.data_query}\n```")


if show_graph and st.session_state.data_query:
    df = pd.DataFrame(message["results"])
    

    for i in graph_type:
        if i == "Bar chart":

            left_columns, right_columns , more_columns = st.columns(3)

# Create a dropdown menu in the left column
            with left_columns:    
                x_column = st.selectbox("# **Select x-axis column for Bar chart**", df.columns)

# Create a dropdown menu in the right column
            with right_columns:    
                y_column = st.selectbox("# **Select y-axis column for Bar chart**", df.columns)
            fig = px.bar(df.head(10), x=x_column, y=y_column)
            fig.update_layout(
                xaxis_title= x_column,
                yaxis_title= y_column,
                title=f"Bar Chart of {x_column} vs {y_column}"
            )
            st.plotly_chart(fig)
        elif i == "Double Bar Chart":

            left_columns, right_columns ,more_columns = st.columns(3)
            
# Create a dropdown menu in the left column
            with left_columns:    
                x_columns = st.selectbox("# **Select x-axis column for  Double Bar Chart**", df.columns)

# Create a dropdown menu in the right column
            with right_columns:    
                y_columns = st.selectbox("# **Select y-axis column for Double Bar Chart**", df.columns)

            with more_columns:
                z_columns = st.selectbox("# **Select y2-axis column for Double Bar chart**:", df.columns)
            
            selected_columns = [x_columns, y_columns ,z_columns]
            
            if len(set(selected_columns)) < len(selected_columns):
                st.error("Please select different values from all the Drop-Down Menus")
            else:
                
            
                full_df = df[selected_columns].copy()
                new_df = full_df.head(8)
                st.write(new_df)

                # st.write(tables)
                        #transform dataframe 
                source=pd.melt(new_df, id_vars=[x_columns])
                chart=alt.Chart(source).mark_bar(strokeWidth=100).encode(
                x=alt.X('variable:N', title="", scale=alt.Scale(paddingOuter=0.1)),#paddingOuter - you can play with a space between 2 models 
                y='value:Q',
                color='variable:N',
                column=alt.Column('VIN:N', title="", spacing =0), #spacing =0 removes space between columns, column for can and st 
                ).properties( width = 100, height = 150, ).configure_header(labelOrient='bottom').configure_view(
                strokeOpacity=0)

                st.altair_chart(chart)

        elif i == "Line chart":
            left_columns, right_columns = st.columns(2)

# Create a dropdown menu in the left column
            with left_columns:    
                x_columns = st.selectbox("# **Select x-axis column for Line chart**", df.columns)

# Create a dropdown menu in the right column
            with right_columns:    
                y_columns = st.selectbox("# **Select y-axis column for Line chart**", df.columns)

            fig = px.line(df.head(10), x=x_columns, y=y_columns)
            fig.update_layout(
                xaxis_title= x_columns,
                yaxis_title= y_columns,
                title=f"Line Chart of {x_columns} vs {y_columns}"
            )
            st.plotly_chart(fig)
        elif i == "3D Scatter Plot":


            left_columns, right_columns ,more_columns = st.columns(3)

# Create a dropdown menu in the left column
            with left_columns:    
                x_columns = st.selectbox("# **Select x-axis column for 3D Scatter Plot**", df.columns)

# Create a dropdown menu in the right column
            with right_columns:    
                y_columns = st.selectbox("# **Select y-axis column for 3D Scatter Plot**", df.columns)

            with more_columns:
                z_columns = st.selectbox("Select z-axis column for 3D Scatter Plot:", df.columns)
            
            fig = px.scatter_3d(df.head(10), x=x_column, y=y_column, z=z_columns)
            fig.update_layout(
                scene=dict(
                    xaxis_title= x_column,
                    yaxis_title= y_column,
                    zaxis_title= z_columns
                ),
                title=f"3D Scatter Plot of {x_column}, {y_column}, {z_columns}"
            )
            st.plotly_chart(fig)
        elif i == "Scatter Plot":

            left_columns, right_columns  = st.columns(2)

# Create a dropdown menu in the left column
            with left_columns:    
                x_columns = st.selectbox("# **Select x-axis column for Scatter Plot**", df.columns)

# Create a dropdown menu in the right column
            with right_columns:    
                y_columns = st.selectbox("# **Select y-axis column for Scatter Plot**", df.columns)

            fig = px.scatter(df.head(10), x=x_column, y=y_column)
            fig.update_layout(
                xaxis_title= x_column,
                yaxis_title= y_column,
                title=f"Scatter Plot of {x_column} vs {y_column}"
            )
            st.plotly_chart(fig)
        else:
            left_columns, right_columns  = st.columns(2)

            # Create a dropdown menu in the left column
            with left_columns:    
                x_columns = st.selectbox("# **Select x-axis column for Pie Chart**", df.columns)
            # Create a dropdown menu in the right column
            with right_columns:    
                y_columns = st.selectbox("# **Select y-axis column for Pie Chart**", df.columns)

            fig = px.pie(df.head(10), values=y_column, names=x_column)
            fig.update_layout(
                title=f"Pie Chart of {x_column} vs {y_column}"
            )
            st.plotly_chart(fig)