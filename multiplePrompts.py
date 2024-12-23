import os
import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv
import re
from pezzo.client import pezzo

load_dotenv()

os.environ['PEZZO_API_KEY'] = 'pez_5c1cf74f681fb6ad2535431ec7673c22'
os.environ['PEZZO_PROJECT_ID'] = 'cm4qt2zwg002zqk0hl0o7euva'
os.environ['PEZZO_ENVIRONMENT'] = 'Production'
os.environ['PEZZO_SERVER_URL'] = 'https://elsai-prompts-proxy.optisolbusiness.com'

# Fetch available prompts or specific prompt version from Pezzo

# Initialize Azure Chat Model
model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_MODEL_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version="2023-06-01-preview",
    temperature=0,
    top_p=1
)

# Connect to SQLite Database
db = SQLDatabase.from_uri("sqlite:///emissions.db")

# Create SQL Agent
agent_executor = create_sql_agent(
    model,
    db=db,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=100,
    agent_kwargs={
        "return_intermediate_steps": True,
        "seed": 42
    },
)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Consistent Report Generator")

# Input Form
with st.form("chat_form", clear_on_submit=True):
    submitted = st.form_submit_button("Send")

# Process User Input and Generate Reports
if submitted:
    # Start with an initial message to indicate processing
    st.session_state.messages.append({"user": "You", "content": "Generating the reports..."})

    # Initialize a string to collect all responses
    all_responses = ""

    # Define a list of prompts you want to run
    prompt_list = ["organizationsHeader", "overallSummary", "carbonEmissions","waterUsage","wasteManagement","socialDataAnalysis","governanceDataAnalysis","ESGPerformanceMetrics","futureGoalsAndStrategies","contactInfo"]
    #prompt_list = ["organizationsHeader","overallSummary","carbonEmissions","waterUsage"]
    #prompt_list = ["wasteManagement"]

    # Iterate over each prompt
    for prompt_name in prompt_list:
        try:
            # Fetch the prompt from Pezzo (you can modify version as per your need)
            prompt_template = pezzo.get_prompt(prompt_name)
            prompt = prompt_template.content['prompt']
            #st.write(f"Running prompt: {prompt_name}")
            #st.write(prompt)

            # Integrating the AzureChatOpenAI model with the fetched prompt
            #response = agent_executor.invoke(prompt_template)
            response = agent_executor.invoke(prompt)
            output = response["output"]
            #st.write(output)
            formatted_output = re.sub(r"(?<!\n)\n", "\n\n", output)  # Normalize spacing between paragraphs

            # Append the response to the all_responses string
            all_responses += f"\n\n{formatted_output}\n\n"

        except Exception as e:
            error_message = str(e)
            all_responses += f"An error occurred while generating the report for {prompt_name}. Error details: {error_message}\n\n"

    # After processing all prompts, append the accumulated response to the chat history
    st.session_state.messages.append({"user": "bot", "content": all_responses})
    #st.session_state.messages.append(all_responses)

# Display Chat History
st.subheader("Chat History")
for message in st.session_state.messages:
    if message["user"] == "You":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Bot:** {message['content']}")

st.divider()
