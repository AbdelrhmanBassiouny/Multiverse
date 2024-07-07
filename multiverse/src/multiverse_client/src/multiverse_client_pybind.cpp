// Copyright (c) 2023, Giang Hoang Nguyen - Institute for Artificial Intelligence, University Bremen

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

#include "multiverse_client.h"

#include <pybind11/chrono.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

std::map<std::string, size_t> attribute_map = {
    {"", 0},
    {"position", 3},
    {"quaternion", 4},
    {"relative_velocity", 6},
    {"odometric_velocity", 6},
    {"joint_rvalue", 1},
    {"joint_tvalue", 1},
    {"joint_linear_velocity", 1},
    {"joint_angular_velocity", 1},
    {"joint_force", 1},
    {"joint_torque", 1},
    {"cmd_joint_rvalue", 1},
    {"cmd_joint_tvalue", 1},
    {"cmd_joint_linear_velocity", 1},
    {"cmd_joint_angular_velocity", 1},
    {"cmd_joint_force", 1},
    {"cmd_joint_torque", 1},
    {"joint_position", 3},
    {"joint_quaternion", 4},
    {"force", 3},
    {"torque", 3},
    {"rgb_1024_1024", 1024 * 1024 * 3}};

class MultiverseClientPybind final : public MultiverseClient
{
public:
    MultiverseClientPybind(const std::string &in_server_socket_addr = "tcp:127.0.0.1:7000")
    {
        server_socket_addr = in_server_socket_addr;
    }

    ~MultiverseClientPybind()
    {
    }

    inline void set_request_meta_data(const pybind11::dict &in_request_meta_data_dict)
    {
        request_meta_data_dict = in_request_meta_data_dict;
        compute_request_buffer_sizes(send_buffer_size, receive_buffer_size);
    }

    inline pybind11::dict get_response_meta_data()
    {
        return response_meta_data_dict;
    }

    inline void set_send_data(const pybind11::list &in_send_data)
    {
        if (in_send_data.size() != send_buffer_size)
        {
            printf("[Client %s] The size of in_send_data (%ld) does not match with send_buffer_size (%ld).\n", port.c_str(), in_send_data.size(), send_buffer_size);
        }
        else
        {
            send_data = in_send_data.cast<std::vector<double>>();
        }
    }

    inline pybind11::list get_receive_data() const
    {
        return pybind11::cast(receive_data);
    }

    inline void set_api_callbacks(const std::map<std::string, std::function<pybind11::list(pybind11::list)>> &in_api_callbacks)
    {
        api_callbacks = in_api_callbacks;
    }

private:
    pybind11::dict request_meta_data_dict;

    pybind11::dict response_meta_data_dict;

    std::vector<double> send_data;

    std::vector<double> receive_data;

    std::map<std::string, std::function<pybind11::list(pybind11::list)>> api_callbacks;

    std::map<std::string, pybind11::list> api_callbacks_response;

private:
    bool compute_request_and_response_meta_data() override
    {
        if (response_meta_data_str.empty())
        {
            response_meta_data_dict = pybind11::dict();
            return false;
        }

        pybind11::module json_module = pybind11::module::import("json");

        pybind11::object json_loads = json_module.attr("loads");

        pybind11::object parsed_dict = json_loads(response_meta_data_str);

        response_meta_data_dict = parsed_dict.cast<pybind11::dict>();

        if (response_meta_data_dict.contains("time"))
        {
            request_meta_data_dict["meta_data"] = response_meta_data_dict["meta_data"];
            request_meta_data_dict["send"] = pybind11::dict();
            request_meta_data_dict["receive"] = pybind11::dict();

            if (response_meta_data_dict.contains("send"))
            {
                for (const auto &send_objects : response_meta_data_dict["send"].cast<pybind11::dict>())
                {
                    request_meta_data_dict["send"][send_objects.first] = pybind11::list();
                    const pybind11::dict attributes = send_objects.second.cast<pybind11::dict>();
                    for (const auto &attribute : attributes)
                    {
                        request_meta_data_dict["send"][send_objects.first].cast<pybind11::list>().append(attribute.first.cast<std::string>());
                    }
                }
            }

            if (response_meta_data_dict.contains("receive"))
            {
                for (const auto &receive_objects : response_meta_data_dict["receive"].cast<pybind11::dict>())
                {
                    request_meta_data_dict["receive"][receive_objects.first] = pybind11::list();
                    const pybind11::dict attributes = receive_objects.second.cast<pybind11::dict>();
                    for (const auto &attribute : attributes)
                    {
                        request_meta_data_dict["receive"][receive_objects.first].cast<pybind11::list>().append(attribute.first.cast<std::string>());
                    }
                }
            }

            return true;
        }

        return false;
    }

