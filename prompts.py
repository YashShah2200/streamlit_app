import streamlit as st
from snowflake.snowpark import Session
from config import conn_params
import pandas as pd

DATABASE = "SNOWPILOT_DB" 
SCHEMA = "SNOWPILOT_SCHEMA" 

GEN_SQL = """
You will be acting as SnowPilot (an AI Snowflake SQL expert). 
Your goal is to provide correct, executable SQL queries to users.
 You will be replying to users who may be confused if you don't respond as an AI Snowflake SQL expert.
   You are given multiple tables, and each table name is enclosed in <tableName> tags, with columns listed in <columns> tags. The user will ask questions, and for each question, you should respond with an SQL query based on the question and the table.


{context}
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                                                                                                                                    
Here are critical rules for the interaction you must abide:
<rules>
1. If the users asks regarding the insurance price of this vehicle number then go for SNOWPILOT_DB.SNOWPILOT_SCHEMA.FINAL_ML_TABLE and the column name as DISCOUNT_PREMIUM_PRICE.
2. You MUST wrap the generated SQL queries within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
This markdown down can only be used one in single response
3.DO NOT change column name in select statement using AS keyword
4. Always limit number of rows to 10.
5. never ask which table to be used to generate the query.
6. You must join the required tables, if the user asks the information which is present in more than one table i.e., when you are taking columns from different tables use join to join the tables.
7. Text / string where clauses must be fuzzy match e.g ilike %keyword%
8. Make sure to generate a single Snowflake SQL code snippet, not multiple.
9. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names.
10. DO NOT put numerical at the very front of SQL variable.
11. If the column name is not avilable in the table then don't mention it in the query.
12. Consider the seatbelt indicator column (DRIVER_SEATBELT_INDICATOR_FIRST) in the silver table when the question is about LATCHED or UNLATCHED of seatbelt.
13. use "ilike %keyword%" for fuzzy match queries (especially for string datatypes in where condition)

</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```
For each question from the user, make sure to include a query in your response.

Now to get started, please  introduce yourself.
"""

@st.cache_data(show_spinner=False)
def get_table_context(db_name: str ,schema_name: str):

    query = f"""
     SELECT TABLE_NAME FROM {DATABASE}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_TYPE ILIKE 'BASE TABLE'
"""
    context=""
    # conn = st.experimental_connection("snowpark")

    session = Session.builder.configs(conn_params).create()
    tables = session.sql(query).to_pandas()
    # print(type(tables))
    # make a loop
    table_names = [
    f"{tables['TABLE_NAME'][i]}"
    for i in range(len(tables["TABLE_NAME"]))
    ]
    context = f"There are total of {len(tables)} tables in the current schema \n \n Table Name: \n \n "

    for i in range(len(table_names)):
        context= context + f" {i+1}. {DATABASE}.{SCHEMA}.{tables['TABLE_NAME'][i]}" + "\n";

    columns_info = {}
    # table = table_name.split(".")
    
    for table_name in table_names:

        updated_table_names=f"{DATABASE}.{SCHEMA}.{table_name}"
        
        # context = context + f"Here is the table name <tableName> {updated_table_names} </tableName>  \n"
        column_descriptions="";
        columns_query = f"""
            SELECT COLUMN_NAME, DATA_TYPE FROM {db_name}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}' 
        """
        columns = session.sql(columns_query).to_pandas()
        for i in range(len(columns["COLUMN_NAME"])):

            column_descriptions = column_descriptions+ f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}" +"\n"
                    
        context = context + " \n \n Here are the column names of each table \n\n"
        context = context + f"\n{updated_table_names}   :- \n<columns> \n  {column_descriptions} \n</columns> \n\n\n"


        
        if table_name in columns_info:
            columns_info[table_name].extend(column_descriptions)
        else:
            columns_info[table_name] = column_descriptions
        
        
    
    # updated_table_names = [{QUALIFIED_DB_NAME}+"."+{QUALIFIED_SCHEMA_NAME} + str(item) for item in table_names]     
#     context = f"""DATABASE NAME = {DATABASE}\n \nSCHEMA NAME= {SCHEMA}\n\n<tableName>\n\n{updated_table_names}\n\n</tableName>\n \n
# <columns>\n\n{columns_info}\n\n</columns>
#     """  
    return context

def get_system_prompt():
    table_context = get_table_context(
        db_name=DATABASE, 
        schema_name = SCHEMA
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for GMF ")
    st.markdown(get_system_prompt())
