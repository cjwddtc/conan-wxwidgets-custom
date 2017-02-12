#from conans.util.files import save, load
from conans import ConanFile, CMake ,tools
import platform
import os
from glob import glob
import posixpath
import string
import re
from collections import namedtuple
import codecs

class WxWidgetsConan(ConanFile):
    name = "wxWidgets"
    version = "3.0.3"
    url = "https://github.com/cjwddtc/conan-wxwidgets-custom"
    license = "wxWindows Library Licence"
    settings = {
        "os",
        "compiler",
        "build_type",
        "arch"
    }
    options = {
        "shared": [True, False],
        "use_gui": [True, False]
    }
    default_options = "shared=False", "use_gui=True"
    exports = "wxWidgets/*"

    # If this is changed, remember to update exports as well.
    repo_subdir = "wxWidgets"
    ver_spl = version.split('.')
    git_branch =  "WX_"+ver_spl[0]+"_"+ver_spl[1]+"_BRANCH"
    git_repository_url = "https://github.com/wxWidgets/wxWidgets.git"

    def config(self):
        pass

    def conan_info(self):
        # This option is just for clients, not for building the library. It should not generate a new variation of the package.
        self.info.options.use_gui = "Any"

    def source(self):
        self.run("git clone %s %s %s" % ("--branch %s" % self.git_branch,self.git_repository_url,self.repo_subdir))
        self.wx_version = Version(int(self.ver_spl[0]),int(self.ver_spl[1]),int(self.ver_spl[2]))

    def build(self):
        os.chdir(self.repo_subdir)
        if self.settings.compiler == "Visual Studio":
            self.build_with_visual_studio()
        elif self.settings.compiler == "gcc":
            self.build_with_gcc()

    def package(self):
        lib_dir={
            "Windows":{True:"vc_dll",False:"vc_lib"},
            "Linux":{True:".",False:"."}
        }
        lib_dir_map={
            "x86_64" : "x64",
            "x86" : "x86",
            True : "dll",
            False : "lib"
        }
        dst_lib_dir=None
        src_libs_dir = posixpath.join(self.repo_subdir,"lib",lib_dir[str(self.settings.os)][bool(self.options.shared)])
        if str(self.settings.os) == "Windows":
            dst_lib_dir=posixpath.join("lib","vc_%s_%s"%(lib_dir_map[str(self.settings.arch)],lib_dir_map[bool(self.options.shared)]))
            self.copy(pattern="*.dll", dst=dst_lib_dir, src=src_libs_dir)
            self.copy(pattern="*.lib", dst=dst_lib_dir, src=src_libs_dir)
        elif str(self.settings.os) == "Linux":
            dst_lib_dir="lib"
            self.copy(pattern="*.so", dst=dst_lib_dir, src=src_libs_dir)
            self.copy(pattern="*.a", dst=dst_lib_dir, src=src_libs_dir)
            self.copy(pattern="wx-config",dst="bin",src="self.repo_subdir")
        self.copy(pattern="*", dst="include", src=posixpath.join(self.repo_subdir,"include"))
        self.copy(pattern="*.h", dst=dst_lib_dir, src=src_libs_dir)
    def package_info(self):
        self.env_info.wxWidgets_ROOT_DIR=self.package_folder
        self.env_info.path.append(posixpath.join(self.package_folder,"bin"))
        pass

    def build_with_visual_studio(self):
        os.chdir(os.path.join("build","msw"))
        build_type_map={
            "Debug": "BUILD=debug",
            "Release": "BUILD=release"
        }
        link_type_map={
            False: "SHARED=0",
            True: "SHARED=1"
        }
        self.run("nmake -f makefile.vc UNICODE=1 %s %s" %(build_type_map[str(self.settings.build_type)],link_type_map[bool(self.options.shared)]))
        os.chdir(os.path.join("..",".."))

    def build_with_gcc(self):
        # Conan build type to wx build type
        build_type_map={
            "Debug": "--enable-debug",
            "Release": "--disable-debug"
        }
        link_type_map = {
            False : "--disable-shared",
            True : "--enable-shared"
        }
        self.run("./configure --without-opengl --enable-unicode %s %s" % (build_type_map[str(self.settings.build_type)],link_type_map[bool(self.options.shared)]))
        self.run("make -j%s" % tools.cpu_count())

    def load(self, path, encoding=None):
        encoding = detect_by_bom(path, "utf-8") if encoding is None else encoding
        with codecs.open(path, "rb", encoding=encoding) as f:
            return f.read()

    def save(self, path, content, encoding=None):
        with codecs.open(path, "wb", encoding=encoding) as f:
            f.write(content)

class Version:
    major = None
    minor = None
    release = None

    def __init__(self, major, minor, release):
        self.major = major
        self.minor = minor
        self.release = release 
