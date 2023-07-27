import streamlit as st
import openai
import os
import json
import requests
  
openai.api_base = "https://openai-mhsnalm.openai.azure.com/"


openai.api_version = "2023-07-01-preview"
openai.api_type = "azure"
openai.api_key = "09dcdc87479949daa767662e46468faf" # os.environ["OPENAI_API_KEY"]


# Define Streamlit app layout
st.title("Affordability Analyzer")
language = st.selectbox("Select Language", ["English", "French","German", "Chinese"])
query_input = st.text_area("Enter Query here")


# Temperature and token slider
temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.1
)
tokens = st.sidebar.slider(
    "Tokens",
    min_value=64,
    max_value=16000,
    value=4000,
    step=100
)

functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
            },
            "required": ["location"],
        }
    },
    {
        "name": "get_rental_amount",
        "description": "Get the rental amounts for a finance or lease loan.",
        "parameters": {
            "type": "object",
            "properties": {
                "financedAmount": {
                    "type": "integer",
                    "description": "Total finance amount",
                },
                "apr": {
                    "type": "integer",
                    "description": "Interest Rate ",
                },
                "contractTerms": {
                    "type": "integer",
                    "description": "Total number of months",
                },
                "rentalMode": {
                    "type": "string",
                    "description": "Payment Mode - Advance or Arrear",
                },
                "rentalFrequency": {
                    "type": "string",
                    "description": "Payment Frequency - 'Monthly', 'SemiAnnual', 'Quarterly', 'Annual', 'Weekly','Fortnightly'",
                },                  
            },
        }
    }
]


def call_post_endpoint_with_api_key(url, data):
    headers = {
        'x-api-key': 'pk_unity_2ae70138-d53b-11ed-be9b-7e87f65ba1ef',
        'Content-Type': 'application/json'  # Adjust the content type if your API requires a different one
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes

        # If the API returns JSON data in the response, you can access it like this:
        response_data = response.json()
        return response_data
    
    except requests.exceptions.RequestException as e:
        # Handle any request-related errors (e.g., connection error, timeout, etc.)
        print("Error:", e)
        return None


def get_rental_amount(request):
    payload = { "requestParam": { "apr": request.get("apr"), "contractTerms": request.get("contractTerms"), "rentalMode": request.get("rentalMode"), "rentalFrequency": request.get("rentalFrequency"), "financedAmount": request.get("financedAmount")}}
    
    response_data = call_post_endpoint_with_api_key('https://dev-api.netsolapp.io/marketplace/calculate/RentalAmountAnnuity', payload)
    
    return response_data

def get_current_weather(request):
    """
    This function is for illustrative purposes.
    The location and unit should be used to determine weather
    instead of returning a hardcoded response.
    """
    location = request.get("location")
    unit = request.get("unit")
    return {"temperature": "22", "unit": "celsius", "description": "Sunny"}


# Define function to explain code using OpenAI Codex
def call_flex(query, query_lang):
    messages = [
        {"role": "system", "content": f"If a value is not available make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous. Communicate in {query_lang} language."},
        {"role": "user", "content": query}
    ]

    chat_completion = openai.ChatCompletion.create(
        deployment_id="gpt35t16k",
        messages=messages,
        functions=functions,
    )
    
    function_call =  chat_completion.choices[0].message.function_call
    print(function_call.name)
    print(function_call.arguments)

    if function_call.name == "get_current_weather":
        response = get_current_weather(json.loads(function_call.arguments))
        
        messages.append(
            {
                "role": "function",
                "name": "get_current_weather",
                "content": json.dumps(response)
            }
        )
        
    if function_call.name == "get_rental_amount":
        response = get_rental_amount(json.loads(function_call.arguments))
        
        messages.append(
            {
                "role": "function",
                "name": "get_rental_amount",
                "content": json.dumps(response)
            }
        )        

    function_completion = openai.ChatCompletion.create(
        deployment_id="gpt35t16k",
        messages=messages,
        functions=functions,
    )

    return function_completion.choices[0].message.content.strip()


# Define Streamlit app behavior
if st.button("Send"):
    output_text = call_flex(query_input, language)
    st.text_area("Explanation", output_text)