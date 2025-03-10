from typing import Literal
from pydantic import BaseModel
import streamlit as st
from components.sidebar import sidebar
from shared import constants
import json
from tools import extract_json
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI



api_key_1, selected_model = sidebar(constants.OPENROUTER_DEFAULT_CHAT_MODEL)


# Initialize the model
model_name = "google/gemini-2.0-flash-thinking-exp:free"
llm = ChatOpenAI(
    model=model_name,
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
    temperature=0.1,
    max_tokens=2000
)

# Category-specific prompts
outdoor_prompt = ChatPromptTemplate.from_messages(
    [("system", "You are an expert in analyzing outdoor layouts of telecom sites. Provide details such as sunshade presence, free positions, cable tray dimensions, and bus bars information."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

cabinet_prompt = ChatPromptTemplate.from_messages(
    [("system", "You are an expert in analyzing cabinets at telecom sites. Provide information such as cabinet count, type, vendor, model, and technical details."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

ran_prompt = ChatPromptTemplate.from_messages(
    [("system", "You are an expert in analyzing RAN equipment at telecom sites. Provide information such as equipment count, type, vendor, model, and technical details."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

transmission_prompt = ChatPromptTemplate.from_messages(
    [("system", "You are an expert in analyzing transmission equipment at telecom sites. Provide information such as equipment count, type, vendor, model, and technical details."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

# Category-specific chains
outdoor_chain = outdoor_prompt | llm | StrOutputParser()
cabinet_chain = cabinet_prompt | llm | StrOutputParser()
ran_chain = ran_prompt | llm | StrOutputParser()
transmission_chain = transmission_prompt | llm | StrOutputParser()

# Routing prompt and chain
route_system = """
Analyze the provided telecom site image and classify it into one of the following categories: Outdoor Layout, Cabinet, RAN, or Transmission.

Adhere strictly to the following rules:

1.  Respond ONLY with a JSON object.  Do not include any surrounding text, explanations, or markdown formatting.
2.  The JSON object must have the following format:

    ```
    {{"destination": "CategoryName"}}
    ```
3. The only valid values for the "destination" key are: "Outdoor Layout", "Cabinet", "RAN", and "Transmission".

Example Response:

{{"destination": "Cabinet"}}
"""


route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", route_system),
        ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}]),
    ]
)

class RouteQuery(BaseModel):
    destination: Literal["Outdoor Layout", "Cabinet", "RAN", "Transmission"]
"""
route_chain = (
    route_prompt
    | llm.with_structured_output(RouteQuery)
    | (lambda x: x.destination)
)
"""
# Define the processing chain
route_chain = (
    route_prompt
    | llm
    | RunnableLambda(lambda x: extract_json(x.content))  # Clean output if needed
    | JsonOutputParser()  # Parse JSON
    | (lambda x: RouteQuery(**x).destination)  # Validate with Pydantic and extract destination
)

# Main chain
chain = {
    "destination": route_chain,
    "image_path": RunnablePassthrough(),
} | RunnableLambda(
    lambda x: {
        "destination": x["destination"],  # Capture the category text
        "analysis": (
            outdoor_chain if x["destination"] == "Outdoor Layout" else
            cabinet_chain if x["destination"] == "Cabinet" else
            ran_chain if x["destination"] == "RAN" else
            transmission_chain
        ).invoke({"image_path": x["image_path"]})
    }
)

# Process image function
def process_image(image_path: str) -> dict:
    """Process an image using a file path and return a dictionary."""
    # Get routing information (which category the image belongs to)
    
    result = chain.invoke({"image_path": image_path})
     # Debug: Print the raw result before parsing
    #print(f"✅ Destination Category: {result['destination']}")
    #print(f"🔍 Analysis Results: {result['analysis']}")

    # Convert to dict if needed (preserve original structure)
    """
    if isinstance(result['analysis'], str):
        try:
            result['analysis'] = json.loads(result['analysis'])
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "raw_output": result}
    """
    print(result)

    return result  # Now always returns a dictionary