import ast
import os
import sys
import pickle

import streamlit as st
import pandas as pd

# ensure the local module folder is in Python path when Streamlit runs from another cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import load_data, get_recommendations


st.set_page_config(layout="wide")
st.title("🛍️ M2 SHOP HERE 🛍️")


def parse_image_field(item, products_df):
    if 'all_images' in products_df.columns:
        raw = item.get('all_images', '')
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = ast.literal_eval(raw)
                if isinstance(parsed, list) and parsed:
                    return parsed[0]
            except Exception:
                return raw
    if 'image_url' in products_df.columns:
        return item.get('image_url', None)
    return None


@st.cache_resource
def setup():
    # try loading precomputed data from pickle first
    pkl_path = os.path.join(os.path.dirname(__file__), 'Ecommarce.pkl')
    if os.path.exists(pkl_path):
        try:
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f)
            products_df = data.get('products_df') or data.get('products')
            reviews_df = data.get('reviews_df') or data.get('reviews')
            similarity_matrix = data.get('similarity_matrix') or data.get('similarity')
            if products_df is not None and reviews_df is not None:
                return products_df, reviews_df, similarity_matrix
        except Exception as e:
            st.warning(f"Failed to load {pkl_path}: {e}. Falling back to CSVs.")
    return load_data("products.csv", "reviews.csv")


def format_int(value):
    if value is None:
        return "0"
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return str(value)


products_df, reviews_df, similarity_matrix = setup()

if products_df.empty:
    st.error("Products dataset is empty. Please provide a valid products.csv file.")
    st.stop()

all_products = products_df['title'].fillna('').unique().tolist()
selected_product = st.selectbox("Select a product", all_products)

if selected_product:
    current_item = products_df[products_df['title'] == selected_product].iloc[0]
    current_asin = current_item.get('asin', '')

    col1, col2 = st.columns([1, 2])
    with col1:
        image_url = parse_image_field(current_item, products_df)
        if image_url:
            st.image(image_url, width=300)
        else:
            st.info("No product image available.")

    with col2:
        st.write(f"### {current_item.get('title', 'Untitled')}")
        st.write(f"**Brand:** {current_item.get('brand_name', 'N/A')}")
        st.write(f"**Price:** ${current_item.get('price_value', 'N/A')}")
        st.write(f"**Average Rating:** {current_item.get('rating_stars', 'N/A')} ⭐")
        st.write(f"**Rating Count:** {format_int(current_item.get('rating_count', 0))}")
        description = current_item.get('product_description', '')
        if description:
            st.write(description)

    st.markdown("---")
    st.subheader("💬 Customer Reviews for this Product")

    matching_reviews = reviews_df[reviews_df['productASIN'] == current_asin]
    if not matching_reviews.empty:
        for _, review in matching_reviews.head(5).iterrows():
            with st.container():
                st.write(f"**{review.get('reviewTitle', 'Review')}**")
                st.write(f"Rating: {review.get('rating', 'N/A')} ⭐")
                st.write(review.get('reviewText', ''))
                if review.get('verifiedPurchase'):
                    st.markdown("<small>Verified Purchase</small>", unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No reviews available for this product.")

    st.markdown("---")
    st.subheader("🔥 Customers who viewed this also liked")

    recommendations = get_recommendations(selected_product, products_df, similarity_matrix)
    if recommendations.empty:
        st.info("No recommendations available.")
    else:
        cols = st.columns(min(len(recommendations), 4))
        for idx, (_, rec_item) in enumerate(recommendations.iterrows()):
            with cols[idx % len(cols)]:
                rec_image = parse_image_field(rec_item, products_df)
                if rec_image:
                    st.image(rec_image, use_column_width=True)
                short_title = rec_item.get('title', 'Untitled')
                if len(short_title) > 40:
                    short_title = short_title[:37] + '...'
                st.write(f"**{short_title}**")
                st.write(f"Price: ${rec_item.get('price_value', 'N/A')}")
                
                
                
