import platform
import os
import subprocess
import re
import shutil
import multiprocessing

    
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
