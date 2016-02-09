from conans import ConanFile, CMake
import os

class RunConanTestConan(ConanFile):
    _conan_user = os.getenv("CONAN_CHANNEL", "sl")
    _conan_channel = os.getenv("CONAN_CHANNEL", "testing")

    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    requires = "wxWidgets_custom/master@{0}/{1}".format(_conan_user, _conan_channel)

    def build(self):
        cmake = CMake(self.settings)
        self.run("cmake . %s" % cmake.command_line)
        self.run("cmake --build . %s" % cmake.build_config)

    def imports(self):
        self.copy(pattern="*.dll", dst="bin", src="bin")

    def test(self):
        self.run(os.path.join(".", "bin", "run_conan_test"))
