from confluent_kafka import Consumer, KafkaError
import joblib
import json
import numpy as np
import pandas as pd
from datetime import datetime
import os

# Load your trained model
model = joblib.load('classifier_model.pkl')

# Initialize Kafka consumer
consumer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_conf)
consumer.subscribe(['network-traffic'])

# Initialize global data DataFrame
data = pd.DataFrame(columns=['timestamp', 'frame.number', 'frame.time', 'frame.len', 'eth.src', 'eth.dst', 'ip.src', 'ip.dst',
                             'ip.proto', 'ip.len', 'tcp.len', 'tcp.srcport', 'tcp.dstport', 'prediction'])

def preprocess_packet(packet):
    def mac_to_decimal(mac):
        return int(mac.replace(":", ""), 16) if mac else 0

    def ip_reformation(ip):
        return int(ip.replace(".", "")) if ip else 0

    features = [
        packet['frame_number'], packet['frame_time'], packet['frame_length'], 
        packet['eth_src'], packet['eth_dst'], packet['ip_src'], packet['ip_dst'],
        packet['ip_proto'], packet['ip_length'], packet['tcp_length'],
        packet['tcp_srcport'], packet['tcp_dstport']
    ]
    
    features[0] = int(features[0])
    features[1] = round(datetime.strptime(features[1], '%Y-%m-%d %H:%M:%S.%f').timestamp())
    features[3] = mac_to_decimal(features[3])
    features[4] = mac_to_decimal(features[4])
    features[5] = ip_reformation(features[5])
    features[6] = ip_reformation(features[6])
    features[2] = float(features[2]) if features[2] else 0.0
    features[7] = float(features[7]) if features[7] else 0.0
    features[8] = float(features[8]) if features[8] else 0.0
    features[9] = float(features[9]) if features[9] else 0.0
    features[10] = float(features[10]) if features[10] else 0.0
    
    return features

def save_to_excel(df):
    # Ensure archive directory exists
    archive_dir = 'archive'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # Create year directory
    now = datetime.now()
    year_dir = os.path.join(archive_dir, now.strftime('%Y'))
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)

    # Create month directory
    month_dir = os.path.join(year_dir, now.strftime('%m'))
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)

    # Create a file name with the current day
    file_name = now.strftime('%d_%m_%Y.xlsx')
    file_path = os.path.join(month_dir, file_name)

    # Write to Excel file
    try:
        if os.path.exists(file_path):
            with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='overlay') as writer:
                # Determine if the sheet already exists
                if 'Sheet1' in writer.sheets:
                    sheet = writer.sheets['Sheet1']
                    startrow = sheet.max_row
                else:
                    startrow = 0
                df.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=startrow)
        else:
            df.to_excel(file_path, index=False, header=True)
    except PermissionError:
        print(f"Permission denied: {file_path}")
    except Exception as e:
        print(f"An error occurred while saving to Excel: {e}")



def map_prediction_to_label(prediction):
    labels = {
        0: 'normal',
        1: 'wrong setup',
        2: 'DDoS',
        3: 'Data type probing',
        4: 'scan attack',
        5: 'man in the middle'
    }
    return labels.get(prediction[0], 'unknown')

def consume_packets():
    global data
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(msg.error())
                break
        packet = json.loads(msg.value().decode('utf-8'))
        preprocessed_data = preprocess_packet(packet)
        input_data = np.array(preprocessed_data).reshape(1, -1)
        df_input_data = pd.DataFrame(input_data, columns=['frame.number', 'frame.time', 'frame.len', 'eth.src', 'eth.dst', 'ip.src', 'ip.dst',
                                                        'ip.proto', 'ip.len', 'tcp.len', 'tcp.srcport', 'tcp.dstport'])

        # Ensure there are no NaN values in input data
        df_input_data = df_input_data.fillna(0)

        prediction = model.predict(df_input_data.drop(columns='frame.number', axis=1))
        label = map_prediction_to_label(prediction)
        print(f"Prediction: {label}")

        # Add prediction to data
        df_input_data['timestamp'] = datetime.now()
        df_input_data['prediction'] = label
        
        # Avoid concatenation of empty DataFrames
        if not df_input_data.empty and not df_input_data.isna().all().all():
            data = pd.concat([data, df_input_data], ignore_index=True)


        # Save data to Excel periodically (e.g., every 10 messages)
        if len(data) >= 10:
            save_to_excel(data)
            data = pd.DataFrame(columns=data.columns)  # Clear the DataFrame while preserving columns


if __name__ == '__main__':
    try:
        consume_packets()
    except KeyboardInterrupt:
        # Save any remaining data when the script is stopped
        if not data.empty:
            save_to_excel(data)
    finally:
        consumer.close()
