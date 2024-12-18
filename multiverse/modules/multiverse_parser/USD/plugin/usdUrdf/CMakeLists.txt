set(PXR_PACKAGE usdUrdf)

pxr_plugin(${PXR_PACKAGE}
    LIBRARIES
        usd
        tf

    INCLUDE_DIRS
        ${Boost_INCLUDE_DIRS}
        ${PYTHON_INCLUDE_DIRS}

    PUBLIC_HEADERS
        api.h

    PUBLIC_CLASSES
        urdf
        urdfRobot
        urdfMaterial
        urdfLinkAPI
        urdfLinkInertialAPI
        urdfLinkVisualAPI
        urdfLinkCollisionAPI
        urdfGeometryBoxAPI
        urdfGeometryCylinderAPI
        urdfGeometrySphereAPI
        urdfGeometryMeshAPI
        urdfJointAPI
        tokens

    PYTHON_CPPFILES
        moduleDeps.cpp    

    PYMODULE_FILES
        __init__.py

    PYMODULE_CPPFILES
        module.cpp
        wrapUrdf.cpp
        wrapUrdfRobot.cpp
        wrapUrdfMaterial.cpp
        wrapUrdfLinkAPI.cpp
        wrapUrdfLinkInertialAPI.cpp
        wrapUrdfLinkVisualAPI.cpp
        wrapUrdfLinkCollisionAPI.cpp
        wrapUrdfGeometryBoxAPI.cpp
        wrapUrdfGeometryCylinderAPI.cpp
        wrapUrdfGeometrySphereAPI.cpp
        wrapUrdfGeometryMeshAPI.cpp
        wrapUrdfJointAPI.cpp

    RESOURCE_FILES
        generatedSchema.usda
        plugInfo.json
        schema.usda:usdUrdf/schema.usda
)
