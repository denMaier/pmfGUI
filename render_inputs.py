import streamlit as st

def render_input_element(key, value, key_prefix=None, allowed_values=None):
    """
    Renders the appropriate Streamlit input element based on the value type.
    Args:
        key: The key of the item in the dictionary.
        value: The value of the item.
        key_prefix: (Optional) A prefix for streamlit element keys.
        allowed_values: (Optional) A list of allowed values.
    """
    if key_prefix is None:
        element_key = key
    else:
        element_key = f"{key_prefix}.{key}"
    if allowed_values is not None:
        # Use a selectbox if allowed_values are provided
        if not isinstance(value, (dict, list)):  # Selectbox only for non-container types
            if value not in allowed_values:
                if len(allowed_values) > 0:
                    selected_value = st.selectbox(f"{key}:", options=allowed_values, index=0, key=element_key)
                else:
                    st.write(f"{key}: No options available.")
                    return
            else:
              selected_value = st.selectbox(f"{key}:", options=allowed_values, index=allowed_values.index(value), key=element_key)
            return selected_value #Important, as before
    if isinstance(value, dict):
        with st.expander(f"{key}:", expanded=True):
            selected_values = {}
            for sub_key, sub_value in value.items():
                # Pass allowed_values if it was provided
                selected_values[sub_key] = render_input_element(sub_key, sub_value, key_prefix=element_key, allowed_values=allowed_values)
            return selected_values
    elif isinstance(value, list):
        with st.expander(f"{key}:", expanded=True):
            selected_values = []
            for i, item in enumerate(value):
                # Pass allowed_values if it was provided
                selected_values.append(
                    render_input_element(f"[{i}]", item, key_prefix=element_key, allowed_values=allowed_values)
                )
            return selected_values
    elif isinstance(value, int):
        new_value = st.number_input(f"{key}:", value=value, key=element_key, step=1) # step=1 for integers
        return new_value
    elif isinstance(value, float):
        new_value = st.number_input(f"{key}:", value=value, key=element_key, format="%.5e")  # Scientific notation
        return new_value
    elif isinstance(value, str):
        if len(value) < 100:
           new_value = st.text_input(f"{key}:", value=value, key=element_key)
        else:
            new_value = st.text_area(f"{key}:", value=value, key=element_key, height=200)
        return new_value
    elif isinstance(value, tuple):
        v1, v2, v3 = value
        vector = st.columns(3)
        with vector[0]:
            gx = st.number_input("x", value=v1, key=f"{element_key}_x")
        with vector[1]:
            gy = st.number_input("y", value=v2, key=f"{element_key}_y")
        with vector[2]:
            gz = st.number_input("z", value=v3, key=f"{element_key}_z")
        return (gx, gy, gz)
    elif isinstance(value, bool):
        new_value = st.toggle(f"{key}:", value=value, key=element_key)
        return new_value
    else:
        st.text(f"{key}: {value} (Unsupported type)")
        return value
