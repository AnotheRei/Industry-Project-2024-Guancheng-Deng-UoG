# ACTUS Model Demonstrations Web Application

This project is a web application developed as part of the 2024 University of Glasgow, Adam Smith Business School, Industry Project. The application was created by **Guancheng Deng** from **Quantitative Finance**.

## Project Overview

The ACTUS Model Demonstrations Web Application is built in a Django environment using Python 3.10. This application is an implementation of the concepts discussed in the research paper titled *Extending the ACTUS Model: Adapting Algorithmic Financial Contract Standards to Lease Contracts*. The primary purpose of this web app is to demonstrate the extension of the ACTUS model to accommodate general commercial real estate lease contracts.

## Installation

To set up this project locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YourUsername/ACTUS-Model-Demonstrations.git
2. **Navigate to the project directory, create a virtual environment, and activate it**:
   cd ACTUS-Model-Demonstrations
  python -m venv venv
  # On Windows:
  venv\Scripts\activate
  # On macOS/Linux:
  source venv/bin/activate
3. **Install the required dependencies**:
  pip install -r requirements.txt
4. **Apply migrations**:
  python manage.py migrate
5. **Run the development server**:
  python manage.py runserver
6. **Access the application**:
  Open your web browser and navigate to http://127.0.0.1:8000/ to access the web application.
