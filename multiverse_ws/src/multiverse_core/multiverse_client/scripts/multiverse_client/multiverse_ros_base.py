#!/usr/bin/env python3

from multiverse_client.utils.multiverse_utils import init_request_meta_data_dict
import rospy
import sys
import os
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))
from multiverse_socket import MultiverseSocket  # noqa


class MultiverseRosBase:
    _request_meta_data_dict = {}
    _response_meta_data_dict = {}

    def __init__(self, **kwargs) -> None:
        self.host = kwargs.get('host', 'tcp://127.0.0.1')
        self.port = str(kwargs.get('port'))
        self.use_thread = True
        self._init_request_meta_data()

    def start(self) -> None:
        pass

    def _init_multiverse_socket(self):
        self.__multiverse_socket = MultiverseSocket(self.use_thread, 'tcp://127.0.0.1:7000')

    def _init_request_meta_data(self) -> None:
        self._request_meta_data_dict = init_request_meta_data_dict()

    def _connect(self) -> None:
        self.__multiverse_socket.connect(self.host, self.port)
        rospy.sleep(0.1) # Wait for multiverse_client to establish a connection with the server.

    def _disconnect(self) -> None:
        self.__multiverse_socket.disconnect()

    def _set_request_meta_data(self):
        self.__multiverse_socket.set_request_meta_data(self._request_meta_data_dict)

    def _get_response_meta_data(self, time_out=float('inf')) -> bool:
        start = rospy.Time.now()
        while not rospy.is_shutdown():
            self._response_meta_data_dict = self.__multiverse_socket.get_response_meta_data()
            if self._response_meta_data_dict:
                return True
            elif (rospy.Time.now() - start).to_sec() > time_out:
                rospy.logwarn(f"Could not receive meta data from the server for {self.__class__.__name__}.")
                return False
        return False

    def _set_send_data(self, send_data: List[float]) -> None:
        self.__multiverse_socket.set_send_data(send_data)

    def _communicate(self, resend_request_meta_data: bool=False) -> None:
        self.__multiverse_socket.communicate(resend_request_meta_data)

    def _get_receive_data(self) -> List[float]:
        return self.__multiverse_socket.get_receive_data()
    
    def _restart(self) -> None:
        self._disconnect()
        self._connect()
