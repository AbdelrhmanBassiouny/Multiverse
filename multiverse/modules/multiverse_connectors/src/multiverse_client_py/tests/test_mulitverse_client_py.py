import datetime
import signal
import subprocess
import threading
import unittest
from time import sleep, time
import os
from typing_extensions import List

from multiverse_client_py import MultiverseClient, MultiverseMetaData, SocketAddress


def start_multiverse_server(server_port: str) -> subprocess.Popen:
    return subprocess.Popen(["multiverse_server", f"tcp://127.0.0.1:{server_port}"])


def kill_multiverse_server(process: subprocess.Popen):
    process.send_signal(signal.SIGINT)
    process.wait()


# Change the following line to the IP address of the machine running multiverse_server
# SocketAddress.host = "tcp://192.168.178.171"


class MultiverseClientTest(MultiverseClient):
    def __init__(self,
                 client_addr: SocketAddress,
                 multiverse_meta_data: MultiverseMetaData) -> None:
        super().__init__(client_addr, multiverse_meta_data)

    def loginfo(self, message: str) -> None:
        print(message)

    def logwarn(self, message: str) -> None:
        print(message)

    def _run(self) -> None:
        self._connect_and_start()

    def send_and_receive_meta_data(self):
        self._communicate(True)

    def send_and_receive_data(self):
        self._communicate(False)


class MultiverseClientTestCase(unittest.TestCase):
    meta_data = MultiverseMetaData(
        world_name="world",
        length_unit="m",
        angle_unit="rad",
        mass_unit="kg",
        time_unit="s",
        handedness="rhs",
    )
    time_start = 0.0
    _server_port = "7000"
    _process = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.time_start = time()

    #
    # @classmethod
    # def tearDownClass(cls) -> None:
    #     kill_multiverse_server(cls._process)

    def create_multiverse_client_send(self, port, object_name, attribute_names):
        meta_data = self.meta_data
        meta_data.simulation_name = "sim_test_send"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.request_meta_data["send"][object_name] = attribute_names
        multiverse_client.run()
        return multiverse_client

    def multiverse_client_send_data(self, multiverse_client, send_data):
        multiverse_client.send_data = send_data
        multiverse_client.send_and_receive_data()

    def create_multiverse_client_receive(self, port, object_name, attribute_names):
        meta_data = self.meta_data
        meta_data.simulation_name = "sim_test_receive"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.request_meta_data["receive"][object_name] = attribute_names
        multiverse_client.run()
        return multiverse_client

    def create_multiverse_client_reset(self, port):
        meta_data = self.meta_data
        meta_data.simulation_name = "sim_test_reset"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.run()
        return multiverse_client

    def create_multiverse_client_spawn(self, port):
        meta_data = self.meta_data
        meta_data.simulation_name = "sim_test_spawn"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.run()
        return multiverse_client

    def test_multiverse_client_send_creation(self):
        multiverse_client_test_send = self.create_multiverse_client_send("1234", "object_1", ["position", "quaternion"])
        self.assertIn("time", multiverse_client_test_send.response_meta_data)
        time_send = multiverse_client_test_send.response_meta_data["time"]
        self.assertIn("send", multiverse_client_test_send.response_meta_data)
        send_objects = multiverse_client_test_send.response_meta_data["send"]
        self.assertDictEqual(multiverse_client_test_send.response_meta_data, {
            'meta_data': {'angle_unit': 'rad', 'handedness': 'rhs', 'length_unit': 'm', 'mass_unit': 'kg',
                          'simulation_name': 'sim_test_send', 'time_unit': 's', 'world_name': 'world'},
            'send': send_objects,
            'time': time_send})
        multiverse_client_test_send.stop()

    def test_multiverse_client_send_data(self, stop=True):
        multiverse_client_test_send = self.create_multiverse_client_send("1234", "object_1", ["position", "quaternion"])

        time_now = time() - self.time_start
        self.multiverse_client_send_data(multiverse_client_test_send, [time_now, 3.0, 2.0, 1.0, 1.0, 0.0, 0.0, 0.0])
        self.assertEqual(multiverse_client_test_send.receive_data, [time_now])
        if stop:
            multiverse_client_test_send.stop()

        return multiverse_client_test_send, time_now

    def test_multiverse_client_receive_creation(self):
        _, time_send = self.test_multiverse_client_send_data()

        multiverse_client_test_receive = self.create_multiverse_client_receive("1235", "object_1",
                                                                               ["position", "quaternion"])

        time_receive = multiverse_client_test_receive.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_receive.response_meta_data, {
            'meta_data': {'angle_unit': 'rad', 'handedness': 'rhs', 'length_unit': 'm', 'mass_unit': 'kg',
                          'simulation_name': 'sim_test_receive', 'time_unit': 's', 'world_name': 'world'},
            'receive': {'object_1': {'position': [3, 2, 1], 'quaternion': [1, 0, 0, 0]}}, 'time': time_receive})

        multiverse_client_test_receive.stop()

    def test_multiverse_client_send_data_2(self, stop=True):
        time_now = time()
        multiverse_client_test_send = self.create_multiverse_client_send("1234", "object_1", ["rgb_1280_1024"])
        print("Send request_meta_data takes time: ", time() - time_now)
        time_now = time() - self.time_start
        send_data = [int(i % 255) for i in range(1280 * 1024 * 3)]
        send_data = [time_now] + send_data
        self.multiverse_client_send_data(multiverse_client_test_send, send_data)

        self.assertEqual(multiverse_client_test_send.receive_data, [time_now])

        for _ in range(10):
            time_now = time()
            multiverse_client_test_send.send_and_receive_data()
            print("Send data takes time: ", time() - time_now)

        if stop:
            multiverse_client_test_send.stop()

        return multiverse_client_test_send, time_now

    def test_multiverse_client_send_data_3(self, stop=True):
        time_now = time()
        multiverse_client_test_send = self.create_multiverse_client_send("1234", "object_1", ["depth_1280_1024"])
        print("Send request_meta_data takes time: ", time() - time_now)

        time_now = time() - self.time_start
        send_data = [int(i % 65535) for i in range(1280 * 1024)]
        send_data = [time_now] + send_data
        self.multiverse_client_send_data(multiverse_client_test_send, send_data)

        self.assertEqual(multiverse_client_test_send.receive_data, [time_now])

        for _ in range(10):
            time_now = time()
            multiverse_client_test_send.send_and_receive_data()
            print("Send data takes time: ", time() - time_now)

        if stop:
            multiverse_client_test_send.stop()

        return multiverse_client_test_send, time_now

    def test_multiverse_client_receive_2(self):
        _, time_send = self.test_multiverse_client_send_data_2()

        multiverse_client_test_receive = self.create_multiverse_client_receive("1235", "object_1",
                                                                               ["rgb_1280_1024"])

        time_now = time()
        multiverse_client_test_receive.send_and_receive_meta_data()
        print("Receive response_meta_data takes time: ", time() - time_now)
        for i in multiverse_client_test_receive.response_meta_data["receive"]["object_1"]["rgb_1280_1024"]:
            self.assertEqual(i, int(i % 255))

        multiverse_client_test_receive.stop()

    def test_multiverse_client_receive_3(self):
        _, time_send = self.test_multiverse_client_send_data_3()

        multiverse_client_test_receive = self.create_multiverse_client_receive("1235", "object_1",
                                                                               ["depth_1280_1024"])

        time_now = time()
        multiverse_client_test_receive.send_and_receive_meta_data()
        print("Receive response_meta_data takes time: ", time() - time_now)
        for i in multiverse_client_test_receive.response_meta_data["receive"]["object_1"]["depth_1280_1024"]:
            self.assertEqual(i, int(i % 65535))

        multiverse_client_test_receive.stop()

    def test_multiverse_client_reset_creation(self):
        multiverse_client_test_reset = self.create_multiverse_client_reset("1236")
        self.assertIn("time", multiverse_client_test_reset.response_meta_data)
        time_reset = multiverse_client_test_reset.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_reset.response_meta_data, {
            'meta_data': {'angle_unit': 'rad', 'handedness': 'rhs', 'length_unit': 'm', 'mass_unit': 'kg',
                          'simulation_name': 'sim_test_reset', 'time_unit': 's', 'world_name': 'world'},
            'time': time_reset})
        multiverse_client_test_reset.stop()

    def test_multiverse_client_reset(self):
        self.test_multiverse_client_send_data()
        multiverse_client_test_reset = self.create_multiverse_client_reset("1236")

        multiverse_client_test_reset.send_data = [0.0]
        multiverse_client_test_reset.send_and_receive_data()

        self.assertEqual(multiverse_client_test_reset.receive_data, [0.0])
        multiverse_client_test_reset.stop()

    def test_multiverse_client_spawn_creation(self):
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1237")

        self.assertIn("time", multiverse_client_test_spawn.response_meta_data)
        time_spawn = multiverse_client_test_spawn.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_spawn.response_meta_data, {
            'meta_data': {'angle_unit': 'rad', 'handedness': 'rhs', 'length_unit': 'm', 'mass_unit': 'kg',
                          'simulation_name': 'sim_test_spawn', 'time_unit': 's', 'world_name': 'world'},
            'time': time_spawn})

        multiverse_client_test_spawn.stop()


