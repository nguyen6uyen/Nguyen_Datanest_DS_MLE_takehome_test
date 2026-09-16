import streamlit as st
import pandas as pd
import os

# Set page config for a premium look
st.set_page_config(
    page_title="Retail Forecast Dashboard",
    page_icon="📈",
    layout="centered"
)

# Use inline HTML styling for guaranteed stable rendering in Streamlit
st.markdown('<h1 style="font-size: 2.5rem; font-weight: 700; color: #6B7280; margin-bottom: 0rem;">📈 Inventory Forecast - November 2015 Projection </h1>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_path = 'data/forecast.csv'
    if not os.path.exists(file_path):
        return None
    
    # Read the pre-computed predictions
    df = pd.read_csv(file_path)
    
    # Floor negative predictions to 0 (we can't sell negative items!)
    if 'predicted_sales' in df.columns:
        # Round to whole numbers, but KEEP as floats to prevent the Mac PyArrow int64 crash
        df['predicted_sales'] = df['predicted_sales'].clip(lower=0).round(0)
    return df

with st.spinner("Connecting to batch prediction database..."):
    df = load_data()

if df is None:
    st.error("⚠️ Forecasting database not found. Please ensure `data/forecast.csv` has been generated from the notebook.")
else:
    # User Input Panel
    st.write("### Search Inventory (Item ID)")
    
    # Create a nice layout for the search bar and button
    col_input, col_button = st.columns([3, 1])
    
    with col_input:
        # Default value is 5037, a popular item in the dataset
        item_search = st.number_input("Enter Item ID:", min_value=0, step=1, value=5037, label_visibility="collapsed")
        
    with col_button:
        # Removed use_container_width=True because it is triggering the Mac Segmentation Fault!
        search_clicked = st.button("Generate Forecast", type="primary")
    
    # When the user clicks the button or hits enter
    if search_clicked or item_search:
        # Filter the pre-computed batch predictions
        item_data = df[df['item_id'] == item_search]
        
        if item_data.empty:
            st.warning(f"Item ID {item_search} was not found in the November 2015 forecast list. (It may be discontinued).")
        else:
            # Aggregate the metrics across all shops
            total_predicted_sales = item_data['predicted_sales'].sum()
            total_shops_selling = len(item_data[item_data['predicted_sales'] > 0])
            
            st.divider()
            
            # Display premium KPI metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label=f"Total Projected Sales", value=f"{total_predicted_sales:,.0f} Units")
            with col2:
                st.metric(label="Shops with Projected Demand", value=f"{total_shops_selling} Shops")
                
            st.divider()
            
            # Display detailed breakdown by shop
            st.write("### Demand Breakdown by Shop")
            
            # Clean up the table for presentation
            display_df = item_data[['shop_id', 'predicted_sales']].copy()
            
            # Add the word "Shop" in front of the ID so it looks extremely premium
            display_df['shop_id'] = display_df['shop_id'].astype(str)
            
            display_df.rename(columns={'shop_id': 'Shop ID', 'predicted_sales': 'Projected Sales'}, inplace=True)
            display_df = display_df.sort_values('Projected Sales', ascending=False).reset_index(drop=True)
            
            # Format as strings to avoid PyArrow int64 crashes on Mac
            display_df['Projected Sales'] = display_df['Projected Sales'].apply(lambda x: f"{x:,.0f}")
            
            # Use st.dataframe for a scrollable, beautiful UI with equal width
            st.dataframe(
                display_df, 
                hide_index=True, 
                use_container_width=True
            )