    void compute_request_buffer_sizes(size_t &req_send_buffer_size, size_t &req_receive_buffer_size) const override
    {
        std::map<std::string, size_t> request_buffer_sizes = {{"send", 1}, {"receive", 1}};

        for (std::pair<const std::string, size_t> &request_buffer_size : request_buffer_sizes)
        {
            if (!request_meta_data_dict.contains(request_buffer_size.first.c_str()))
            {
                continue;
            }

            for (const auto &send_objects : request_meta_data_dict[request_buffer_size.first.c_str()].cast<pybind11::dict>())
            {
                const std::string object_name = send_objects.first.cast<std::string>();
                if (object_name.compare("") == 0 || request_buffer_size.second == -1)
                {
                    request_buffer_size.second = -1;
                    break;
                }

                const pybind11::list attributes = send_objects.second.cast<pybind11::list>();
                for (size_t i = 0; i < pybind11::len(attributes); i++)
                {
                    if (attributes[i].cast<std::string>().compare("") == 0)
                    {
                        request_buffer_size.second = -1;
                        break;
                    }
                    request_buffer_size.second += attribute_map[attributes[i].cast<std::string>()];
                }
            }
        }

        req_send_buffer_size = request_buffer_sizes["send"];
        req_receive_buffer_size = request_buffer_sizes["receive"];
    }

    void compute_response_buffer_sizes(size_t &res_send_buffer_size, size_t &res_receive_buffer_size) const override
    {
        std::map<std::string, size_t> response_buffer_sizes = {{"send", 1}, {"receive", 1}};

        for (std::pair<const std::string, size_t> &response_buffer_size : response_buffer_sizes)
        {
            if (!response_meta_data_dict.contains(response_buffer_size.first.c_str()))
            {
                continue;
            }

            for (const auto &receive_objects : response_meta_data_dict[response_buffer_size.first.c_str()].cast<pybind11::dict>())
            {
                const pybind11::dict attributes = receive_objects.second.cast<pybind11::dict>();
                for (const auto &attribute : attributes)
                {
                    response_buffer_size.second += attribute.second.cast<pybind11::list>().size();
                }
            }
        }

        res_send_buffer_size = response_buffer_sizes["send"];
        res_receive_buffer_size = response_buffer_sizes["receive"];
    }

    void start_connect_to_server_thread() override
    {
        MultiverseClientPybind::connect_to_server();
    }

    void wait_for_connect_to_server_thread_finish() override
    {
    }

    void start_meta_data_thread() override
    {
        MultiverseClientPybind::send_and_receive_meta_data();
    }

    void wait_for_meta_data_thread_finish() override
    {
    }

    bool init_objects(bool from_response_meta_data = false) override
    {
        if (from_response_meta_data)
        {
            bind_request_meta_data();
        }
        return true;
    }

    void bind_request_meta_data() override
    {
        request_meta_data_str = pybind11::str(request_meta_data_dict).cast<std::string>();
        std::replace(request_meta_data_str.begin(), request_meta_data_str.end(), '\'', '"');
    }

    void bind_response_meta_data() override
    {
    }

