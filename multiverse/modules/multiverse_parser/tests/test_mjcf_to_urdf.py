import unittest

import os
import tracemalloc

import numpy

from multiverse_parser import MjcfImporter, InertiaSource, UrdfExporter

from pxr import Usd


class MjcfToUrdfTestCase(unittest.TestCase):
    resource_path: str

    @classmethod
    def setUpClass(cls):
        tracemalloc.start()
        cls.resource_path = os.path.join(os.path.dirname(__file__), "..", "resources")

    def test_mjcf_to_urdf(self):
        input_mjcf_path = os.path.join(self.resource_path, "input", "ur5e", "mjcf", "ur5e_1.xml")
        factory = MjcfImporter(file_path=input_mjcf_path,
                               with_physics=True,
                               with_visual=True,
                               with_collision=False)
        factory.config.default_rgba = numpy.array([1.0, 0.0, 0.0, 0.1])
        self.assertEqual(factory.source_file_path, input_mjcf_path)
        self.assertEqual(factory._config.model_name, "ur5e")

        usd_file_path = factory.import_model()
        self.assertTrue(os.path.exists(usd_file_path))

        stage = Usd.Stage.Open(usd_file_path)
        default_prim = stage.GetDefaultPrim()
        self.assertEqual(default_prim.GetName(), "ur5e")

        output_urdf_path = os.path.join(self.resource_path, "output", "test_mjcf_to_urdf", "ur5e.urdf")
        exporter = UrdfExporter(file_path=output_urdf_path,
                                factory=factory,
                                relative_to_ros_package=None)
        exporter.build()
        exporter.export()

    def test_mjcf_to_urdf_2(self):
        input_mjcf_path = os.path.join(self.resource_path, "input", "milk_box", "mjcf", "milk_box.xml")
        factory = MjcfImporter(file_path=input_mjcf_path,
                               with_physics=True,
                               with_visual=True,
                               with_collision=True)
        factory.config.default_rgba = numpy.array([1.0, 0.0, 0.0, 0.1])
        self.assertEqual(factory.source_file_path, input_mjcf_path)
        self.assertEqual(factory._config.model_name, "milk_box")

        usd_file_path = factory.import_model()
        self.assertTrue(os.path.exists(usd_file_path))

        stage = Usd.Stage.Open(usd_file_path)
        default_prim = stage.GetDefaultPrim()
        self.assertEqual(default_prim.GetName(), "milk_box")

        output_urdf_path = os.path.join(self.resource_path, "output", "test_mjcf_to_urdf", "milk_box.urdf")
        exporter = UrdfExporter(file_path=output_urdf_path,
                                factory=factory,
                                relative_to_ros_package=None)
        exporter.build()
        exporter.export()

    def test_mjcf_to_urdf_3(self):
        input_mjcf_path = "/media/giangnguyen/Storage/mujoco_menagerie/anybotics_anymal_b/anymal_b.xml"
        factory = MjcfImporter(file_path=input_mjcf_path,
                               with_physics=True,
                               with_visual=True,
                               with_collision=True)
        factory.config.default_rgba = numpy.array([1.0, 0.0, 0.0, 0.1])
        self.assertEqual(factory.source_file_path, input_mjcf_path)
        self.assertEqual(factory._config.model_name, "anymal_b")

        usd_file_path = factory.import_model()
        self.assertTrue(os.path.exists(usd_file_path))

        stage = Usd.Stage.Open(usd_file_path)
        default_prim = stage.GetDefaultPrim()
        self.assertEqual(default_prim.GetName(), "anymal_b")

        output_urdf_path = os.path.join(self.resource_path, "output", "test_mjcf_to_urdf", "anymal_b.urdf")
        exporter = UrdfExporter(file_path=output_urdf_path,
                                factory=factory,
                                relative_to_ros_package=None)
        exporter.build()
        exporter.export()

    @classmethod
    def tearDownClass(cls):
        tracemalloc.stop()


if __name__ == '__main__':
    unittest.main()