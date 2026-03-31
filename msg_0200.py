import binascii
from datetime import datetime
from db_inserting import DatabaseManager

class HexDataProcessor0200():
    """
    A class to process raw hexadecimal data, parse it into individual packages, 
    and prepare the data for database insertion.
    """
    def __init__(self) -> None:
        # self.db_manager = DatabaseManager()
        self.db_manager = ''

    @staticmethod
    def hex_to_ascii(hex_str):
        """Convert a hex string to ASCII string."""
        return bytes.fromhex(hex_str).decode('ascii')
    
    @staticmethod
    def hex_to_binary(hex_str, bit_length=16):
        """Convert a hex string to a binary string with a fixed bit length."""
        return bin(int(hex_str, 16))[2:].zfill(bit_length)
    
    @staticmethod
    def bcd_to_datetime(bcd_str):
        """
        Convert a BCD timestamp string to a formatted datetime string 'YYYY-MM-DD HH:MM:SS'.
        """
        year = int(bcd_str[0:2]) + 2000  # Add 2000 for 2-digit years
        month = int(bcd_str[2:4])
        day = int(bcd_str[4:6])
        hour = int(bcd_str[6:8])
        minute = int(bcd_str[8:10])
        second = int(bcd_str[10:12])
        return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
       

    @staticmethod
    def parse_alarm_flags(alarm_flag_binary):
        """
        Parse the alarm flag binary string into individual flags with descriptions.
        """
        alarm_descriptions = {
            31: "Illegal door opening alarm",
            30: "Rollover warning",
            29: "Collision warning",
            28: "Illegal vehicle displacement",
            27: "Illegal ignition of vehicle",
            26: "Vehicle stolen",
            25: "Abnormal vehicle fuel level",
            24: "Vehicle VSS fault",
            23: "Route deviation alarm",
            22: "Road section driving time is insufficient",
            21: "Entry and exit route",
            20: "In and out of area",
            19: "Timeout parking",
            18: "Accumulated driving time on the day",
            15: "Reserved",
            14: "Fatigue driving warning",
            13: "Overspeed warning",
            12: "Road transport certificate IC card module failure",
            11: "Camera failure",
            10: "TTS module fault",
            9: "Terminal LCD or display failure",
            8: "Terminal main power failure",
            7: "Terminal main power undervoltage",
            6: "GNSS antenna short circuit",
            5: "GNSS antenna is not connected or cut off",
            4: "GNSS module failure",
            3: "Danger warning",
            2: "Fatigue driving",
            1: "Overspeed alarm",
            0: "Emergency alarm"
        }
        result = {
            "Alarm Flag": alarm_flag_binary,
            "Alarm flag object": {}
        }

        for bit_position, description in alarm_descriptions.items():
            result["Alarm flag object"][f"{description}"] = alarm_flag_binary[31 - bit_position]
        return result

    @staticmethod
    def parse_status_flags(status_bit_binary):
        """
        Parse the status bit binary string into individual flags with descriptions.
        """
        status_descriptions = {
            21: "Not using Galileo satellites for positioning",
            20: "Not using GLONASS satellites for positioning",
            19: "Use Beidou satellite for positioning",
            18: "Use GPS satellite for positioning",
            17: "Door 5 closed",
            16: "Door 4 closed",
            15: "Door 3 closed",
            14: "Door 2 closed",
            13: "Door 1 closed",
            12: "Door unlocked",
            11: "Vehicle circuit is normal",
            10: "Vehicle oil circuit is normal",
            5: "Longitude and latitude are not encrypted by the security plugin",
            4: "Operation status",
            3: "East longitude",
            2: "North Latitude",
            1: "Positioning",
            0: "ACC on",
        }

        result = {
            "Status Bit Flag": status_bit_binary,
            "Status flag object": {}
        }

        # Parse grouped bits
        result["Status flag object"]["[bit22~bit31] Reserved"] = status_bit_binary[:10]
        result["Status flag object"]["[bit8~bit9] Empty car"] = status_bit_binary[22:24]
        result["Status flag object"]["[bit6~bit7] Reserved"] = status_bit_binary[24:26]

        # Parse individual bits
        for bit_position, description in status_descriptions.items():
            bit_value = int(status_bit_binary[31 - bit_position])
            result["Status flag object"][description] = bit_value

        return result



    
    
    # Function to parse the additional information
    @staticmethod
    def parse_additional_info(data):
        index = 0
        result = []
        id_info = {
            1: "Mileage",
            2: "Fuel",
            3: "Speed_from_driving_record_function",
            4: "alarm_event_id",
            5: "Reserved",
            6: "Reserved",
            7: "Reserved",
            8: "Reserved",
            9: "Reserved",
            10: "Reserved",
            11: "Overspeed_alarm",
            12: "enter_and_exit_area/route_alarm",
            13: "Driving_time_alarm",
            14: "Reserved",
            15: "Reserved",
            16: "Reserved",
            17: "Reserved",
            18: "Reserved",
            19: "Reserved",
            20: "Reserved",
            21: "Reserved",
            22: "Reserved",
            23: "Reserved",
            24: "Reserved",
            25: "Extended_Vehicle_Signal_Status",
            42: "unknown",
            43: "Analog_input",
            48: "Wireless_communication_network",
            49: "Number_of_GNSS_Satellites",
            224: "Length_of_subsequent_custom_information",
            225: "Custom area",
            226: "Custom area",
            # Add more custom IDs if needed up to 255
        }

        while index < len(data):
            # Extract the ID and length
            try:
                info_id = int(data[index:index+2], 16)
                length = int(data[index+2:index+4], 16)
                value = data[index+4:index+4+length*2]
                readable_value = int(value, 16) if length > 1 else int(value, 16)
                result.append({
                    id_info.get(info_id, "Unknown") : readable_value,
                })
                index += 4 + length * 2
            except Exception as e:
                print(f"Error parsing additional info: {e}")
                break
        return result

    
    def process_raw_data(self, raw_data):
        """
        Process the raw hex data, parse each package, and send it to the database.
        """
        final_records = []
        # Extract static fields
        start_marker = raw_data[0:2]
        message_id = raw_data[2:6]
        message_body_attr = HexDataProcessor0200.parse_message_body_attribute(raw_data[6:10])
        phone_number = raw_data[10:22]
        serial_number = int(raw_data[22:26], 16)
        num_data_items = "1"
        position_data_type = raw_data[26:-4]
        Packet_End = raw_data[-2:]
        # Split packages using '7E' as start and end markers
        
        
        alarm_flag_binary = HexDataProcessor0200.hex_to_binary(position_data_type[0:8], bit_length=32)
        parsed_alarm_flags = HexDataProcessor0200.parse_alarm_flags(alarm_flag_binary)
        status_bit_flag = HexDataProcessor0200.hex_to_binary(position_data_type[8:16], bit_length=32)
        parsed_status_flags = HexDataProcessor0200.parse_status_flags(status_bit_flag)
        Latitude = int(position_data_type[16:24], 16)
        Longitude = int(position_data_type[24:32], 16)
        Elevation = int(position_data_type[32:36], 16)
        Speed = int(position_data_type[36:40], 16)
        Direction = int(position_data_type[40:44], 16)
        Positioning_time = HexDataProcessor0200.bcd_to_datetime(position_data_type[44:56])
        additional_information_id = position_data_type[56:]
        parsed_additional_info = HexDataProcessor0200.parse_additional_info(additional_information_id)
        # Assign values to variables in one line with defaults
        Mileage, Wireless_Signal_Strength, Number_of_GNSS_Satellites, Extended_Vehicle_Signal_Status, Unknown_Additional_Info_14, Unknown_Additional_Info_15, Unknown_Additional_Info_16, Unknown_Additional_Info_17, Unknown_Additional_Info_18 = (
            next((info.get(key) for info in parsed_additional_info if key in info), None) for key in [
                "Mileage",
                "Wireless_communication_network",  # Updated key to match parsed_additional_info
                "Number_of_GNSS_Satellites",  # Updated key to match parsed_additional_info
                "Extended_Vehicle_Signal_Status",  # Updated key to match parsed_additional_info
                "Unknown",  # For unknown info IDs
                "Unknown",
                "Unknown",
                "Unknown",
                "Unknown"
            ]
        )
    
        Packet_Start = start_marker
        Message_Id = message_id
        Version_Number = message_body_attr["Version_Number"]
        Terminal_Mobile_Phone_Number = phone_number
        Message_Serial_Number = str(serial_number)
        Number_of_Data_Items = num_data_items
        Position_Data_Type = "0"
        Packet_End = Packet_End

        Message_Body_Attributes = str(message_body_attr)
        Reserved_Bit15 = str(message_body_attr["Reserved_Bit15"])
        Reserved_Bit14 = str(message_body_attr["Reserved_Bit14"])
        Whether_to_Sub_Package = str(message_body_attr["Whether_to_Sub_Package"])
        Data_Encryption = str(message_body_attr["Data_Encryption"])
        Message_Body_Length = str(message_body_attr["Message_Body_Length"])

        # # -- Alarm Flags
        Illegal_Door_Opening_Alarm = int(parsed_alarm_flags["Alarm flag object"]["Illegal door opening alarm"])
        Rollover_Warning = int(parsed_alarm_flags["Alarm flag object"]["Rollover warning"])
        Collision_Warning = int(parsed_alarm_flags["Alarm flag object"]["Collision warning"])
        Illegal_Vehicle_Displacement = int(parsed_alarm_flags["Alarm flag object"]["Illegal vehicle displacement"])
        Vehicle_Illegal_Ignition = int(parsed_alarm_flags["Alarm flag object"]["Illegal ignition of vehicle"])
        Vehicle_Stolen = int(parsed_alarm_flags["Alarm flag object"]["Vehicle stolen"])
        Abnormal_Vehicle_Fuel_Level = int(parsed_alarm_flags["Alarm flag object"]["Abnormal vehicle fuel level"])
        Vehicle_VSS_Fault = int(parsed_alarm_flags["Alarm flag object"]["Vehicle VSS fault"])
        Route_Deviation_Alarm = int(parsed_alarm_flags["Alarm flag object"]["Route deviation alarm"])
        Driving_Time_Insufficient = int(parsed_alarm_flags["Alarm flag object"]["Road section driving time is insufficient"])
        Entry_And_Exit_Route = int(parsed_alarm_flags["Alarm flag object"]["Entry and exit route"])
        In_And_Out_Of_Area = int(parsed_alarm_flags["Alarm flag object"]["In and out of area"])
        Timeout_Parking = int(parsed_alarm_flags["Alarm flag object"]["Timeout parking"])
        Accumulated_Driving_Time = int(parsed_alarm_flags["Alarm flag object"]["Accumulated driving time on the day"])
        Reserved_Bit15_17 = str(parsed_alarm_flags["Alarm flag object"]["Reserved"])
        Fatigue_Driving_Warning = int(parsed_alarm_flags["Alarm flag object"]["Fatigue driving warning"])
        Overspeed_Warning = int(parsed_alarm_flags["Alarm flag object"]["Overspeed warning"])
        Road_Transport_IC_Card_Failure = int(parsed_alarm_flags["Alarm flag object"]["Road transport certificate IC card module failure"])
        Camera_Failure = int(parsed_alarm_flags["Alarm flag object"]["Camera failure"])
        TTS_Module_Fault = int(parsed_alarm_flags["Alarm flag object"]["TTS module fault"])
        LCD_Display_Failure = int(parsed_alarm_flags["Alarm flag object"]["Terminal LCD or display failure"])
        Terminal_Main_Power_Failure = int(parsed_alarm_flags["Alarm flag object"]["Terminal main power failure"])
        Main_Power_Undervoltage = int(parsed_alarm_flags["Alarm flag object"]["Terminal main power undervoltage"])
        GNSS_Antenna_Short_Circuit = int(parsed_alarm_flags["Alarm flag object"]["GNSS antenna short circuit"])
        GNSS_Antenna_Disconnected = int(parsed_alarm_flags["Alarm flag object"]["GNSS antenna is not connected or cut off"])
        GNSS_Module_Failure = int(parsed_alarm_flags["Alarm flag object"]["GNSS module failure"])
        Danger_Warning = int(parsed_alarm_flags["Alarm flag object"]["Danger warning"])
        Fatigue_Driving = int(parsed_alarm_flags["Alarm flag object"]["Fatigue driving"])
        Overspeed_Alarm = int(parsed_alarm_flags["Alarm flag object"]["Overspeed alarm"])
        Emergency_Alarm = int(parsed_alarm_flags["Alarm flag object"]["Emergency alarm"])

        # -- Status Flags
        Reserved_Bit22_31 = parsed_status_flags["Status flag object"]["[bit22~bit31] Reserved"]
        Not_Using_Galileo = parsed_status_flags["Status flag object"]["Not using Galileo satellites for positioning"]
        Not_Using_GLONASS = parsed_status_flags["Status flag object"]["Not using GLONASS satellites for positioning"]
        Using_Beidou = parsed_status_flags["Status flag object"]["Use Beidou satellite for positioning"]
        Using_GPS = parsed_status_flags["Status flag object"]["Use GPS satellite for positioning"]
        Door_5_Closed = parsed_status_flags["Status flag object"]["Door 5 closed"]
        Door_4_Closed = parsed_status_flags["Status flag object"]["Door 4 closed"]
        Door_3_Closed = parsed_status_flags["Status flag object"]["Door 3 closed"]
        Door_2_Closed = parsed_status_flags["Status flag object"]["Door 2 closed"]
        Door_1_Closed = parsed_status_flags["Status flag object"]["Door 1 closed"]
        Door_Unlocked = parsed_status_flags["Status flag object"]["Door unlocked"]
        Vehicle_Circuit_Normal = parsed_status_flags["Status flag object"]["Vehicle circuit is normal"]
        Vehicle_Oil_Circuit_Normal = parsed_status_flags["Status flag object"]["Vehicle oil circuit is normal"]
        Empty_Car = parsed_status_flags["Status flag object"]["[bit8~bit9] Empty car"]
        Longitude_Latitude_Not_Encrypted = parsed_status_flags["Status flag object"]["Longitude and latitude are not encrypted by the security plugin"]
        Operation_Status = parsed_status_flags["Status flag object"]["Operation status"]
        East_Longitude = parsed_status_flags["Status flag object"]["East longitude"]
        North_Latitude = parsed_status_flags["Status flag object"]["North Latitude"]
        Positioning = parsed_status_flags["Status flag object"]["Positioning"]
        ACC_On = parsed_status_flags["Status flag object"]["ACC on"]

        # -- Location Information
        Latitude = str(Latitude)
        Longitude = str(Longitude)
        Elevation = str(Elevation)
        Speed = str(Speed)
        Direction = str(Direction)
        Positioning_Time = Positioning_time

        # # -- Additional Information
        Mileage = str(Mileage)
        Wireless_Signal_Strength = str(Wireless_Signal_Strength)
        Number_of_GNSS_Satellites = str(Number_of_GNSS_Satellites)
        Extended_Vehicle_Signal_Status = str(Extended_Vehicle_Signal_Status)
        Unknown_Additional_Info_14 = str(Unknown_Additional_Info_14)
        Unknown_Additional_Info_15 = str(Unknown_Additional_Info_15)
        Unknown_Additional_Info_16 = str(Unknown_Additional_Info_16)
        Unknown_Additional_Info_17 = str(Unknown_Additional_Info_17)
        Unknown_Additional_Info_18 = str(Unknown_Additional_Info_18)
    
        final_records = [(
            Packet_Start,
            Message_Id,
            Version_Number,
            Terminal_Mobile_Phone_Number,
            Message_Serial_Number,

            Number_of_Data_Items,
            Position_Data_Type,
            Packet_End,
            Message_Body_Attributes,
            Reserved_Bit15,

            Reserved_Bit14,
            Whether_to_Sub_Package,
            Data_Encryption,
            Message_Body_Length,
            Illegal_Door_Opening_Alarm,

            Rollover_Warning,
            Collision_Warning,
            Illegal_Vehicle_Displacement,
            Vehicle_Illegal_Ignition,
            Vehicle_Stolen,

            Abnormal_Vehicle_Fuel_Level,
            Vehicle_VSS_Fault,
            Route_Deviation_Alarm,
            Driving_Time_Insufficient,
            Entry_And_Exit_Route,

            In_And_Out_Of_Area,
            Timeout_Parking,
            Accumulated_Driving_Time,
            Reserved_Bit15_17,
            Fatigue_Driving_Warning,

            Overspeed_Warning,
            Road_Transport_IC_Card_Failure,
            Camera_Failure,
            TTS_Module_Fault,
            LCD_Display_Failure,

            Terminal_Main_Power_Failure,
            Main_Power_Undervoltage,
            GNSS_Antenna_Short_Circuit,
            GNSS_Antenna_Disconnected,
            GNSS_Module_Failure,

            Danger_Warning,
            Fatigue_Driving,
            Overspeed_Alarm,
            Emergency_Alarm,
            Reserved_Bit22_31,

            Not_Using_Galileo,
            Not_Using_GLONASS,
            Using_Beidou,
            Using_GPS,
            Door_5_Closed,

            Door_4_Closed,
            Door_3_Closed,
            Door_2_Closed,
            Door_1_Closed,
            Door_Unlocked,

            Vehicle_Circuit_Normal,
            Vehicle_Oil_Circuit_Normal,
            Empty_Car,
            Longitude_Latitude_Not_Encrypted,
            Operation_Status,

            East_Longitude,
            North_Latitude,
            Positioning,
            ACC_On,
            Latitude,

            Longitude,
            Elevation,
            Speed,
            Direction,
            Positioning_Time,

            Mileage,
            Wireless_Signal_Strength,
            Number_of_GNSS_Satellites,
            Extended_Vehicle_Signal_Status,
            Unknown_Additional_Info_14,

            Unknown_Additional_Info_15,
            Unknown_Additional_Info_16,
            Unknown_Additional_Info_17,
            Unknown_Additional_Info_18
        )]
        print(final_records)
        # self.db_manager.insert_in_parallel(final_records)


    
    @staticmethod
    def parse_message_body_attribute(hex_value):
        """
        Parse the message body attribute hexadecimal value into its binary components.
        """
        # Convert hex to binary
        binary_value = format(int(hex_value, 16), '016b')
        # Parse binary components
        result = {
            "Version_Number": "JTT2013",  # Assuming fixed version
            "Reserved_Bit15": int(binary_value[0]),
            "Reserved_Bit14": int(binary_value[1]),
            "Whether_to_Sub_Package": bool(int(binary_value[2])),
            "Data_Encryption": "None" if binary_value[3:6] == "000" else binary_value[3:6],
            "Message_Body_Length": int(binary_value[6:], 2),
        }
        return result


# Example raw data
if __name__ == "__main__":
    raw_data = "7E02000042660000000002000C00000000000C000300C646C0049FABD0039A00000000260312180132010400000000140400000000150400000000160400000000170200002A02000030015331010A717E"
    processor = HexDataProcessor0200()  # Create an instance of the class
    res = processor.process_raw_data(raw_data)  # Call the method on the instance




