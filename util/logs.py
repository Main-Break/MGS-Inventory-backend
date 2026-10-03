import os
import datetime


class Logs:
    def __init__(self):
        pass


    def file_msg(self, msg, type="info"):
        naming = f"[ {datetime.date} | {datetime.time} ]"
        name_file = f"{datetime.date}_{datetime.time}"

        try:
            with open(name_file, 'a') as file:                

                if type == "erro":
                    file.write(f"{naming} [ERROR] : {msg}")

                elif type == "info":
                    file.write(f"{naming} [INFO] : {msg}")

                elif type == "warn":
                    file.write(f"{naming} [WARN] : {msg}")

                else:
                    file.write(f"{naming} [----] : {msg}")

        except Exception as err:
            return False, str(err)
