# Real-time Network Intrusion Detection System

## Overview
This project implements a real-time network intrusion detection system that captures network packets, analyzes them using a trained machine learning model, and logs the results. The system utilizes Kafka for message delivery and PyShark for packet capturing.

## Features
- **Packet Capture**: Captures live network packets using PyShark.
- **Data Processing**: Preprocesses captured packets and extracts relevant features.
- **Machine Learning**: Utilizes a trained model to predict the type of network traffic.
- **Data Logging**: Logs predictions and saves them to an Excel file for further analysis.

## File Descriptions
- **app.py**: Main application file that initializes the Kafka consumer, processes incoming packets, and saves results to an Excel file.
- **capture.py**: Responsible for capturing packets from the network and sending them to a Kafka topic for processing.
- **classifier_model.pkl**: The trained machine learning model used for making predictions on the captured data.
- **archive/**: Directory for storing archived Excel files containing logged data.

## Requirements
- Python 3.x
- Required libraries:
  - confluent_kafka
  - joblib
  - json
  - numpy
  - pandas
  - pyshark

## Setup
1. Install the required libraries:
   ```bash
   pip install confluent_kafka joblib numpy pandas pyshark
   ```
2. Ensure Kafka is running on your local machine.
3. Run the application:
   ```bash
   python app.py
   ```

## Usage
- The application will start capturing packets and processing them in real-time.
- Predictions will be logged and saved to an Excel file in the `archive/` directory.
