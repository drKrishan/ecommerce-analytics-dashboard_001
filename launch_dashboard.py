#!/usr/bin/env python3
"""
E-Commerce Dashboard Launcher
This script installs dependencies and launches the dashboard
"""

import subprocess
import sys
import os


def install_requirements():
    """Install required packages"""
    print("🔧 Installing required packages...")

    packages = [
        "streamlit==1.28.0",
        "pandas==2.1.0",
        "numpy==1.24.3",
        "plotly==5.15.0",
        "seaborn==0.12.2",
        "matplotlib==3.7.2",
    ]

    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            return False

    print("✅ All packages installed successfully!")
    return True


def launch_dashboard():
    """Launch the Streamlit dashboard"""
    print("🚀 Launching E-Commerce Analytics Dashboard...")
    print("📊 The dashboard will open in your default web browser.")
    print("🛑 Use Ctrl+C to stop the dashboard when you're done.")
    print("-" * 60)

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "ecommerce_dashboard.py"]
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user.")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")


def main():
    print("=" * 60)
    print("🏪 E-COMMERCE ANALYTICS DASHBOARD")
    print("📈 Professional Business Intelligence Solution")
    print("=" * 60)
    print()

    # Check if we're in the right directory
    if not os.path.exists("ecommerce_dashboard.py"):
        print("❌ Error: ecommerce_dashboard.py not found in current directory")
        print("Please make sure you're running this script from the correct folder.")
        return

    # Check for CSV files
    csv_files = [
        "customer_dim.csv",
        "item_dim.csv",
        "store_dim.csv",
        "time_dim.csv",
        "Trans_dim.csv",
        "fact_table.csv",
    ]

    missing_files = [f for f in csv_files if not os.path.exists(f)]
    if missing_files:
        print(f"⚠️  Warning: Missing CSV files: {', '.join(missing_files)}")
        print("Make sure all your data files are in the same directory.")
        print()

    # Install requirements
    if install_requirements():
        print()
        input("Press Enter to launch the dashboard...")
        launch_dashboard()
    else:
        print("❌ Installation failed. Please check your Python environment.")


if __name__ == "__main__":
    main()
