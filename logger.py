import os
from datetime import datetime
import configparser

class Logger:

    def __init__(self, config_file_path='D:\\suryaanand\\MDVR_axelguard\\mdvr_config.ini'):
        self.config = self.load_config(config_file_path)
        self.log_dir_path = self.config.get('Logging', 'log_dir')
        self.current_log_folder = None
        self.check_current_log_folder()

    def load_config(self, config_file_path):
        config = configparser.ConfigParser()
        config.read(config_file_path)
        return config

    def check_current_log_folder(self):
        now = datetime.now()
        current_log_folder = os.path.join(self.log_dir_path, now.strftime('%Y-%m-%d'))
        if self.current_log_folder != current_log_folder:
            # If it's a new day or the first log, update the current log folder
            self.current_log_folder = current_log_folder
            os.makedirs(self.current_log_folder, exist_ok=True)

    def log_data(self, log_type, message):
        now = datetime.now()
        formatted_datetime = now.strftime('%Y-%m-%d %H:%M:%S')

        self.check_current_log_folder()

        # Append the log data to the current log folder
        log_file_path = os.path.join(self.current_log_folder, f"{log_type}.log")
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{formatted_datetime} - {log_type} ==> {message}\n")

# Example usage
if __name__ == "__main__":
    logger = Logger()

    unit_no = "91006"

    # Example GPS request logging
    logger.log_data("GPSRequest", f"Unit_no: {unit_no}")
    # Other GPS request logic...

    # Example alarm request logging
    logger.log_data("AlarmRequest", f"Unit_no: {unit_no}")
    # Other alarm request logic...
