import pyshark
from confluent_kafka import Producer
import json

# Kafka configuration
kafka_config = {
    'bootstrap.servers': 'localhost:9092'
}
producer = Producer(kafka_config)

# Delivery callback for Kafka
def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# Function to process and send packets to Kafka
def process_packet(packet):
    try:
        packet_dict = {
            'frame_number': packet.number,
            'frame_time': str(packet.sniff_time),
            'frame_length': packet.length,
            'eth_src': packet.eth.src if hasattr(packet, 'eth') else None,
            'eth_dst': packet.eth.dst if hasattr(packet, 'eth') else None,
            'ip_src': packet.ip.src if hasattr(packet, 'ip') else None,
            'ip_dst': packet.ip.dst if hasattr(packet, 'ip') else None,
            'ip_proto': packet.ip.proto if hasattr(packet, 'ip') else None,
            'ip_length': packet.ip.len if hasattr(packet, 'ip') else None,
            'tcp_length': packet.tcp.len if hasattr(packet, 'tcp') else None,
            'tcp_srcport': packet.tcp.srcport if hasattr(packet, 'tcp') else None,
            'tcp_dstport': packet.tcp.dstport if hasattr(packet, 'tcp') else None,
        }
        producer.produce('network-traffic', key=str(packet.number), value=json.dumps(packet_dict), callback=delivery_report)
        producer.flush()
    except AttributeError as e:
        print(f"Missing attribute: {e}")

# List available interfaces
print(pyshark.tshark.tshark.get_tshark_interfaces())

# Start capturing packets on the specified interface
# Update 'Wi-Fi' or 'Ethernet 2' based on your available interfaces
capture = pyshark.LiveCapture(interface='Wi-Fi')
capture.apply_on_packets(process_packet)
