import streamlit as st
import requests

st.set_page_config(page_title="Financial Chatbot", layout="centered")

st.title("💰 Financial Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chatbot input
query = st.chat_input("Ask about finance or stocks...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    # Make API request to chatbot backend
    try:
        response = requests.get(f"http://127.0.0.1:8000/chatbot?query={query}")

        if response.status_code == 200:
            bot_reply = response.json().get("response", "Sorry, I couldn't process that.")
        else:
            bot_reply = f"❌ Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        bot_reply = f"⚠️ Request Error: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

# Stock Data Section
st.subheader("📈 Stock Data")
stock_symbol = st.text_input("Enter stock symbol (e.g., AAPL)")

if st.button("Get Stock Data"):
    if not stock_symbol:
        st.warning("⚠️ Please enter a stock symbol!")
    else:
        try:
            stock_response = requests.get(f"http://127.0.0.1:8000/stock?symbol={stock_symbol}")

            if stock_response.status_code == 200:
                stock_data = stock_response.json()

                if "error" in stock_data:
                    st.error(f"🚨 {stock_data['error']}")  # Show error if stock is invalid
                else:
                    st.success(f"✅ Showing recent data for **{stock_symbol.upper()}**")
                    
                    # Display Stock Data in a structured format
                    st.write("### 📊 Stock Details:")
                    st.write(f"**Current Price:** {stock_data['current_price']} ₹")
                    st.write(f"**Open Price:** {stock_data['open']} ₹")
                    st.write(f"**High Price:** {stock_data['high']} ₹")
                    st.write(f"**Low Price:** {stock_data['low']} ₹")
                    st.write(f"**Volume:** {stock_data['volume']} shares")

            else:
                st.error(f"❌ Error: {stock_response.status_code} - {stock_response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Request Error: {str(e)}")
