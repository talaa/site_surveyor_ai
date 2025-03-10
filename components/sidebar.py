import streamlit as st
import requests
import json
from shared import constants, utils


# Get available models from the API
def get_available_models():
    try:
        response = requests.get(constants.OPENROUTER_API_BASE + "/models")
        response.raise_for_status()
        models = json.loads(response.text)["data"]
        return [model["id"] for model in models]
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting models from API: {e}")
        return []


# Handle the model selection process
def handle_model_selection(available_models, default_model):
    # Initialize the model selection in session state if not already present
    if "model" not in st.session_state:
        st.session_state["model"] = default_model
    
    # Check if the currently selected model is in available models
    if st.session_state["model"] not in available_models:
        st.session_state["model"] = default_model
        
    # Get the index of the currently selected model
    selected_index = available_models.index(st.session_state["model"])
    
    # Create the selection box
    selected_model = st.selectbox(
        "Select a model", 
        available_models, 
        index=selected_index,
        key="model_selector"
    )
    
    # Update session state with the new selection
    st.session_state["model"] = selected_model
    return selected_model


def sidebar(default_model):
    """
    Creates a sidebar with model selection and other controls.
    
    Args:
        default_model: The default model to use if none is selected
        
    Returns:
        str: The selected model
    """
    with st.sidebar:
        st.title("Settings")
        
        # Model selection section
        st.subheader("Model Selection")
        
        # Get available models from the API
        available_models = get_available_models()
        
        # If no models are available, use a fallback list
        if not available_models:
            st.warning("Could not fetch models from API. Using default models.")
            available_models = [
                "anthropic/claude-3-haiku-20240307",
                "anthropic/claude-3-sonnet-20240229",
                "anthropic/claude-3-opus-20240229",
                "google/gemini-1.5-pro-latest",
                "google/gemini-1.5-flash-latest",
                "meta-llama/llama-3-70b-instruct",
                "microsoft/phi-3-medium-128k-instruct",
                default_model
            ]
        
        # Make sure default model is in the list
        if default_model not in available_models:
            available_models.append(default_model)
        
        # Handle model selection
        selected_model = handle_model_selection(available_models, default_model)
        
        # Add a temperature slider
        st.subheader("Model Parameters")
        temperature = st.slider(
            "Temperature", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.1, 
            step=0.1,
            help="Higher values make output more random, lower values more deterministic"
        )
        st.session_state["temperature"] = temperature
        
        # Add max tokens slider
        max_tokens = st.slider(
            "Max Tokens", 
            min_value=500, 
            max_value=4000, 
            value=2000, 
            step=100,
            help="Maximum number of tokens in the response"
        )
        st.session_state["max_tokens"] = max_tokens
        
        # Add a divider
        st.divider()
        
        # Add about section
        st.info("Telecom Site Analyzer v1.0")

    return selected_model