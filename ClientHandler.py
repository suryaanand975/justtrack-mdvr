import socket
import threading
import time
import os
from logger import Logger
from msg_0740 import HexDataProcessor0740
from msg_0200 import HexDataProcessor0200

class MDVRClientHandler(threading.Thread):
    def __init__(self, client_socket, client_address, mdvr_server):
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self.mdvr_server = mdvr_server  # Retained as per your requirement
        self.running = True
        self.logging = Logger ()
        self.hex_data_processor = HexDataProcessor0740()
        self.hex_data_processor_0200 = HexDataProcessor0200()   #HexDataProcessor
        self.image_folder = "mdvr_images"
        os.makedirs(self.image_folder, exist_ok=True)
        self.buffer = b''
        self.image_buffer = b''

    def run(self):

        while self.running:
            try:

                data = self.client_socket.recv(65536)

                if not data:
                    break

                self.buffer += data

                while True:

                    start = self.buffer.find(b'\x7e')
                    if start == -1:
                        break

                    end = self.buffer.find(b'\x7e', start + 1)
                    if end == -1:
                        break

                    packet = self.buffer[start:end+1]
                    self.buffer = self.buffer[end+1:]

                    hex_data = packet.hex().upper()

                    print(f"Received Hex Data from {self.client_address}: {hex_data}")

                    stripped_data = self.unescape_data(hex_data[2:-2])

                    if not self.validate_checksum(stripped_data):
                        print("Invalid checksum")
                        continue

                    message_id = stripped_data[:4]

                    print("Message ID:", message_id)

                    if message_id == "0100":
                        self.logging.log_data("msg_id_0100", hex_data)
                        self.handle_terminal_registration(stripped_data)

                    elif message_id == "0102":
                        self.logging.log_data("msg_id_0102", hex_data)
                        self.handle_terminal_authentication(stripped_data)

                    elif message_id == "0002":
                        self.logging.log_data("msg_id_0002", hex_data)
                        self.handle_terminal_heart_beat(stripped_data)

                    elif message_id == "0200":
                        self.logging.log_data("msg_id_0200", hex_data)
                        self.hex_data_processor_0200.process_raw_data(hex_data)

                        terminal_phone = stripped_data[8:20]
                        response_serial = int(stripped_data[20:24], 16)

                        response = self.prepare_response(
                            terminal_phone,
                            response_serial,
                            "0200",
                            0
                        )

                        self.send_response(response)

                    elif message_id == "0801":
                        self.logging.log_data("msg_id_0801", hex_data)
                        self.handle_multimedia_upload(packet, stripped_data)

                    elif message_id == "0704":
                        self.logging.log_data("msg_id_0704", hex_data)
                        self.hex_data_processor.process_raw_data(hex_data)

                    elif message_id == "0900":
                        self.logging.log_data("msg_id_0900", hex_data)
                        self.handle_custom_data_message(stripped_data)
                    else:
                        self.logging.log_data("Unknow_data", hex_data)
            except Exception as e:
                print("Run loop error:", e)
                break


# -----------------------------------------------------------
# Terminal Registration (0100)
# -----------------------------------------------------------

    def handle_terminal_registration(self, hex_string):
        try:
            terminal_phone = hex_string[8:20]
            response_serial = int(hex_string[20:24], 16)

            response = self.prepare_registration_response(
                terminal_phone,
                response_serial
            )

            self.send_response(response)

        except Exception as e:
            print(f"Error handling terminal registration: {e}")



    def prepare_registration_response(self, terminal_phone, response_serial):

        start_flag = "7E"
        end_flag = "7E"

        message_id = "8100"

        auth_code = "313233343536"  # "123456" in hex

        # body = response_serial + result + auth_code
        message_body = f"{response_serial:04X}" + "00" + auth_code

        message_body_length = len(message_body) // 2
        message_body_attributes = f"{message_body_length:04X}"

        message_serial_number = f"{response_serial:04X}"

        combined_message = (
            message_id
            + message_body_attributes
            + terminal_phone
            + message_serial_number
            + message_body
        )

        checksum = self.calculate_checksum(combined_message)

        response = start_flag + combined_message + checksum + end_flag

        return response
