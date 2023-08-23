#!/usr/bin/env python3.10

import mujoco
import numpy
from math import degrees
from multiverse_parser import WorldBuilder, GeomType, JointType
from multiverse_parser.utils import clear_meshes, modify_name


class MjcfImporter:
    def __init__(self, mjcf_file_path: str, with_physics: bool, with_visual: bool, with_collision: bool) -> None:
        try:
            self.mj_model = mujoco.MjModel.from_xml_path(mjcf_file_path)
        except ValueError as error:
            print(f"{error}. Failed to import MJCF.")
            self.world_builder = None
            return

        self.with_physics = with_physics
        self.with_visual = with_visual
        self.with_collision = with_collision
        self.world_builder = WorldBuilder()
        self.mesh_names = set()
        self.build_everyting()

    def build_everyting(self) -> None:
        for body_id in range(self.mj_model.nbody):
            mj_body = self.mj_model.body(body_id)
            body_name = modify_name(in_name=mj_body.name, replacement="Body_" + str(body_id))

            if body_id == 0:
                root_body_name = body_name
                body_builder = self.world_builder.add_body(body_name=root_body_name)
            else:
                mj_body_parent = self.mj_model.body(mj_body.parentid)
                parent_body_name = modify_name(in_name=mj_body_parent.name, replacement="Body_" + str(mj_body.parentid))
                if mj_body.jntnum[0] > 0 and self.with_physics:
                    body_builder = self.world_builder.add_body(body_name=body_name, parent_body_name=root_body_name)
                    body_builder.enable_rigid_body()
                else:
                    body_builder = self.world_builder.add_body(body_name=body_name, parent_body_name=parent_body_name)
                body_builder.set_transform(
                    pos=tuple(mj_body.pos),
                    quat=tuple(mj_body.quat),
                    relative_to=parent_body_name,
                )

            for geom_id in range(mj_body.geomadr[0], mj_body.geomadr[0] + mj_body.geomnum[0]):
                mj_geom = self.mj_model.geom(geom_id)
                is_visual = (mj_geom.contype == 0) and (mj_geom.conaffinity == 0)
                if is_visual and self.with_visual:
                    pass  # TODO: Implement

                if not is_visual and self.with_collision:
                    geom_name = modify_name(in_name=mj_geom.name, replacement="Geom_" + str(geom_id))

                    if mj_geom.type == mujoco.mjtGeom.mjGEOM_PLANE:
                        geom_builder = body_builder.add_geom(geom_name=geom_name, geom_type=GeomType.PLANE, is_visual=is_visual)
                        geom_builder.set_transform(pos=tuple(mj_geom.pos), quat=tuple(mj_geom.quat), scale=(50, 50, 1))
                    elif mj_geom.type == mujoco.mjtGeom.mjGEOM_BOX:
                        geom_builder = body_builder.add_geom(geom_name=geom_name, geom_type=GeomType.CUBE, is_visual=is_visual)
                        geom_builder.set_transform(
                            pos=tuple(mj_geom.pos),
                            quat=tuple(mj_geom.quat),
                            scale=tuple(mj_geom.size),
                        )
                    elif mj_geom.type == mujoco.mjtGeom.mjGEOM_SPHERE:
                        geom_builder = body_builder.add_geom(geom_name=geom_name, geom_type=GeomType.SPHERE, is_visual=is_visual)
                    elif mj_geom.type == mujoco.mjtGeom.mjGEOM_CYLINDER:
                        geom_builder = body_builder.add_geom(geom_name=geom_name, geom_type=GeomType.CYLINDER, is_visual=is_visual)
                    elif mj_geom.type == mujoco.mjtGeom.mjGEOM_MESH:
                        geom_builder = body_builder.add_geom(geom_name=geom_name, geom_type=GeomType.MESH, is_visual=is_visual)
                    else:
                        print(f"Geom type {str(mj_geom.type)} not supported.")
                        continue

                    if mj_geom.type != mujoco.mjtGeom.mjGEOM_BOX and mj_geom.type != mujoco.mjtGeom.mjGEOM_PLANE:
                        geom_builder.set_transform(pos=tuple(mj_geom.pos), quat=tuple(mj_geom.quat))
                    if mj_geom.type == mujoco.mjtGeom.mjGEOM_SPHERE:
                        geom_builder.set_attribute(radius=mj_geom.size[0])
                    elif mj_geom.type == mujoco.mjtGeom.mjGEOM_CYLINDER:
                        geom_builder.set_attribute(radius=mj_geom.size[0], height=mj_geom.size[1] * 2)
                    elif mj_geom.type == mujoco.mjtGeom.mjGEOM_MESH:
                        mesh_id = mj_geom.dataid[0]
                        mesh_name = modify_name(in_name=self.mj_model.mesh(mesh_id).name, replacement="Mesh_" + str(mesh_id))

                        clear_meshes()

                        mesh_builder = geom_builder.add_mesh(mesh_name=mesh_name)

                        if mesh_name not in self.mesh_names:
                            self.mesh_names.add(mesh_name)

                            vert_adr = self.mj_model.mesh_vertadr[mesh_id]
                            vert_num = self.mj_model.mesh_vertnum[mesh_id]

                            face_adr = self.mj_model.mesh_faceadr[mesh_id]
                            face_num = self.mj_model.mesh_facenum[mesh_id]
                            points = numpy.empty(shape=[vert_num, 3], dtype=float)

                            normals = numpy.empty(shape=[self.mj_model.mesh_facenum[mesh_id], 3], dtype=float)

                            face_vertex_counts = numpy.empty(shape=self.mj_model.mesh_facenum[mesh_id], dtype=float)
                            face_vertex_counts.fill(3)

                            face_vertex_indices = numpy.empty(shape=self.mj_model.mesh_facenum[mesh_id] * 3, dtype=float)

                            for i in range(vert_num):
                                vert_id = vert_adr + i
                                points[i] = self.mj_model.mesh_vert[vert_id]

                            face_adr = self.mj_model.mesh_faceadr[mesh_id]
                            normal_adr = self.mj_model.mesh_normaladr[mesh_id]
                            for i in range(face_num):
                                face_id = face_adr + i
                                face_normals = self.mj_model.mesh_normal[normal_adr + self.mj_model.mesh_facenormal[face_id]]

                                p1 = face_normals[0]
                                p2 = face_normals[1]
                                p3 = face_normals[2]

                                v1 = p2 - p1
                                v2 = p3 - p1
                                normal = numpy.cross(v1, v2)
                                norm = numpy.linalg.norm(normal)
                                if norm != 0:
                                    normal = normal / norm
                                normals[i] = normal

                                face_vertex_indices[3 * i] = self.mj_model.mesh_face[face_id][0]
                                face_vertex_indices[3 * i + 1] = self.mj_model.mesh_face[face_id][1]
                                face_vertex_indices[3 * i + 2] = self.mj_model.mesh_face[face_id][2]

                            mesh_builder.build(points, normals, face_vertex_counts, face_vertex_indices)
                            mesh_builder.save()

                if self.with_physics:
                    geom_builder.enable_collision()

                geom_builder.set_attribute(prefix="primvars", displayColor=mj_geom.rgba[:3])
                geom_builder.set_attribute(prefix="primvars", displayOpacity=mj_geom.rgba[3])

                geom_builder.compute_extent()

            if self.with_physics:
                body_builder.set_inertial(mass=mj_body.mass[0], com=tuple(mj_body.ipos), diagonal_inertia=tuple(mj_body.inertia))

                for i in range(mj_body.jntnum[0]):
                    if self.mj_model.joint(mj_body.jntadr[i]).type == mujoco.mjtJoint.mjJNT_FREE:
                        continue

                    joint_id = mj_body.jntadr[i]
                    mj_joint = self.mj_model.joint(joint_id)
                    joint_name = modify_name(in_name=mj_joint.name, replacement="Joint_" + str(joint_id))
                    if mj_joint.type == mujoco.mjtJoint.mjJNT_HINGE:
                        joint_type = JointType.REVOLUTE
                    elif mj_joint.type == mujoco.mjtJoint.mjJNT_SLIDE:
                        joint_type = JointType.PRISMATIC
                    elif mj_joint.type == mujoco.mjtJoint.mjJNT_BALL:
                        joint_type = JointType.SPHERICAL
                    else:
                        print(f"Joint {joint_name} type {str(mj_joint.type)} not supported.")
                        continue
                    joint_axis = "Z"
                    if numpy.array_equal(mj_joint.axis, [1, 0, 0]):
                        joint_axis = "X"
                    elif numpy.array_equal(mj_joint.axis, [0, 1, 0]):
                        joint_axis = "Y"
                    elif numpy.array_equal(mj_joint.axis, [0, 0, 1]):
                        joint_axis = "Z"
                    elif numpy.array_equal(mj_joint.axis, [-1, 0, 0]):
                        joint_axis = "-X"
                    elif numpy.array_equal(mj_joint.axis, [0, -1, 0]):
                        joint_axis = "-Y"
                    elif numpy.array_equal(mj_joint.axis, [0, 0, -1]):
                        joint_axis = "-Z"
                    else:
                        print(f"Joint {joint_name} axis {str(mj_joint.axis)} not supported.")
                        continue

                    joint_builder = body_builder.add_joint(
                        joint_name=joint_name,
                        parent_name=parent_body_name,
                        child_name=body_name,
                        joint_type=joint_type,
                        joint_pos=tuple(mj_joint.pos),
                        joint_axis=joint_axis,
                    )

                    if mj_joint.type == mujoco.mjtJoint.mjJNT_HINGE or mj_joint.type == mujoco.mjtJoint.mjJNT_SLIDE:
                        if mj_joint.type == mujoco.mjtJoint.mjJNT_HINGE:
                            joint_builder.set_limit(lower=degrees(mj_joint.range[0]), upper=degrees(mj_joint.range[1]))
                        else:
                            joint_builder.set_limit(lower=mj_joint.range[0], upper=mj_joint.range[1])