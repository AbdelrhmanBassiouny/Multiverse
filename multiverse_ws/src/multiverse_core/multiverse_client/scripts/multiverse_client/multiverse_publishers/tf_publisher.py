#!/usr/bin/env python3

import rospy
from typing import List
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from .ros_publisher import MultiverseRosPublisher
import numpy

class tf_publisher(MultiverseRosPublisher):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__tf_broadcaster = TransformBroadcaster()
        self.__refresh_time = rospy.Time.now()
        self.__tf_msgs = []

    def _init_request_meta_data(self) -> None:
        super()._init_request_meta_data()
        self._request_meta_data_dict["receive"][""] = ["position", "quaternion"]

    def _construct_rosmsg(self, response_meta_data_dict: dict) -> None:
        self.object_names = []
        if response_meta_data_dict.get("receive") is None:
            return
        self.object_names = response_meta_data_dict["receive"].keys()
        root_frame_id = rospy.get_param("multiverse/root_frame_id") if rospy.has_param("multiverse/root_frame_id") else "map"

        self.__tf_msgs = []
        for object_name in self.object_names:
            tf_msg = TransformStamped()
            tf_msg.header.frame_id = root_frame_id
            tf_msg.child_frame_id = object_name
            self.__tf_msgs.append(tf_msg)

    def _bind_rosmsg(self, receive_data: List[float]) -> None:
        for i, _ in enumerate(self.object_names):
            self.__tf_msgs[i].header.stamp = rospy.Time.now()
            self.__tf_msgs[i].header.seq += 1
            self.__tf_msgs[i].transform.translation.x = receive_data[7 * i + 1]
            self.__tf_msgs[i].transform.translation.y = receive_data[7 * i + 2]
            self.__tf_msgs[i].transform.translation.z = receive_data[7 * i + 3]
            quat = numpy.array([receive_data[7 * i + 4], receive_data[7 * i + 5], receive_data[7 * i + 6], receive_data[7 * i + 7]])
            quat = quat / numpy.linalg.norm(quat)
            self.__tf_msgs[i].transform.rotation.w = quat[0]
            self.__tf_msgs[i].transform.rotation.x = quat[1]
            self.__tf_msgs[i].transform.rotation.y = quat[2]
            self.__tf_msgs[i].transform.rotation.z = quat[3]

    def _publish(self) -> None:
        self.__tf_broadcaster.sendTransform(self.__tf_msgs)
        # if rospy.Time.now().to_sec() - self.__refresh_time.to_sec() > 1:
        #     self._communicate(True)
        #     response_meta_data_dict = self._get_response_meta_data()
        #     self._construct_rosmsg(response_meta_data_dict)
        #     self.__refresh_time = rospy.Time.now()