#---------------------------------------------------------------------------- Terminal heartbeat -----------------------------------

    def handle_terminal_heart_beat(self, hex_string):
        try:
            # Prepare and send response
            terminal_phone = hex_string[8:20]
            response_serial = int(hex_string[20:24], 16)
            response_message_id = "0002"  # Acknowledging message ID 0002
            result = 0  # Success
            print(response_message_id)
            '018270061905'
            "7E0002000 0 018270061905 011B F17E"

            response = self.prepare_response(terminal_phone, response_serial, response_message_id, result)
            self.send_response(response)

        except ValueError as e:
            print(f"ValueError in terminal authentication: {e}")
        except Exception as e:
            print(f"Error handling terminal authentication: {e}")

#----------------------------------------------------------------------------terminal authentication-----------------------------------

    def handle_terminal_authentication(self, hex_string):
        try:
            # Prepare and send response
            terminal_phone = hex_string[8:20]
            response_serial = int(hex_string[20:24], 16)
            response_message_id = "0102"  # Acknowledging message ID 0102
            result = 0  # Success

            response = self.prepare_response(terminal_phone, response_serial, response_message_id, result)
            self.send_response(response)

        except ValueError as e:
            print(f"ValueError in terminal authentication: {e}")
        except Exception as e:
            print(f"Error handling terminal authentication: {e}")

#---------------------------------------------------------------------Data uplink pass-through-------------------------------

    def handle_custom_data_message(self, hex_string):
        try:
            # Send an acknowledgment for 0900
            terminal_phone = hex_string[8:20]
            response_serial = int(hex_string[20:24], 16)  # Use the received serial number
            response_message_id = "0900"  # Acknowledge the same message ID 0900
            result = 0  # Success

            response = self.prepare_response(terminal_phone, response_serial, response_message_id, result)
            self.send_response(response)

        except ValueError as e:
            print(f"ValueError in custom data message (0900): {e}")
        except Exception as e:
            print(f"Error handling custom data message (0900): {e}")


#---------------------------------------------------------------------Media data handling-------------------------------

    def handle_multimedia_upload(self, packet, stripped_data):
        try:

            terminal_phone = stripped_data[8:20]
            response_serial = int(stripped_data[20:24], 16)

            raw = packet[1:-1]

            msg_attr = int.from_bytes(raw[2:4], 'big')

            body_len = msg_attr & 0x03FF
            subpackage = msg_attr & 0x2000

            header_len = 12
            total_packets = 1
            packet_seq = 1

            if subpackage:
                header_len = 16
                total_packets = int.from_bytes(raw[12:14], 'big')
                packet_seq = int.from_bytes(raw[14:16], 'big')

            body = raw[header_len:header_len + body_len]

            media_id = body[0:4]
            key = terminal_phone + "_" + media_id.hex()

            if not hasattr(self, "media_sessions"):
                self.media_sessions = {}

            if key not in self.media_sessions:

                self.media_sessions[key] = {
                    "total": total_packets,
                    "received": {},
                    "start": time.time()
                }

                self.logging.log_data(
                    "msg_id_0801_start",
                    f"NEW IMAGE SESSION MEDIA_ID={key} TOTAL={total_packets}"
                )

            session = self.media_sessions[key]

            # -------- Extract image data dynamically --------

            jpeg_start = body.find(b'\xff\xd8')

            if jpeg_start != -1:
                media_data = body[jpeg_start:]
            else:
                media_data = body

            session["received"][packet_seq] = media_data

            self.logging.log_data(
                "msg_id_0801_fragment",
                f"MEDIA_ID={key} PACKET={packet_seq}/{total_packets}"
            )

            # -------- Check if all packets received --------

            if len(session["received"]) == session["total"]:

                full = b''

                for i in range(1, session["total"] + 1):

                    if i not in session["received"]:
                        self.logging.log_data(
                            "msg_id_0801_missing",
                            f"MISSING PACKET {i} MEDIA_ID={key}"
                        )
                        return

                    full += session["received"][i]

                # -------- Locate JPEG --------

                start = full.find(b'\xff\xd8')
                end = full.rfind(b'\xff\xd9')

                if start != -1 and end != -1 and end > start:

                    jpeg = full[start:end+2]

                    filename = f"{self.image_folder}/img_{key}.jpg"

                    with open(filename, "wb") as f:
                        f.write(jpeg)

                    self.logging.log_data(
                        "msg_id_0801_image_created",
                        f"FILE={filename} SIZE={len(jpeg)}"
                    )

                    print("Image saved:", filename)

                else:

                    self.logging.log_data(
                        "msg_id_0801_error",
                        f"JPEG markers not found MEDIA_ID={key}"
                    )

                del self.media_sessions[key]

            # -------- Send ACK --------

            response = self.prepare_8800_response(
                terminal_phone,
                response_serial,
                media_id.hex()
            )

            self.send_response(response)

            self.logging.log_data(
                "msg_id_0801_ack",
                f"ACK SENT MEDIA_ID={key}"
            )

        except Exception as e:

            self.logging.log_data(
                "msg_id_0801_error",
                str(e)
            )
