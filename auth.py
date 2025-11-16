# auth.py
import streamlit as st
from database import add_user, get_user, verify_password

def login_user():
    """Handle user login"""
    st.subheader("Login")
    
    # Add unique keys to all inputs
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login", key="login_button"):
        if not username or not password:
            st.error("Please fill all fields")
            return
            
        user = get_user(username)
        if user and verify_password(password, user[3]):  # user[3] is password_hash
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def register_user():
    """Handle user registration"""
    st.subheader("Create New Account")
    
    # Add unique keys to all inputs
    username = st.text_input("Choose Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
    
    if st.button("Register", key="register_button"):
        if not username or not email or not password:
            st.error("Please fill all fields")
        elif password != confirm_password:
            st.error("Passwords don't match")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            if add_user(username, email, password):
                st.success("Account created successfully! Please login.")
            else:
                st.error("Username or email already exists")

def logout_user():
    """Handle user logout"""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.success("Logged out successfully!")
    st.rerun()

def check_auth():
    """Check if user is authenticated"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
    
    return st.session_state.logged_in