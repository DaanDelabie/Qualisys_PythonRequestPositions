import numpy as np
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import samplerate
import asyncio
import qtm

async def main(wanted_body, measuring_time):
    # Connect to qtm
    connection = await qtm.connect("192.108......")  #ENTER IP ADDRESS OF QUALISYS SERVER

    # Connection failed?
    if connection is None:
        print("Qualisys: Failed to connect")
        return

    # Take control of qtm, context manager will automatically release control after scope end
    async with qtm.TakeControl(connection, "PW"):  #ENTER PW
        await connection.new()

    # Get 6dof settings from qtm
    xml_string = await connection.get_parameters(parameters=["6d"])
    body_index = create_body_index(xml_string)

    temp_data = []
    def on_packet(packet):
        info, bodies = packet.get_6d()
        framenumber = packet.framenumber  # number of the frame/position estimate
        body_count = info.body_count  # amount of tracked bodies
        now = datetime.now()

        if wanted_body is not None and wanted_body in body_index:
            # Extract one specific body
            wanted_index = body_index[wanted_body]
            position, rotation = bodies[wanted_index]

            if not check_NaN(position, rotation):
                data = dict(t=now.strftime("%H:%M:%S"),
                            x=position[0] / 1000,  # x-position in [m]
                            y=position[1] / 1000,  # y-position in [m]
                            z=position[2] / 1000,  # z-position in [m]
                            rotation_matrix=rotation[0])

                temp_data.append(data)
                np.save('temp_data_qualisys\\temp_data_qualisys.npy', temp_data)

            else:
                print('Qualisys: No object detected')
        else:
            # Print all bodies
            print('Qualisys: NO BODY FOUND')

    # Start streaming frames
    await connection.stream_frames(components=["6d"], on_packet=on_packet)

    # Wait asynchronously some time
    await asyncio.sleep(measuring_time)

    # Stop streaming
    await connection.stream_frames_stop()


def get_Qualisys_Position(wanted_body, measuring_time):
    asyncio.get_event_loop().run_until_complete(main(wanted_body, measuring_time))


def average_qualisys_data(data_list):
    n = len(data_list)

    # Sum all values using list comprehensions and NumPy for the rotation matrix
    x_avg = sum(data['x'] for data in data_list) / n
    y_avg = sum(data['y'] for data in data_list) / n
    z_avg = sum(data['z'] for data in data_list) / n

    # Convert time to timedelta, then sum them up and average
    time_sum = sum((
        timedelta(hours=int(data['t'][:2]), minutes=int(data['t'][3:5]), seconds=int(data['t'][6:]))
        for data in data_list
    ), timedelta(0))  # Start with timedelta(0) instead of an integer

    avg_time = time_sum / n  # Average timedelta

    # Convert average timedelta back to HH:MM:SS format
    avg_time_str = str(avg_time).split('.')[0]  # Remove microseconds

    # Sum and average rotation matrices
    rotation_matrix_avg = sum(np.array(data['rotation_matrix']) for data in data_list) / n

    return {
        't': avg_time_str,
        'x': x_avg,
        'y': y_avg,
        'z': z_avg,
        'rotation_matrix': rotation_matrix_avg.tolist()  # Convert back to list
    }


if __name__ == "__main__":
    print('Get Qualisys Position Data')
    get_Qualisys_Position('Name_Body', 0.03)

    # Average positioning data recorded with Qualisys in given timeframe
    position_qualisys = average_qualisys_data(position_qualisys_record)
    print(position_qualisys)
  
