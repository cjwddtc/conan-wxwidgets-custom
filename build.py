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


class ConanTestSettings:
    compiler = None
    compiler_version = None
    compiler_runtime = None
    architecture = None
    build_type = None

    def __init__(self, compiler, compiler_version, compiler_runtime, architecture, build_type):
        self.compiler = compiler
        self.compiler_version = compiler_version
        self.compiler_runtime = compiler_runtime
        self.architecture = architecture
        self.build_type = build_type


class ConanTestCommandBuilder:
    command = None

    def __init__(self, settings, options = {}):
        conan_settings = [
            ("compiler", settings.compiler),
            ("compiler.version", settings.compiler_version),
            ("compiler.runtime", settings.compiler_runtime),
            ("arch", settings.architecture),
            ("build_type", settings.build_type)
        ]
        conan_cmd = "conan test"
        # Transform settings into command line parameters
        conan_settings_params = ["-s {0}=\"{1}\"".format(k, v) for k, v in conan_settings]
        # Transform options into command line parameters
        conan_options_params = ["-o {0}=\"{1}\"".format(k, v) for k, v in options.items()]
        # Build the full command line
        conan_all_cmd_tokens = []
        conan_all_cmd_tokens.append(conan_cmd)
        conan_all_cmd_tokens.extend(conan_settings_params)
        conan_all_cmd_tokens.extend(conan_options_params)
        conan_full_cmd = " ".join(conan_all_cmd_tokens)
        self.command = conan_full_cmd


class VisualStudioEnvironmentHarvester:
    _compiler_versions = None
    _architectures = None

    def __init__(self, compiler_versions, architectures):
        self._compiler_versions = compiler_versions
        self._architectures = architectures

    def get_vc_environment(self, compiler_version, architecture):
        # Open the Visual Studio shell and extract the environment variables
        vc_vars_dump = subprocess.check_output(
            "cmd /c \"\"C:\\Program Files (x86)\\Microsoft Visual Studio {compiler_version}.0\\VC\\vcvarsall.bat\"\" {architecture} && set".format(
                compiler_version=compiler_version,
                architecture=architecture
            )
        ).decode().strip()
        vc_vars = [line.split("=") for line in vc_vars_dump.split("\r\n")]
        # Using str() here because running a sub-process with an environment that contains unicode strings fails with Python 2, and using byte strings fails with Python 3. 
        vc_vars = {str(k): str(v) for k, v in vc_vars}

        return vc_vars

    def get_vc_environments_pool_function(self, arg):
        version = arg[0]
        arch = arg[1]
        arg.append(self.get_vc_environment(version, arch))
        return arg

    def get_vc_environments(self, compiler_versions, architectures):
        args = []
        for version in compiler_versions:
            for arch in architectures:
                args.append([version, arch])
        pool = multiprocessing.Pool(processes=min(len(args), multiprocessing.cpu_count()))
        result = pool.map(self.get_vc_environments_pool_function, args)
        return result

    def harvest(self):
        result = {}
        env_items = self.get_vc_environments(self._compiler_versions, self._architectures)
        for env_item in env_items:
            version = env_item[0]
            arch = env_item[1]
            env = env_item[2]

            if not version in result:
                result[version] = {}

            result[version][arch] = env
        return result

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
        vc_environments = VisualStudioEnvironmentHarvester(compiler_versions, vc_architectures).harvest()

        for compiler_version in compiler_versions:
            for architecture in architectures:
                # Environment (variables) to use when running commands
                vc_environment = vc_environments[compiler_version][vc_architecture_map[architecture]]

                conan_test_commands = [
                    RunCommandWrapperArg(
                        command=ConanTestCommandBuilder(
                            settings=ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Debug", compiler_runtime="MDd"),
                            options = { "wxWidgets_custom:shared": "True" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    ),
                    RunCommandWrapperArg(
                        command=ConanTestCommandBuilder(
                            settings=ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Release", compiler_runtime="MD"),
                            options = { "wxWidgets_custom:shared": "True" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    ),
                    RunCommandWrapperArg(
                        command=ConanTestCommandBuilder(
                            settings=ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Release", compiler_runtime="MD"),
                            options = { "wxWidgets_custom:shared": "False" }
                        ).command,
                        working_dir=self.project_root_dir,
                        environment=vc_environment
                    ),
                    RunCommandWrapperArg(
                        command=ConanTestCommandBuilder(
                            settings=ConanTestSettings(compiler=compiler, compiler_version=compiler_version, architecture=architecture, build_type="Release", compiler_runtime="MT"),
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
