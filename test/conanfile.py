from conans import ConanFile, CMake
import os

class RunConanTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    requires = "wxWidgets_custom/master@sl/develop"

    def build(self):
        cmake = CMake(self.settings)
        self.run("cmake . %s" % cmake.command_line)
        self.run("cmake --build . %s" % cmake.build_config)

    def imports(self):
        self.copy(pattern="*.dll", dst="bin", src="bin")

    def test(self):
        os.chdir("bin")
        self.run("run_conan_test")
