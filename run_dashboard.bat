@echo off
echo Installing required packages for E-Commerce Dashboard...
echo.

REM Install required Python packages
pip install streamlit pandas numpy plotly seaborn matplotlib

echo.
echo Installation complete!
echo.
echo Starting the E-Commerce Analytics Dashboard...
echo.
echo The dashboard will open in your default web browser.
echo Use Ctrl+C to stop the dashboard when you're done.
echo.

REM Run the Streamlit dashboard
streamlit run ecommerce_dashboard.py

pause