class MultiverseClientComplexTestCase(unittest.TestCase):
    meta_data = MultiverseMetaData(
        length_unit="m",
        angle_unit="rad",
        mass_unit="kg",
        time_unit="s",
        handedness="rhs",
    )
    time_start = 0.0
    _server_port = "7000"
    _process = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.time_start = time()
        # _process = subprocess.Popen(["multiverse_launch", "multiverse/resources/muv/empty.muv"])

    # @classmethod
    # def tearDownClass(cls) -> None:
    #     kill_multiverse_server(cls._process)

    def create_multiverse_client_receive(self, port, object_name, attribute_names, world_name=None,
                                         simulation_name="sim_test_receive"):
        meta_data = self.meta_data
        meta_data.simulation_name = simulation_name
        if world_name is not None:
            meta_data.world_name = world_name
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.request_meta_data["receive"][object_name] = attribute_names
        multiverse_client.run()
        return multiverse_client

    def create_multiverse_client_spawn(self, port, world_name, simulation_name="sim_test_spawn"):
        meta_data = self.meta_data
        meta_data.world_name = world_name
        meta_data.simulation_name = simulation_name
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.run()
        return multiverse_client

    @staticmethod
    def reset_spawn_request_meta_data(multiverse_client):
        multiverse_client.request_meta_data["send"] = {}
        multiverse_client.request_meta_data["receive"] = {}
        return multiverse_client

    def create_multiverse_client_listenapi(self, port, world_name):
        meta_data = self.meta_data
        meta_data.world_name = world_name
        meta_data.simulation_name = "sim_test_listenapi"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)

        def func_1(args: List[str]) -> List[str]:
            return args

        def func_2(args: List[str]) -> List[str]:
            return [" ".join(args)]

        multiverse_client.api_callbacks = {
            "func_1": func_1,
            "func_2": func_2
        }
        multiverse_client.run()
        return multiverse_client

    def create_multiverse_client_callapi(self, port, world_name, api_callbacks, simulation_name="sim_test_callapi"):
        meta_data = self.meta_data
        meta_data.world_name = world_name
        meta_data.simulation_name = simulation_name
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.request_meta_data["api_callbacks"] = api_callbacks
        multiverse_client.run()
        return multiverse_client

    def test_attach_and_detach_object_with_a_world_link(self):
        # create world clients
        multiverse_client_test_receive = self.create_multiverse_client_receive("1337", "", [""],
                                                                               "world", "receiver")
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1338", "world",
                                                                           "writer")
        multiverse_test_call_api = self.create_multiverse_client_callapi("1339", "world", {},
                                                                         "sim_test_callapi")

        simulation_name = "pycram_test"

        # pause simulation
        self.pause_simulation(multiverse_test_call_api, simulation_name)

        obj_name = "milk_box"
        world_link_name = "cabinet10_drawer1"

        # Spawn object
        self.send_body_data(multiverse_client_test_spawn, obj_name,
                            {
                                "position": [-2.0, -2.0, 0.0],
                                "quaternion": [1.0, 0.0, 0.0, 0.0],
                                "relative_velocity": [0.0] * 6
                            },
                            simulation_name)

        # Attach object to a world link
        self.attach(multiverse_test_call_api, obj_name, world_link_name,
                    simulation_name=simulation_name)

        # Detach object from a world link
        self.detach(multiverse_test_call_api, obj_name, world_link_name,
                    simulation_name=simulation_name)

        # stop all clients
        multiverse_client_test_receive.stop()
        multiverse_client_test_spawn.stop()
        multiverse_test_call_api.stop()

    def test_spawn_robot_and_two_objects_and_get_contact_points_and_contact_effort_multiple_times(self):
        # create world clients
        multiverse_client_test_receive = self.create_multiverse_client_receive("1337", "", [""],
                                                                                 "world", "receiver")
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1338", "world",
                                                                            "writer")
        multiverse_test_call_api = self.create_multiverse_client_callapi("1339", "world", {},
                                                                            "sim_test_callapi")

        simulation_name = "empty_simulation"

        # pause simulation
        self.pause_simulation(multiverse_test_call_api, simulation_name)

        robot_name = "tiago_dual"
        obj_name_1 = "milk_box"
        obj_name_2 = "cup"
        n_repitions = 100

        for _ in range(n_repitions):
            self.reset_spawn_request_meta_data(multiverse_client_test_spawn)

            # Spawn robot
            self.send_body_data(multiverse_client_test_spawn, robot_name,
                                {
                                    "position": [-2.0, -2.0, 0.001],
                                    "quaternion": [1.0, 0.0, 0.0, 0.0],
                                    "relative_velocity": [0.0] * 6
                                },
                                simulation_name)

            sleep(0.5)

            # remove robot
            self.remove_object(multiverse_client_test_spawn, robot_name, simulation_name)

            sleep(0.5)

            # Spawn object 1
            self.send_body_data(multiverse_client_test_spawn, obj_name_1,
                                {
                                    "position": [1, 1, 0.01],
                                    "quaternion": [0.707, 0, -0.707, 0],
                                    "relative_velocity": [0.0] * 6
                                },
                                simulation_name)

            # Spawn object 2
            self.send_body_data(multiverse_client_test_spawn, obj_name_2,
                                {
                                    "position": [1, 1, 0.2],
                                    "quaternion": [1.0, 0.0, 0.0, 0.0],
                                    "relative_velocity": [0.0] * 6
                                },
                                simulation_name)

            # Get contact points and contact effort for object 1
            self.simulate(multiverse_test_call_api, simulation_name, datetime.timedelta(milliseconds=200))
            contact_data = self.get_contact_points_and_contact_effort(multiverse_test_call_api, obj_name_1,
                                                                      simulation_name)

            self.assertEqual(contact_data[0], [obj_name_2, 'world'])

            # Remove all objects
            self.remove_object(multiverse_client_test_spawn, obj_name_1, simulation_name)
            self.remove_object(multiverse_client_test_spawn, obj_name_2, simulation_name)

            # reset the world
            self.reset_world(multiverse_client_test_spawn, simulation_name)

        # stop all clients
        multiverse_client_test_receive.stop()
        multiverse_client_test_spawn.stop()
        multiverse_test_call_api.stop()

    def reset_world(self, spawn_client, simulation_name="empty_simulation"):
        self.reset_spawn_request_meta_data(spawn_client)
        spawn_client.request_meta_data["meta_data"]["simulation_name"] = simulation_name
        spawn_client.send_data = [0.0]
        spawn_client.send_and_receive_data()
        # self.assertEqual(spawn_client.receive_data, [0.0])

    def remove_object(self, spawn_client, object_name, simulation_name="empty_simulation"):
        self.reset_spawn_request_meta_data(spawn_client)
        spawn_client.request_meta_data["meta_data"]["simulation_name"] = simulation_name
        spawn_client.request_meta_data["send"][object_name] = []
        spawn_client.request_meta_data["receive"][object_name] = []
        spawn_client.send_and_receive_meta_data()
        spawn_client.send_data = [spawn_client.sim_time]
        spawn_client.send_and_receive_data()

    def simulate(self, multiverse_test_call_api, simulation_name, simulation_time: datetime.timedelta):
        self.unpause_simulation(multiverse_test_call_api, simulation_name)
        sleep(simulation_time.total_seconds())
        self.pause_simulation(multiverse_test_call_api, simulation_name)

    def get_contact_points_and_contact_effort(self, api_callback_client, object_name, simulation_name):
        api_callback_client.request_meta_data["send"] = {}
        api_callback_client.request_meta_data["receive"] = {}
        api_callback_client.request_meta_data["api_callbacks"] = {
            simulation_name: [
                {"get_contact_bodies": [object_name]},
                {"get_constraint_effort": [object_name]}
            ]
        }
        api_callback_client.send_and_receive_meta_data()
        self.assertIn("api_callbacks_response", api_callback_client.response_meta_data)
        response = api_callback_client.response_meta_data["api_callbacks_response"]
        self.assertIn(simulation_name, response)
        self.assertIn("get_contact_bodies", response[simulation_name][0])
        self.assertIn("get_constraint_effort", response[simulation_name][1])
        return (response[simulation_name][0]["get_contact_bodies"],
                response[simulation_name][1]["get_constraint_effort"])

    def attach(self, api_callback_client, object_1, object_2, translation=None, rotation=None,
               simulation_name="empty_simulation"):
        api_callback_client.request_meta_data["send"] = {}
        api_callback_client.request_meta_data["receive"] = {}
        if translation is not None and rotation is not None:
            api_callback_client.request_meta_data["api_callbacks"] = {
                simulation_name: [
                    {"attach": [object_1, object_2, " ".join(map(str, translation + rotation))]}
                ]
            }
        else:
            api_callback_client.request_meta_data["api_callbacks"] = {
                simulation_name: [
                    {"attach": [object_1, object_2]}
                ]
            }
        api_callback_client.send_and_receive_meta_data()

    def detach(self, api_callback_client, object_1, object_2, simulation_name="empty_simulation"):
        api_callback_client.request_meta_data["send"] = {}
        api_callback_client.request_meta_data["receive"] = {}
        api_callback_client.request_meta_data["api_callbacks"] = {
            simulation_name: [
                {"detach": [object_1, object_2]}
            ]
        }
        api_callback_client.send_and_receive_meta_data()

    def test_multiverse_move_mobile_robot_in_two_unrelated_worlds(self):
        # create world_1 clients
        multiverse_client_test_receive_1 = self.create_multiverse_client_receive("1337", "", [""],
                                                                                 "world_1", "receiver_1")
        multiverse_client_test_spawn_1 = self.create_multiverse_client_spawn("1338", "world_1", "writer_1")

        multiverse_test_call_api_1 = self.create_multiverse_client_callapi("1339", "world_1", {},
                                                                           "sim_test_callapi_1")

        # create world_2 clients
        multiverse_client_test_receive_2 = self.create_multiverse_client_receive("1340", "", [""],
                                                                                 "world_2", "receiver_2")
        multiverse_client_test_spawn_2 = self.create_multiverse_client_spawn("1341", "world_2", "writer_2")

        multiverse_test_call_api_2 = self.create_multiverse_client_callapi("1342", "world_2", {},
                                                                           "sim_test_callapi_2")

        # pause simulation in world_1
        self.pause_simulation(multiverse_test_call_api_1, "empty_simulation_1")

        # pause simulation in world_2
        self.pause_simulation(multiverse_test_call_api_2, "empty_simulation_2")

        # Spawn robot in world1
        self.send_body_data(multiverse_client_test_spawn_1, "tiago_dual", {"position": [0.0, 0.0, 0.0],
                                                                           "quaternion": [1.0, 0.0, 0.0, 0.0],
                                                                           "relative_velocity": [0.0] * 6},
                            "empty_simulation_1")

        latest_position_1 = 0.0

        # Spawn robot in world2
        self.send_body_data(multiverse_client_test_spawn_2, "tiago_dual", {"position": [1.0, 0.0, 0.0],
                                                                           "quaternion": [1.0, 0.0, 0.0, 0.0],
                                                                           "relative_velocity": [0.0] * 6},
                            "empty_simulation_2")

        latest_position_2 = 1.0

        step_x = 0.4
        for i in range(10):
            curr_value = step_x * (i + 1)
            # Move robot in world1
            self.send_body_data(multiverse_client_test_spawn_1, "odom_vel_lin_x_joint", {"joint_tvalue": [curr_value]},
                                "empty_simulation_1")

            latest_position_1 += step_x
            print("new position 1 should be: ", [latest_position_1, 0.0, 0.0])

            # Assert robot position in world1
            self.assert_receive_body_data(multiverse_client_test_receive_1, "tiago_dual",
                                          {"position": [latest_position_1, 0.0, 0.0]})

            # Move robot in world2
            self.send_body_data(multiverse_client_test_spawn_2, "odom_vel_lin_x_joint", {"joint_tvalue": [curr_value]},
                                "empty_simulation_2")

            latest_position_2 += step_x
            print("new position 2 should be: ", [latest_position_2, 0.0, 0.0])

            # Asser robot position in world2
            self.assert_receive_body_data(multiverse_client_test_receive_2, "tiago_dual",
                                          {"position": [latest_position_2, 0.0, 0.0]})

        # stop all clients
        multiverse_client_test_receive_1.stop()
        multiverse_client_test_spawn_1.stop()
        multiverse_test_call_api_1.stop()
        multiverse_client_test_receive_2.stop()
        multiverse_client_test_spawn_2.stop()
        multiverse_test_call_api_2.stop()

    def pause_simulation(self, multiverse_client_test_callapi, simulation_name):
        multiverse_client_test_callapi.request_meta_data["send"] = {}
        multiverse_client_test_callapi.request_meta_data["receive"] = {}
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            simulation_name: [{"pause": []}]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()
        self.assertEqual(multiverse_client_test_callapi.response_meta_data["api_callbacks_response"][simulation_name],
                         [{"pause": ["paused"]}])

    def unpause_simulation(self, multiverse_client_test_callapi, simulation_name):
        multiverse_client_test_callapi.request_meta_data["send"] = {}
        multiverse_client_test_callapi.request_meta_data["receive"] = {}
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            simulation_name: [{"unpause": []}]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()
        self.assertEqual(multiverse_client_test_callapi.response_meta_data["api_callbacks_response"][simulation_name],
                         [{"unpause": ["unpaused"]}])

    def send_body_data(self, multiverse_client, object_name, body_data, simulation_name):
        multiverse_client.request_meta_data["meta_data"]["simulation_name"] = simulation_name
        multiverse_client.request_meta_data["send"] = {}
        multiverse_client.request_meta_data["send"][object_name] = list(body_data.keys())
        multiverse_client.send_and_receive_meta_data()
        flattened_body_data = [item for sublist in body_data.values() for item in sublist]
        time_now = time() - self.time_start
        multiverse_client.send_data = [time_now, *flattened_body_data]
        multiverse_client.send_and_receive_data()

    def assert_receive_body_data(self, multiverse_client_test_receive, object_name, expected_data):
        multiverse_client_test_receive.request_meta_data["receive"][""] = [""]
        multiverse_client_test_receive.send_and_receive_meta_data()
        self.assertIn("receive", multiverse_client_test_receive.response_meta_data)
        self.assertIn(object_name, multiverse_client_test_receive.response_meta_data["receive"])
        body_data = multiverse_client_test_receive.response_meta_data["receive"][object_name]
        for att_name in expected_data.keys():
            self.assertIn(att_name, body_data)
            print(f"{object_name}[{att_name}]: ", body_data[att_name])
            for v1, v2 in zip(body_data[att_name], expected_data[att_name]):
                self.assertAlmostEqual(v1, v2, 1)

    # @unittest.skip("Only occasionally")
    def test_multiverse_client_callapi_pause(self):
        # Test pause for 2s
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"pause": []},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'pause': ['paused']},
                                                          {'is_mujoco': ['yes']},
                                                          {'something_else': ['not implemented']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})
        multiverse_client_test_callapi.stop()

        sleep(2)

        # Test unpause
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"unpause": []},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'unpause': ['unpaused']},
                                                          {'is_mujoco': ['yes']},
                                                          {'something_else': ['not implemented']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})
        multiverse_client_test_callapi.stop()

    def create_multiverse_client_spawn_and_callapi(self, port, world_name, api_callbacks):
        meta_data = self.meta_data
        meta_data.world_name = world_name
        meta_data.simulation_name = "sim_test_spawn_and_callapi"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.request_meta_data["api_callbacks"] = api_callbacks
        return multiverse_client

    def create_multiverse_client_destroy(self, port, world_name):
        meta_data = self.meta_data
        meta_data.world_name = world_name
        meta_data.simulation_name = "sim_test_destroy"
        multiverse_client = MultiverseClientTest(client_addr=SocketAddress(port=port),
                                                 multiverse_meta_data=meta_data)
        multiverse_client.run()
        return multiverse_client

    def test_multiverse_client_spawn_creation(self):
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1337", "world")
        self.assertIn("time", multiverse_client_test_spawn.response_meta_data)
        time_spawn = multiverse_client_test_spawn.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_spawn.response_meta_data, {
            'meta_data': {'angle_unit': 'rad', 'handedness': 'rhs', 'length_unit': 'm', 'mass_unit': 'kg',
                          'simulation_name': 'sim_test_spawn', 'time_unit': 's', 'world_name': 'world'},
            'time': time_spawn})

        multiverse_client_test_spawn.stop()

    def test_multiverse_client_spawn(self):
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1337", "world")

        multiverse_client_test_spawn.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_spawn.request_meta_data["send"]["milk_box"] = ["position",
                                                                              "quaternion"]
        multiverse_client_test_spawn.request_meta_data["send"]["panda"] = ["position",
                                                                           "quaternion"]
        multiverse_client_test_spawn.send_and_receive_meta_data()

        multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time,
                                                  0, 0, 5,
                                                  0.0, 0.0, 0.0, 1.0,
                                                  0, 0, 3,
                                                  0.0, 0.0, 0.0, 1.0]
        multiverse_client_test_spawn.send_and_receive_data()

        multiverse_client_test_receive = self.create_multiverse_client_receive("1338",
                                                                               "",
                                                                               [""])
        self.assertIn("receive", multiverse_client_test_receive.response_meta_data)
        self.assertIn("milk_box", multiverse_client_test_receive.response_meta_data["receive"])
        self.assertIn("position", multiverse_client_test_receive.response_meta_data["receive"]["milk_box"])
        milk_box_pos = multiverse_client_test_receive.response_meta_data["receive"]["milk_box"]["position"]
        self.assertAlmostEqual(milk_box_pos[0], 0.0, 0)
        self.assertAlmostEqual(milk_box_pos[1], 0.0, 0)
        self.assertAlmostEqual(milk_box_pos[2], 5.0, 0)

        # self.assertIn("joint5", multiverse_client_test_receive.response_meta_data["receive"])
        # self.assertIn("joint_rvalue", multiverse_client_test_receive.response_meta_data["receive"]["joint5"])
        # joint5_value = multiverse_client_test_receive.response_meta_data["receive"]["joint5"]["joint_rvalue"][0]
        # self.assertAlmostEqual(joint5_value, 0.0, 1)

        multiverse_client_test_spawn.stop()

    def test_multiverse_client_callapi_save_load(self):
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1337", "world")
        multiverse_client_test_spawn.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_spawn.request_meta_data["send"]["milk_box"] = ["position",
                                                                              "quaternion"]
        multiverse_client_test_spawn.request_meta_data["send"]["panda"] = ["position",
                                                                           "quaternion"]
        multiverse_client_test_spawn.send_and_receive_meta_data()

        multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time,
                                                  0, 0, 5,
                                                  0.0, 0.0, 0.0, 1.0,
                                                  0, 0, 3,
                                                  0.0, 0.0, 0.0, 1.0]
        multiverse_client_test_spawn.send_and_receive_data()

        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"save": ["save_0"]},
                                                                                   ]
                                                                               })
        save_response = multiverse_client_test_callapi.response_meta_data["api_callbacks_response"]["empty_simulation"]
        save_path_0 = save_response[0]["save"][0]
        self.assertTrue(os.path.exists(save_path_0))

        multiverse_client_test_destroy = self.create_multiverse_client_destroy("1275", "world")
        multiverse_client_test_destroy.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_destroy.request_meta_data["send"]["panda"] = []
        multiverse_client_test_destroy.request_meta_data["receive"]["panda"] = []
        multiverse_client_test_destroy.send_and_receive_meta_data()
        multiverse_client_test_destroy.send_data = [multiverse_client_test_spawn.sim_time]
        multiverse_client_test_destroy.send_and_receive_data()

        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"save": ["save_1/awesome.xml"]},
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()
        save_response = multiverse_client_test_callapi.response_meta_data["api_callbacks_response"]["empty_simulation"]
        save_path_1 = save_response[0]["save"][0]
        self.assertTrue(os.path.exists(save_path_1))

        multiverse_client_test_destroy.request_meta_data["send"]["milk_box"] = []
        multiverse_client_test_destroy.request_meta_data["receive"]["milk_box"] = []
        multiverse_client_test_destroy.send_and_receive_meta_data()
        multiverse_client_test_destroy.send_data = [multiverse_client_test_spawn.sim_time]
        multiverse_client_test_destroy.send_and_receive_data()

        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"save": ["save_2/another_awesome.xml"]},
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()
        save_response = multiverse_client_test_callapi.response_meta_data["api_callbacks_response"]["empty_simulation"]
        save_path_2 = save_response[0]["save"][0]
        self.assertTrue(os.path.exists(save_path_2))

        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"load": [save_path_0]},
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        for _ in range(5):
            # Load save_path_0
            sleep(0.1)
            multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
                "empty_simulation": [
                    {"load": [save_path_0]},
                ]
            }
            multiverse_client_test_callapi.send_and_receive_meta_data()

            # Load save_path_1
            sleep(0.1)
            multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
                "empty_simulation": [
                    {"load": [save_path_1]},
                ]
            }
            multiverse_client_test_callapi.send_and_receive_meta_data()

            # Load save_path_2
            sleep(0.1)
            multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
                "empty_simulation": [
                    {"load": [save_path_2]},
                ]
            }
            multiverse_client_test_callapi.send_and_receive_meta_data()

        multiverse_client_test_callapi.stop()

    def test_multiverse_client_spawn_with_controller(self):
        # 1) Send controller data
        meta_data = self.meta_data
        meta_data.simulation_name = "send_controller"
        multiverse_client_send = MultiverseClientTest(client_addr=SocketAddress(port="4871"),
                                                      multiverse_meta_data=self.meta_data)
        multiverse_client_send.run()
        multiverse_client_send.request_meta_data["send"]["torso_lift_actuator"] = ["cmd_joint_tvalue"]
        multiverse_client_send.request_meta_data["send"]["head_1_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["head_2_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_1_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_2_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_3_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_4_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_5_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_6_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_left_7_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_1_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_2_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_3_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_4_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_5_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_6_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.request_meta_data["send"]["arm_right_7_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_send.send_and_receive_meta_data()
        multiverse_client_send.send_data = [multiverse_client_send.sim_time] + [0.0] * 17
        multiverse_client_send.send_and_receive_data()

        # 2) Spawn the robot

        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1337", "world")

        multiverse_client_test_spawn.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_spawn.request_meta_data["send"]["tiago_dual"] = ["position", "quaternion"]
        multiverse_client_test_spawn.request_meta_data["receive"]["torso_lift_actuator"] = ["cmd_joint_tvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["head_1_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["head_2_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_1_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_2_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_3_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_4_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_5_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_6_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_left_7_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_1_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_2_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_3_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_4_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_5_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_6_actuator"] = ["cmd_joint_rvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"]["arm_right_7_actuator"] = ["cmd_joint_rvalue"]

        multiverse_client_test_spawn.send_and_receive_meta_data()

        time_now = time() - self.time_start
        multiverse_client_test_spawn.send_data = [time_now,
                                                  0, 2, 0,
                                                  1.0, 0.0, 0.0, 0.0]
        multiverse_client_test_spawn.send_and_receive_data()

        # 3) Move the robot
        multiverse_client_test_spawn.request_meta_data["send"] = {}
        multiverse_client_test_spawn.request_meta_data["send"]["torso_lift_joint"] = ["joint_tvalue"]
        multiverse_client_test_spawn.request_meta_data["receive"] = {}

        multiverse_client_test_spawn.send_and_receive_meta_data()

        multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time, 0.0]
        multiverse_client_test_spawn.send_and_receive_data()

        # 4) Change the controller
        multiverse_client_send.request_meta_data["send"] = {}
        multiverse_client_send.request_meta_data["send"]["torso_lift_actuator"] = ["cmd_joint_tvalue"]
        multiverse_client_send.request_meta_data["receive"] = {}
        multiverse_client_send.send_and_receive_meta_data()

        multiverse_client_send.send_data = [multiverse_client_send.sim_time, 0.0]
        multiverse_client_send.send_and_receive_data()

        # 5) Remove the robot
        sleep(2)

        multiverse_client_test_destroy = self.create_multiverse_client_destroy("1275", "world")

        multiverse_client_test_destroy.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_destroy.request_meta_data["send"]["tiago_dual"] = []
        multiverse_client_test_destroy.request_meta_data["receive"]["tiago_dual"] = []
        multiverse_client_test_destroy.send_and_receive_meta_data()

        multiverse_client_test_destroy.send_data = [multiverse_client_test_destroy.sim_time]
        multiverse_client_test_destroy.send_and_receive_data()

        multiverse_client_test_spawn.stop()
        multiverse_client_send.stop()
        multiverse_client_test_destroy.stop()

    def test_multiverse_client_spawns(self):
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1337", "world")
        multiverse_client_test_spawn.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"

        for i in range(50):
            # Destroy milk box
            multiverse_client_test_spawn.request_meta_data["send"] = {}
            multiverse_client_test_spawn.request_meta_data["receive"] = {}
            multiverse_client_test_spawn.request_meta_data["send"]["milk_box"] = []
            multiverse_client_test_spawn.request_meta_data["receive"]["milk_box"] = []
            multiverse_client_test_spawn.send_and_receive_meta_data()
            multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time]
            multiverse_client_test_spawn.send_and_receive_data()

            # Destroy panda
            multiverse_client_test_spawn.request_meta_data["send"] = {}
            multiverse_client_test_spawn.request_meta_data["receive"] = {}
            multiverse_client_test_spawn.request_meta_data["send"]["panda"] = []
            multiverse_client_test_spawn.request_meta_data["receive"]["panda"] = []
            multiverse_client_test_spawn.send_and_receive_meta_data()
            multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time]
            multiverse_client_test_spawn.send_and_receive_data()

            # Spawn milk box
            multiverse_client_test_spawn.request_meta_data["send"] = {}
            multiverse_client_test_spawn.request_meta_data["receive"] = {}
            multiverse_client_test_spawn.request_meta_data["send"]["milk_box"] = ["position",
                                                                                  "quaternion",
                                                                                  "relative_velocity"]
            multiverse_client_test_spawn.send_and_receive_meta_data()
            multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time,
                                                      0, 0, 5,
                                                      0.0, 0.0, 0.0, 1.0,
                                                      0.0, 0.0, i / 10, 0.0, 0.0, 0.0]
            multiverse_client_test_spawn.send_and_receive_data()

            # Spawn panda
            multiverse_client_test_spawn.request_meta_data["send"] = {}
            multiverse_client_test_spawn.request_meta_data["receive"] = {}
            multiverse_client_test_spawn.request_meta_data["send"]["panda"] = ["position",
                                                                               "quaternion"]
            multiverse_client_test_spawn.send_and_receive_meta_data()
            multiverse_client_test_spawn.send_data = [multiverse_client_test_spawn.sim_time,
                                                      0, 0, 3,
                                                      0.0, 0.0, 0.0, 1.0]
            multiverse_client_test_spawn.send_and_receive_data()

        multiverse_client_test_spawn.stop()

    def test_multiverse_client_callapi_weld(self):
        # Spawn panda and milk box
        self.test_multiverse_client_spawn()

        # Weld milk box to hand at (0 0 0) (1 0 0 0)
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"weld": [
                                                                                           "milk_box",
                                                                                           "hand"]},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'weld': ['success']},
                                                          {'is_mujoco': ['yes']},
                                                          {'something_else': ['not implemented']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        sleep(2)

        # Re-weld milk box to hand at (0 0 0.5) (1 0 0 0)
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"weld": ["milk_box", "hand", "0.0 0.0 0.5 1.0 0.0 0.0 0.0"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'weld': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        sleep(2)

        # Unweld milk box from hand
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"unweld": ["milk_box", "hand"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'unweld': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        sleep(2)

        # Unweld milk box from hand again (should success)
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"unweld": ["milk_box", "hand"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'unweld': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        sleep(2)

        # Weld milk box to hand at (0 0 -0.5) (1 0 0 0)
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"weld": ["milk_box", "hand", "0.0 0.0 -0.5 1.0 0.0 0.0 0.0"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'weld': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        sleep(2)

        # Unweld milk box from hand again (should success)
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"unweld": ["milk_box", "hand"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'unweld': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        sleep(2)

        multiverse_client_test_callapi.stop()

    def test_multiverse_client_callapi_attach(self):
        # Spawn panda and milk box
        self.test_multiverse_client_spawn()

        # Attach milk box to hand at relative pose
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"attach": [
                                                                                           "milk_box",
                                                                                           "hand"]},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'attach': ['success']},
                                                          {'is_mujoco': ['yes']},
                                                          {'something_else': ['not implemented']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        # Re-attach milk box to hand at (0 0 0.5) (1 0 0 0)
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"attach": ["milk_box", "hand", "0.0 0.0 0.5 1.0 0.0 0.0 0.0"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'attach': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        # Detach milk box from hand
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"detach": ["milk_box", "hand"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'detach': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        # Detach milk box from hand again (should success)
        multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
            "empty_simulation": [
                {"detach": ["milk_box", "hand"]}
            ]
        }
        multiverse_client_test_callapi.send_and_receive_meta_data()

        time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
        self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                             {'api_callbacks_response':
                                 {
                                     'empty_simulation': [{'detach': ['success']}]},
                                 'meta_data': {'angle_unit': 'rad',
                                               'handedness': 'rhs',
                                               'length_unit': 'm',
                                               'mass_unit': 'kg',
                                               'simulation_name': 'sim_test_callapi',
                                               'time_unit': 's',
                                               'world_name': 'world'},
                                 'time': time_callapi})

        multiverse_client_test_callapi.stop()

    def test_multiverse_client_move(self):
        multiverse_client_test_move = self.create_multiverse_client_spawn("1337", "world")

        # Spawn the cup
        multiverse_client_test_move.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_move.request_meta_data["send"]["cup"] = ["position",
                                                                        "quaternion",
                                                                        "relative_velocity"]
        multiverse_client_test_move.send_and_receive_meta_data()
        time_now = time() - self.time_start
        multiverse_client_test_move.send_data = [time_now,
                                                 0, 0, 1,
                                                 1.0, 0.0, 0.0, 0.0,
                                                 0.0, 0.0, 0, 0.0, 0.0, 0.0]
        multiverse_client_test_move.send_and_receive_data()

        # reset request_meta_data
        multiverse_client_test_move.request_meta_data["send"] = {}
        multiverse_client_test_move.request_meta_data["receive"] = {}

        for h in range(10):
            x_pos = [0.0, 1.0, 1.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0]
            y_pos = [1.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 1.0, 1.0]
            for i in range(9):
                # spawn/move the milk box
                multiverse_client_test_move.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
                multiverse_client_test_move.request_meta_data["send"]["milk_box"] = ["position",
                                                                                     "quaternion",
                                                                                     "relative_velocity"]
                multiverse_client_test_move.send_and_receive_meta_data()
                time_now = time() - self.time_start
                multiverse_client_test_move.send_data = [time_now,
                                                         x_pos[i], y_pos[i], h,
                                                         0.0, 0.0, 0.0, 1.0,
                                                         0.0, 0.0, h - i, 0.0, 0.0, 0.0]
                multiverse_client_test_move.send_and_receive_data()

                if h == 0 and i == 0:
                    # Receive the data of the milk box
                    multiverse_client_test_receive = self.create_multiverse_client_receive("1338",
                                                                                           "milk_box",
                                                                                           ["position",
                                                                                            "quaternion",
                                                                                            "relative_velocity"])
                    multiverse_client_test_receive.send_and_receive_meta_data()

                    # Attach the cup and milk box

                    multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                                           {
                                                                                               "empty_simulation": [
                                                                                                   {"attach": [
                                                                                                       "cup",
                                                                                                       "milk_box"]},
                                                                                               ]
                                                                                           })
                    multiverse_client_test_callapi.send_and_receive_meta_data()

                    time_callapi = multiverse_client_test_callapi.response_meta_data["time"]
                    self.assertDictEqual(multiverse_client_test_callapi.response_meta_data,
                                         {'api_callbacks_response':
                                             {
                                                 'empty_simulation': [{'attach': ['success']}]},
                                             'meta_data': {'angle_unit': 'rad',
                                                           'handedness': 'rhs',
                                                           'length_unit': 'm',
                                                           'mass_unit': 'kg',
                                                           'simulation_name': 'sim_test_callapi',
                                                           'time_unit': 's',
                                                           'world_name': 'world'},
                                             'time': time_callapi})

                time_now = time() - self.time_start
                multiverse_client_test_receive.send_data = [time_now]
                multiverse_client_test_receive.send_and_receive_data()
                # expected_result = [time_now,
                #                    x_pos[i], y_pos[i], h,
                #                    0.0, 0.0, 0.0, 1.0,
                #                    0.0, 0.0, h - i, 0.0, 0.0, 0.0]
                # for k in range(len(expected_result)):
                #     self.assertEqual(multiverse_client_test_receive.receive_data[k], expected_result[k])

                sleep(0.1)

        multiverse_client_test_move.stop()

    def test_multiverse_client_callapi_get_contact(self):
        # Spawn panda and milk box
        self.test_multiverse_client_spawn()

        sleep(1)

        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"get_contact_bodies": [
                                                                                           "milk_box"]},
                                                                                       {"get_contact_bodies": [
                                                                                           "link1"]},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        print(multiverse_client_test_callapi.response_meta_data)

    def test_multiverse_client_callapi_get_constraint_effort(self):
        # Spawn panda and milk box
        self.test_multiverse_client_spawn()

        sleep(1)

        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"get_contact_bodies": [
                                                                                           "milk_box"]},
                                                                                       {"get_constraint_effort": [
                                                                                           "milk_box"]},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        print(multiverse_client_test_callapi.response_meta_data)

        sleep(5)  # Wait for the milk box to fall and stabilize

        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"get_contact_bodies": [
                                                                                           "milk_box"]},
                                                                                       {"get_constraint_effort": [
                                                                                           "milk_box"]},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        print(multiverse_client_test_callapi.response_meta_data)

    def test_multiverse_client_callapi_get_rays(self):
        # Spawn panda and milk box
        self.test_multiverse_client_spawn()

        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "empty_simulation": [
                                                                                       {"get_rays": ["1 0 3", "0 0 3"]},
                                                                                       {"get_rays": [
                                                                                           "0 0 1 0 0 1 0 0 2",
                                                                                           "0 0 3 0 0 -1 0 0 2.5"]},
                                                                                       {"is_mujoco": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        print(multiverse_client_test_callapi.response_meta_data)

    def test_multiverse_client_destroy(self):
        multiverse_client_test_destroy = self.create_multiverse_client_destroy("1275", "world")

        multiverse_client_test_destroy.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_destroy.request_meta_data["send"]["milk_box"] = []
        multiverse_client_test_destroy.request_meta_data["receive"]["milk_box"] = []
        multiverse_client_test_destroy.send_and_receive_meta_data()

        multiverse_client_test_destroy.send_data = [multiverse_client_test_destroy.sim_time]
        multiverse_client_test_destroy.send_and_receive_data()

        multiverse_client_test_destroy.stop()

    def test_multiverse_client_spawn_and_destroy(self):
        multiverse_client_test_spawn = self.create_multiverse_client_spawn("1337", "world")
        multiverse_client_test_spawn.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_spawn.request_meta_data["send"]["bread_1"] = ["position", "quaternion"]
        multiverse_client_test_spawn.send_and_receive_meta_data()

        time_now = time() - self.time_start
        multiverse_client_test_spawn.send_data = [time_now,
                                                  0.0, 0.0, 3.0,
                                                  0.0, 0.0, 0.0, 1.0]
        multiverse_client_test_spawn.send_and_receive_data()
        multiverse_client_test_spawn.stop()

        sleep(2)

        multiverse_client_test_destroy = self.create_multiverse_client_destroy("1338", "world")

        multiverse_client_test_destroy.request_meta_data["meta_data"]["simulation_name"] = "empty_simulation"
        multiverse_client_test_destroy.request_meta_data["send"]["bread_1"] = []
        multiverse_client_test_destroy.request_meta_data["send"]["panda"] = []
        multiverse_client_test_destroy.request_meta_data["receive"]["bread_1"] = []
        multiverse_client_test_destroy.request_meta_data["receive"]["panda"] = []
        multiverse_client_test_destroy.send_and_receive_meta_data()

        time_now = time() - self.time_start
        multiverse_client_test_destroy.send_data = [time_now]
        multiverse_client_test_destroy.send_and_receive_data()

        multiverse_client_test_destroy.stop()


class MultiverseClientUnrealTestCase(MultiverseClientComplexTestCase):
    def test_multiverse_client_callapi_unreal(self):
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "unreal": [
                                                                                       {"is_unreal": []},
                                                                                       {"something_else": ["param1",
                                                                                                           "param2"]}
                                                                                   ]
                                                                               })
        print(multiverse_client_test_callapi.response_meta_data)


class MultiverseClientCallapiPythonTestCase(MultiverseClientComplexTestCase):
    def test_multiverse_client_listenapi(self):
        multiverse_client_test_listenapi = self.create_multiverse_client_listenapi("1358", "world")
        for _ in range(10):
            multiverse_client_test_listenapi.send_data = [time() - self.time_start]
            multiverse_client_test_listenapi.send_and_receive_data()
            sleep(0.5)

    def test_multiverse_client_callapi(self):
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1339", "world",
                                                                               {
                                                                                   "sim_test_listenapi": [
                                                                                       {"func_1": ["param1",
                                                                                                   "param2"]},
                                                                                       {"func_2": ["param3",
                                                                                                   "param4",
                                                                                                   "param5"]}
                                                                                   ]
                                                                               })
        print(multiverse_client_test_callapi.response_meta_data)

    def test_multiverse_client_callapi_preparing_soup(self):
        multiverse_client_test_callapi = self.create_multiverse_client_callapi("1587",
                                                                               "world",
                                                                               {
                                                                                   "preparing_soup":
                                                                                       [
                                                                                           {
                                                                                               "get_contact_islands":
                                                                                                   [
                                                                                                       "cooking_pot_body"
                                                                                                   ]
                                                                                           }
                                                                                       ]
                                                                               })

        # print(multiverse_client_test_callapi.response_meta_data["api_callbacks_response"]["preparing_soup"][0])
        sleep(1)
        for i in range(10):
            time_start = time()
            multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
                "preparing_soup": [
                    {"get_contact_bodies": ["cooking_pot_body", "with_children"]}
                ]
            }
            multiverse_client_test_callapi.send_and_receive_meta_data()
            print(multiverse_client_test_callapi.response_meta_data)
            print(f"{2 * i + 1} takes {time() - time_start}s")
            time_start = time()
            multiverse_client_test_callapi.request_meta_data["api_callbacks"] = {
                "preparing_soup": [
                    {"get_contact_islands": ["cooking_pot_body", "with_children"]}
                ]
            }
            multiverse_client_test_callapi.send_and_receive_meta_data()
            print(multiverse_client_test_callapi.response_meta_data)
            print(f"{2 * i + 2} takes {time() - time_start}s")

    def test_multiverse_client_call_and_listen_api(self):
        listen_thread = threading.Thread(target=self.test_multiverse_client_listenapi)
        listen_thread.start()
        sleep(2)
        call_thread = threading.Thread(target=self.test_multiverse_client_callapi)
        call_thread.start()
        listen_thread.join()
        call_thread.join()


if __name__ == "__main__":
    unittest.main()
