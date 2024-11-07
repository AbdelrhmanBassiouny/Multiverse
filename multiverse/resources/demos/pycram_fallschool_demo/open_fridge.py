from multiverse_client_py import MultiverseClient, MultiverseMetaData, SocketAddress
import rospy

class MultiverseConnector(MultiverseClient):
    def __init__(self, client_addr: SocketAddress, multiverse_meta_data: MultiverseMetaData) -> None:
        super().__init__(client_addr, multiverse_meta_data)

    def loginfo(self, message: str) -> None:
        print(f"INFO: {message}")

    def logwarn(self, message: str) -> None:
        print(f"WARN: {message}")

    def _run(self) -> None:
        self.loginfo("Start running the client.")
        self._connect_and_start()

    def send_and_receive_meta_data(self) -> None:
        self.loginfo("Sending request meta data: " + str(self.request_meta_data))
        self._communicate(True)
        self.loginfo("Received response meta data: " + str(self.response_meta_data))

    def send_and_receive_data(self) -> None:
        self.loginfo("Sending data: " + str(self.send_data))
        self._communicate(False)
        self.loginfo("Received data: " + str(self.receive_data))

if __name__ == "__main__":
    multiverse_meta_data = MultiverseMetaData(
        world_name="real",
        simulation_name="fridge_opener",
        length_unit="m",
        angle_unit="rad",
        mass_unit="kg",
        time_unit="s",
        handedness="rhs",
    )
    client_addr = SocketAddress(port="5000")
    my_connector = MultiverseConnector(client_addr=client_addr,
                                       multiverse_meta_data=multiverse_meta_data)
    my_connector.run()

    # Set the fridge door joint

    joint_name = "fridge_door1_joint"
    joint_rvalue = [1.5]

    my_connector.request_meta_data["meta_data"]["simulation_name"] = "real"
    my_connector.request_meta_data["send"] = {}
    my_connector.request_meta_data["send"][joint_name] = ["joint_rvalue"]
    my_connector.send_and_receive_meta_data()
    my_connector.send_data = [my_connector.sim_time] + joint_rvalue
    my_connector.send_and_receive_data()

    my_connector.stop()
