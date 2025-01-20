import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s       - %(message)s [%(filename)s:%(lineno)d]',  # Custom log format
    datefmt='%Y-%m-%d %H:%M:%S'  # Custom date format
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import streamlit as st
import pandas as pd

# Initialize session state
if "table_visible" not in st.session_state:
    st.session_state["table_visible"] = False  # Tracks if the table and button2 are visible
if "table_data" not in st.session_state:
    st.session_state["table_data"] = pd.DataFrame({"Column1": [], "Column2": []})  # Stores table data

# Button1 to display the editable table and button2
if st.button("Show Table (Button1)"):
    st.session_state["table_visible"] = True  # Set the table visibility flag to True
    # Initialize with default data for the first time
    st.session_state["table_data"] = pd.DataFrame({"Column1": [1, 2, 3], "Column2": [4, 5, 6]})

# Display the table and button2 if the visibility flag is True
if st.session_state["table_visible"]:
    # Editable table
    st.write("Editable Table:")
    st.session_state["table_data"] = st.data_editor(
        st.session_state["table_data"], num_rows="dynamic"
    )

    # Button2
    if st.button("Process Table (Button2)"):
        st.write("You clicked Button2!")
        # Example: Process the table data
        st.write(st.session_state["table_data"])
