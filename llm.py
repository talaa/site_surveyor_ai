from typing import Literal
from pydantic import BaseModel
import streamlit as st
import json
from dotenv import load_dotenv
import base64
import config
from prompts import Outdoor_prompt_main,Cabinet_prompt_main,ran_prompt_main,transmission_prompt_main,antenna_prompt_main,others_prompt_main
from tools import extract_json
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI




# Initialize the model
#model_name = "google/gemini-2.0-flash-thinking-exp:free"
#loading the envirnoment variables 
load_dotenv()

model_name = config.model_name


#model_name="anthropic/claude-3.7-sonnet"
llm = ChatOpenAI(
    model=model_name,
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
    temperature=0.1,
    max_tokens=2000
)

# Category-specific prompts
outdoor_prompt = ChatPromptTemplate.from_messages(
    [("system",Outdoor_prompt_main ),#"You are an expert in analyzing outdoor layouts of telecom sites. Provide details such as sunshade presence, free positions, cable tray dimensions, and bus bars information."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

cabinet_prompt = ChatPromptTemplate.from_messages(
    [("system", Cabinet_prompt_main),#"You are an expert in analyzing cabinets at telecom sites. Provide information such as cabinet count, type, vendor, model, and technical details."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

ran_prompt = ChatPromptTemplate.from_messages(
    [("system", ran_prompt_main),#"You are an expert in analyzing RAN equipment at telecom sites. Provide information such as equipment count, type, vendor, model, and technical details."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

transmission_prompt = ChatPromptTemplate.from_messages(
    [("system", transmission_prompt_main),#"You are an expert in analyzing transmission equipment at telecom sites. Provide information such as equipment count, type, vendor, model, and technical details."),
     ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])]
)

antenna_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", antenna_prompt_main),
        ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])
    ]
)
others_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", others_prompt_main),
        ("human", [{"type": "image_url", "image_url": {"url": "{image_path}"}}])
    ]
)

# Category-specific chains
outdoor_chain = outdoor_prompt | llm | StrOutputParser()
cabinet_chain = cabinet_prompt | llm | StrOutputParser()
ran_chain = ran_prompt | llm | StrOutputParser()
transmission_chain = transmission_prompt | llm | StrOutputParser()
antenna_chain = antenna_prompt | llm | StrOutputParser()
others_chain = others_prompt | llm | StrOutputParser()

# Routing prompt and chain
route_system = """
Analyze the provided telecom site image and classify it into one of the following categories: Outdoor Layout, Cabinet, RAN, or Transmission.

Adhere strictly to the following rules:

1.  Respond ONLY with a JSON object.  Do not include any surrounding text, explanations, or markdown formatting.
2.  The JSON object must have the following format:

    ```
    {{"destination": "CategoryName"}}
    ```
3. The only valid values for the "destination" key are: "Outdoor Layout", "Cabinet", "RAN", "Transmission","antenna" and "others".

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
    destination: Literal["Outdoor Layout", "Cabinet", "RAN","Transmission","antenna","others"]
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
            transmission_chain if x["destination"] == "Transmission" else
            antenna_chain if x["destination"] == "antenna" else
            others_chain
        ).invoke({"image_path": x["image_path"]})
    }
)

# Process image function
# Cache this function to avoid reprocessing the same image
@st.cache_data
def process_image(image_bytes=None, image_url=None) -> dict:
    """
    Process an image using either raw bytes or a URL and return a dictionary.
    
    Args:
        image_bytes: Raw image bytes 
        image_url: Direct URL to the image
        
    Returns:
        dict: Analysis results
    """
    # If we have image bytes but no URL, convert to data URL
    if image_bytes and not image_url:
        # Determine image format from bytes signature or default to JPEG
        # This is a simple check - you might want to use a more robust method
        image_format = "jpeg"
        if image_bytes[:2] == b'\x89\x50':  # PNG signature
            image_format = "png"
            
        # Create data URL
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:image/{image_format};base64,{encoded_image}"
    
    # Ensure we have a URL to work with
    if not image_url:
        return {"error": "No image provided"}
        
    # Get routing information and perform analysis
    result = chain.invoke(image_url)
    
    print(result)
    return result  # No