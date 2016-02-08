import common

import platform
import os
import subprocess
import re
import shutil
import multiprocessing


class RunCommandWrapperArg:
    command = None
    working_dir = None
    environment = None

    def __init__(self, command, working_dir = None, environment = None):
        self.command = command
        self.working_dir = working_dir;
        self.environment = environment


class Program:
    conan_user = "sl"
    conan_channel = "develop"

    project_root_dir = None

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.project_root_dir = self.script_dir

    def run(self):
        commands = []
        commands.append("conan export {0}/{1}".format(self.conan_user, self.conan_channel))
        commands.extend(self.get_conan_test_commands())

        # Wrap commands if needed
        command_wrappers = [
            command if isinstance(command, RunCommandWrapperArg)
            else RunCommandWrapperArg(command=command, working_dir=self.project_root_dir)
            for command in commands
        ]

        print("------------------------------------------------------------")
        print("\n".join(["cmd: {0}\ncwd: {1}".format(x.command, x.working_dir) for x in command_wrappers]))
        print("------------------------------------------------------------")

        # Run commands
        for cw in command_wrappers:
            self.run_command_wrapper(cw)

    def run_command(self, command, working_dir=None, environment=None):
        if working_dir is None:
            working_dir = os.getcwd()

        subprocess.check_call(command, cwd=working_dir, env=environment)

    def run_command_wrapper(self, wrapper_arg):
        self.run_command(
            command=wrapper_arg.command,
            working_dir=wrapper_arg.working_dir,
            environment=wrapper_arg.environment
        )

    def get_conan_test_commands_for_windows(self):
        commands = []
        commands.extend(self.get_conan_test_commands_for_visualstudio())
        return commands

    def get_conan_test_commands_for_visualstudio(self):
        commands = []

        compiler = "Visual Studio"
        compiler_versions = [14]
        architectures = ["x86", "x86_64"]
        vc_architectures = ["x86", "amd64"]

        # Map Conan architecture to Visual Studio/VC++ architecture
        vc_architecture_map = {
            "x86": "x86",
            "x86_64": "amd64"
        }

        # Get the environment variables needed for building with VC++
        vc_environments = common.VisualStudioEnvironmentHarvester(compiler_versions, vc_architectures).harvest()

        for compiler_version in compiler_versions:
            for architecture in architectures:
                # Environment (variables) to use when running commands
                vc_environment = vc_environments[compiler_version][vc_architecture_map[architecture]]

                conan_test_commands = [
                    RunCommandWrapperArg(
                        command=common.ConanTestCommandBuilder(
                            settings=common.ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Debug", compiler_runtime="MDd"),
                            options = { "wxWidgets_custom:shared": "True" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    ),
                    RunCommandWrapperArg(
                        command=common.ConanTestCommandBuilder(
                            settings=common.ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Release", compiler_runtime="MD"),
                            options = { "wxWidgets_custom:shared": "True" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    ),
                    RunCommandWrapperArg(
                        command=common.ConanTestCommandBuilder(
                            settings=common.ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Release", compiler_runtime="MD"),
                            options = { "wxWidgets_custom:shared": "False" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    ),
                    RunCommandWrapperArg(
                        command=common.ConanTestCommandBuilder(
                            settings=common.ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Release", compiler_runtime="MT"),
                            options = { "wxWidgets_custom:shared": "False" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    )
                ]

                commands.extend(conan_test_commands)

        return commands

    def get_conan_test_commands(self):
        if platform.system() == "Windows":
            return self.get_conan_test_commands_for_windows()
        else:
            raise Exception("Unsupported platform")

if __name__ == "__main__":
    Program().run()
