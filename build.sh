#!/usr/bin/env sh

if command -v git &>/dev/null; then
    # Update the submodules to make sure everything is there
    git submodule update --init
else
    echo "Git is not installed."
fi

SRC_DIR="$(dirname $0)/src"

# Specify the folder path to create
BUILD_DIR="$(dirname $0)/build"

# Build USD

# Check if the folder already exists
USD_BUILD_DIR="$BUILD_DIR/USD"
USD_SRC_DIR="$SRC_DIR/USD"
if [ ! -d "$USD_BUILD_DIR" ]; then
    # Create the folder if it doesn't exist
    mkdir -p "$USD_BUILD_DIR"
    echo "Folder created: $USD_BUILD_DIR"
else
    echo "Folder already exists: $USD_BUILD_DIR"
fi

(python3 $USD_SRC_DIR/build_scripts/build_usd.py $USD_BUILD_DIR)

# Build the workspace
rosdep init
(cd multiverse_ws; . /opt/ros/noetic/setup.sh; catkin build)