#--------------------------------------------------------------------------RESPONSE--------------------------------------------

    def prepare_response(self, terminal_phone, response_serial, response_message_id, result=0):
        try:
            # Start and End flags
            start_flag = "7E"
            end_flag = "7E"
            # Message ID
            message_id = "8001"
            # Message body attributes (length = 5 bytes = 2 (serial) + 2 (message ID) + 1 (result))
            message_body_length = 5
            message_body_attributes = f"{message_body_length:04X}"  # Binary [0000000000000101]
            # Terminal Phone Number
            terminal_phone_number = terminal_phone
            # Message Serial Number
            message_serial_number = f"{response_serial:04X}"  # Acknowledging the received serial
            # Data object
            response_message_serial = f"{response_serial:04X}"
            response_message_id_hex =  f"{int(response_message_id, 16):04X}"
            result_hex = f"{result:02X}"  # 00 = Success
            # Construct the message body
            message_body = response_message_serial + response_message_id_hex + result_hex
            # Combine all fields (excluding checksum and end flag)
            combined_message = message_id + message_body_attributes + terminal_phone_number + message_serial_number + message_body
            # Calculate checksum (XOR of all bytes in the combined message)
            checksum = self.calculate_checksum(combined_message)
            # Complete the response
            response = start_flag + combined_message + checksum + end_flag
            return response
        except Exception as e:
            print(f"Error preparing response: {e}")
            return None
        
    def prepare_8800_response(self, terminal_phone, response_serial, media_id):

        start_flag = "7E"
        end_flag = "7E"

        message_id = "8800"

        # body = multimedia id + reload count
        message_body = media_id + "00"

        message_body_length = len(message_body) // 2
        message_body_attributes = f"{message_body_length:04X}"

        message_serial_number = f"{response_serial:04X}"

        combined_message = (
            message_id +
            message_body_attributes +
            terminal_phone +
            message_serial_number +
            message_body
        )

        checksum = self.calculate_checksum(combined_message)

        return start_flag + combined_message + checksum + end_flag

    def send_response(self, response):
        try:
            if response:
                self.client_socket.sendall(bytes.fromhex(response))
        except Exception as e:
            print(f"Error sending response: {e}")

    def parse_message_body_attributes(self, attribute_string):
        """Parses the message body attribute field."""
        attributes = int(attribute_string, 16)
        return {
            "[0000000000001110]Message body attributes": attributes,
            "Version Number": "JTT2013",
            "[bit15] Reserved": (attributes >> 15) & 0x1,
            "[bit14] Reserved": (attributes >> 14) & 0x1,
            "[bit13] Whether to sub-package": bool((attributes >> 13) & 0x1),
            "[bit10~bit12] Data encryption": "None",  # Assuming no encryption
            "[bit0~bit9] Message body length": attributes & 0x3FF,
        }

    @staticmethod
    def decode_authentication_code(hex_string):
        try:
            return bytes.fromhex(hex_string).decode(errors='ignore')
        except ValueError as e:
            print(f"Error decoding authentication code: {e}")
            return "Invalid Code"

    @staticmethod
    def calculate_checksum(data):
        checksum = 0
        for byte in bytes.fromhex(data):
            checksum ^= byte
        return f"{checksum:02X}"

    def validate_checksum(self, stripped_data):
        try:
            expected_checksum = int(stripped_data[-2:], 16)
            calculated_checksum = 0
            for byte in bytes.fromhex(stripped_data[:-2]):
                calculated_checksum ^= byte
            return calculated_checksum == expected_checksum
        except Exception as e:
            print(f"Error validating checksum: {e}")
            return False

    @staticmethod
    def unescape_data(data):
        try:
            return data.replace("7D02", "7E").replace("7D01", "7D")
        except Exception as e:
            print(f"Error unescaping data: {e}")
            return data
        


if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 9000))
    server_socket.listen(5)
    print("MDVR Server started and listening on port 9000")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New connection established from {client_address}")
            client_handler = MDVRClientHandler(client_socket, client_address, None)  # Passing mdvr_server as None
            client_handler.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()