    void bind_api_callbacks() override
    {
        pybind11::list api_callbacks_list = response_meta_data_dict["api_callbacks"].cast<pybind11::list>();
        for (size_t i = 0; i < pybind11::len(api_callbacks_list); i++)
        {
            const pybind11::dict api_callback_dict = api_callbacks_list[i].cast<pybind11::dict>();
            for (auto api_callback_pair : api_callback_dict)
            {
                const std::string api_callback_name = api_callback_pair.first.cast<std::string>();
                if (api_callbacks.find(api_callback_name) == api_callbacks.end())
                {
                    continue;
                }
                const pybind11::list api_callback_arguments = api_callback_pair.second.cast<pybind11::list>();
                const pybind11::list api_callback_response = api_callbacks[api_callback_name.c_str()](api_callback_arguments);
                api_callbacks_response[api_callback_name.c_str()] = api_callback_response;
            }
        }
    }

    void bind_api_callbacks_response() override
    {
        request_meta_data_dict["api_callbacks_response"] = pybind11::list();
        pybind11::list api_callbacks_list = response_meta_data_dict["api_callbacks"].cast<pybind11::list>();
        for (size_t i = 0; i < pybind11::len(api_callbacks_list); i++)
        {
            const pybind11::dict api_callback_dict = api_callbacks_list[i].cast<pybind11::dict>();
            for (auto api_callback_pair : api_callback_dict)
            {
                const std::string api_callback_name = api_callback_pair.first.cast<std::string>();
                pybind11::dict api_callback_dict_request;
                if (api_callbacks.find(api_callback_name) != api_callbacks.end())
                {                
                    api_callback_dict_request[api_callback_name.c_str()] = api_callbacks_response[api_callback_name.c_str()];
                }
                else
                {
                    api_callback_dict_request[api_callback_name.c_str()] = pybind11::list();
                    api_callback_dict_request[api_callback_name.c_str()].cast<pybind11::list>().append("not implemented");
                }
                request_meta_data_dict["api_callbacks_response"].cast<pybind11::list>().append(api_callback_dict_request);
            }
        }
    }

    void clean_up() override
    {
        // TODO: Find a clean way to clear the data because it's unsure if the data is still in use.

        // send_data.clear();

        // receive_data.clear();
    }

    void reset() override
    {
        printf("[Client %s] Resetting the client (will be implemented).\n", port.c_str());
    }

    void init_send_and_receive_data() override
    {
        if (send_buffer_size != send_data.size())
        {
            send_data = std::vector<double>(send_buffer_size, 0.0);
        }
        if (receive_buffer_size != receive_data.size())
        {
            receive_data = std::vector<double>(receive_buffer_size, 0.0);
        }
    }

    void bind_send_data() override
    {
        if (send_buffer_size != send_data.size())
        {
            printf("[Client %s] The size of in_send_data (%ld) does not match with send_buffer_size (%ld).\n", port.c_str(), send_data.size(), send_buffer_size);
            return;
        }

        std::copy(send_data.begin(), send_data.end(), send_buffer);
    }

    void bind_receive_data() override
    {
        receive_data = std::vector<double>(receive_buffer, receive_buffer + receive_buffer_size);
    }
};

PYBIND11_MODULE(multiverse_client_pybind, handle)
{
    handle.doc() = "";

    pybind11::class_<MultiverseClient>(handle, "MultiverseClient")
        .def("connect", static_cast<void (MultiverseClient::*)(const std::string &, const std::string &)>(&MultiverseClient::connect))
        .def("start", &MultiverseClient::start)
        .def("communicate", &MultiverseClient::communicate)
        .def("disconnect", &MultiverseClient::disconnect)
        .def("get_time_now", &MultiverseClient::get_time_now);

    pybind11::class_<MultiverseClientPybind, MultiverseClient>(handle, "MultiverseClientPybind")
        .def(pybind11::init<const std::string &>())
        .def("set_request_meta_data", &MultiverseClientPybind::set_request_meta_data)
        .def("get_response_meta_data", &MultiverseClientPybind::get_response_meta_data)
        .def("set_send_data", &MultiverseClientPybind::set_send_data)
        .def("get_receive_data", &MultiverseClientPybind::get_receive_data)
        .def("set_api_callbacks", &MultiverseClientPybind::set_api_callbacks);
}