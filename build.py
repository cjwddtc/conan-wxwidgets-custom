import platform
import os
import multiprocessing
import subprocess
import re
import shutil


class RunCommandWrapperArg:
    command = None
    working_dir = None

    def __init__(self, command, working_dir):
        self.command = command
        self.working_dir = working_dir;

class Program:
    conan_user = "sl"
    conan_channel = "develop"

    project_root_dir = None

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.project_root_dir = self.script_dir

    def run(self):
        self.run_command(
            command="conan export {0}/{1}".format(self.conan_user, self.conan_channel),
            working_dir=self.project_root_dir
        )

        # FIXME: We need to let Conan do its initial work before we run more jobs in parallel
        pool = multiprocessing.Pool(processes=min(1, multiprocessing.cpu_count()))
        commands = []

        if platform.system() == "Windows":
            commands.extend([
                "conan test -s compiler=\"Visual Studio\" -s compiler.version=14 -s arch=x86_64 -s build_type=Debug -s compiler.runtime=MDd -o wxWidgets_custom:shared=True",
                "conan test -s compiler=\"Visual Studio\" -s compiler.version=14 -s arch=x86_64 -s build_type=Release -s compiler.runtime=MD -o wxWidgets_custom:shared=True",
                "conan test -s compiler=\"Visual Studio\" -s compiler.version=14 -s arch=x86_64 -s build_type=Release -s compiler.runtime=MD -o wxWidgets_custom:shared=False",
                "conan test -s compiler=\"Visual Studio\" -s compiler.version=14 -s arch=x86_64 -s build_type=Release -s compiler.runtime=MT -o wxWidgets_custom:shared=False"
            ])
        else:
            raise Exception("Unsupported platform")

        command_wrappers = [RunCommandWrapperArg(command=command, working_dir=self.project_root_dir) for command in commands]

        print("------------------------------------------------------------")
        print("\n".join(["cmd: {0}\ncwd: {1}".format(x.command, x.working_dir) for x in command_wrappers]))
        print("------------------------------------------------------------")

        pool.map(self.run_command_wrapper, command_wrappers)

    def run_command(self, command, working_dir=None):
        if working_dir is None:
            working_dir = os.getcwd()

        subprocess.check_call(command, cwd=working_dir)

    def run_command_wrapper(self, wrapper_arg):
        self.run_command(
            command=wrapper_arg.command,
            working_dir=wrapper_arg.working_dir
        )

if __name__ == "__main__":
    Program().run()
