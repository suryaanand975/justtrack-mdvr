import pyodbc
from configparser import ConfigParser
from threading import Lock, Thread
from datetime import datetime
from logger import Logger

class DatabaseManager:
    """Singleton class to manage database connections and bulk data insertion."""
    _instance = None
    _lock = Lock()

    def __init__(self):
        """Initialize the Logger instance."""
        self.logger = Logger()

    def __new__(cls):
        """Implement the singleton pattern to ensure only one instance exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize_connections()
            return cls._instance

    def _initialize_connections(self):
        """Set up database connections based on configuration."""
        try:
            config = ConfigParser()
            config.read('D:\\suryaanand\\MDVR_axelguard\\mdvr_config.ini')

            # Primary database configuration
            self._connection = pyodbc.connect(
                f"DRIVER={config.get('Database', 'driver')};"
                f"SERVER={config.get('Database', 'server')};"
                f"DATABASE={config.get('Database', 'database')};"
                f"UID={config.get('Database', 'username')};"
                f"PWD={config.get('Database', 'password')};Pooling=True",
                autocommit=True
            )
            self._cursor = self._connection.cursor()

            # Application database configuration
            self._app_connection = pyodbc.connect(
                f"DRIVER={config.get('App_Database', 'app_driver')};"
                f"SERVER={config.get('App_Database', 'app_server')};"
                f"DATABASE={config.get('App_Database', 'app_database')};"
                f"UID={config.get('App_Database', 'app_username')};"
                f"PWD={config.get('App_Database', 'app_password')};Pooling=True",
                autocommit=True
            )
            self._app_cursor = self._app_connection.cursor()

            # Stored procedures
            self.raw_sp = config.get('SP', 'Raw_SP')
            self.app_sp = config.get('SP', 'App_SP')

        except pyodbc.Error as e:
            self.logger.log_data("DB_connection_error", f"Database connection error: {e}")

    def execute_bulk_insert(self, cursor, query, records, db_name):
        """Helper method to execute bulk inserts."""
        try:
            cursor.executemany(query, records)
        except pyodbc.Error as e:
            self.logger.log_data(f"DB_insertion_error_{db_name}", f"Error inserting records into {db_name} DB: {e}")

    def insert_records_primary(self, records):
        """Bulk insert records into the primary database."""
        query = f'''EXEC {self.raw_sp} {', '.join(['?' for _ in range(len(records[0]))])};'''
        self.execute_bulk_insert(self._cursor, query, records, "primary")

    def insert_records_app(self, records):
        """Bulk insert records into the application-specific database."""
        query = f'''EXEC {self.app_sp} {', '.join(['?' for _ in range(len(records[0]))])};'''
        self.execute_bulk_insert(self._app_cursor, query, records, "app")

    def insert_in_parallel(self, records_primary):
        """Insert records into both databases in parallel using threads."""
        primary_thread = Thread(target=self.insert_records_primary, args=(records_primary,))
        # app_thread = Thread(target=self.insert_records_app, args=(records_app,))

        # Start threads
        primary_thread.start()
        # app_thread.start()

        # Wait for threads to complete
        primary_thread.join()
        # app_thread.join()

if __name__ == "__main__":
    db_manager = DatabaseManager()

    # Sample records for both databases
    from datetime import datetime

    records_primary = [
        (
            # Packet Information (VARCHAR)
            "START",                    # @Packet_Start VARCHAR(20)
            "MSG01",                    # @Message_Id VARCHAR(20)
            "JTT2013",                  # @Version_Number VARCHAR(20)
            "0123456789",               # @Terminal_Mobile_Phone_Number VARCHAR(15)
            "SER123",                   # @Message_Serial_Number VARCHAR(20)
            "3",                        # @Number_of_Data_Items VARCHAR(20)
            "1",                        # @Position_Data_Type VARCHAR(20)
            "END",                      # @Packet_End VARCHAR(20)

            # Message Body Attributes (VARCHAR)
            "ATTR123",                  # @Message_Body_Attributes VARCHAR(20)
            "0",                        # @Reserved_Bit15 VARCHAR(20)
            "0",                        # @Reserved_Bit14 VARCHAR(20)
            "NO",                       # @Whether_to_Sub_Package VARCHAR(20)
            "None",                     # @Data_Encryption VARCHAR(20)
            "123",                      # @Message_Body_Length VARCHAR(20)

            # Alarm Flags (BIT)
            0,                         # @Illegal_Door_Opening_Alarm BIT
            0,                         # @Rollover_Warning BIT
            0,                         # @Collision_Warning BIT
            0,                         # @Illegal_Vehicle_Displacement BIT
            0,                         # @Vehicle_Illegal_Ignition BIT
            0,                         # @Vehicle_Stolen BIT
            0,                         # @Abnormal_Vehicle_Fuel_Level BIT
            0,                         # @Vehicle_VSS_Fault BIT
            0,                         # @Route_Deviation_Alarm BIT
            0,                         # @Driving_Time_Insufficient BIT
            0,                         # @Entry_And_Exit_Route BIT
            0,                         # @In_And_Out_Of_Area BIT
            0,                         # @Timeout_Parking BIT
            0,                         # @Accumulated_Driving_Time BIT
            "000",                     # @Reserved_Bit15_17 VARCHAR(20)
            0,                         # @Fatigue_Driving_Warning BIT
            0,                         # @Overspeed_Warning BIT
            0,                         # @Road_Transport_IC_Card_Failure BIT
            0,                         # @Camera_Failure BIT
            0,                         # @TTS_Module_Fault BIT
            0,                         # @LCD_Display_Failure BIT
            0,                         # @Terminal_Main_Power_Failure BIT
            0,                         # @Main_Power_Undervoltage BIT
            0,                         # @GNSS_Antenna_Short_Circuit BIT
            0,                         # @GNSS_Antenna_Disconnected BIT
            0,                         # @GNSS_Module_Failure BIT
            0,                         # @Danger_Warning BIT
            0,                         # @Fatigue_Driving BIT
            0,                         # @Overspeed_Alarm BIT
            0,                         # @Emergency_Alarm BIT

            # Status Flags (BIT and VARCHAR)
            "0000000000",               # @Reserved_Bit22_31 VARCHAR(10)
            0,                         # @Not_Using_Galileo BIT
            0,                         # @Not_Using_GLONASS BIT
            1,                         # @Using_Beidou BIT
            1,                         # @Using_GPS BIT
            0,                         # @Door_5_Closed BIT
            0,                         # @Door_4_Closed BIT
            0,                         # @Door_3_Closed BIT
            0,                         # @Door_2_Closed BIT
            0,                         # @Door_1_Closed BIT
            0,                         # @Door_Unlocked BIT
            1,                         # @Vehicle_Circuit_Normal BIT
            1,                         # @Vehicle_Oil_Circuit_Normal BIT
            "Empty",                   # @Empty_Car VARCHAR(20)
            0,                         # @Longitude_Latitude_Not_Encrypted BIT
            0,                         # @Operation_Status BIT
            1,                         # @East_Longitude BIT
            1,                         # @North_Latitude BIT
            1,                         # @Positioning BIT
            1,                         # @ACC_On BIT

            # Location Information (VARCHAR and DATETIME)
            "12.345678",               # @Latitude VARCHAR(50)
            "98.765432",               # @Longitude VARCHAR(50)
            "100",                     # @Elevation VARCHAR(50)
            "60",                      # @Speed VARCHAR(50)
            "180",                     # @Direction VARCHAR(50)
            datetime.now(),            # @Positioning_Time DATETIME

            # Additional Information (VARCHAR)
            "1234",                    # @Mileage VARCHAR(20)
            "90",                      # @Wireless_Signal_Strength VARCHAR(20)
            "10",                      # @Number_of_GNSS_Satellites VARCHAR(20)
            "OK",                      # @Extended_Vehicle_Signal_Status VARCHAR(20)
            "UNKNOWN14",               # @Unknown_Additional_Info_14 VARCHAR(20)
            "UNKNOWN15",               # @Unknown_Additional_Info_15 VARCHAR(20)
            "UNKNOWN16",               # @Unknown_Additional_Info_16 VARCHAR(20)
            "UNKNOWN17",               # @Unknown_Additional_Info_17 VARCHAR(20)
            "UNKNOWN18"                # @Unknown_Additional_Info_18 VARCHAR(20)
        )
    ]



    records_app = [
        (
            "APP01", "Unknown", datetime.now(), 90, 5, 60.5, 77.5, 13.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0,
            "1234", "90", "10", "OK", "UNKNOWN14", "UNKNOWN15", "UNKNOWN16", "UNKNOWN17", "UNKNOWN18"
        )
    ]

    # Insert records in parallel
    db_manager.insert_in_parallel(records_primary)
