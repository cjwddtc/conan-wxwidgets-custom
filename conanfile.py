from conans.util.files import save, load
from conans import ConanFile, CMake
import platform
import os
from glob import glob
import posixpath
import string
import re
from collections import namedtuple

class WxWidgetsConan(ConanFile):
    name = "wxWidgets_custom"
    version = "master"
    url = "https://github.com/SteffenL/conan-wxwidgets-custom"
    license = "wxWindows Library Licence"
    settings = {
        "os": ["Windows"],
        "compiler": ["Visual Studio"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86", "x86_64"]
    }
    options = {
        "shared": [True, False],
        "use_gui": [True, False]
    }
    default_options = "shared=True", "use_gui=True"
    exports = "wxWidgets/*"

    # If this is changed, remember to update exports as well.
    repo_subdir = "wxWidgets"

    git_branch_format = "custom-{version}"
    git_branch = None
    git_repository_url = "https://github.com/SteffenL/wxWidgets"

    wx_lib_name_version = None
    wx_platform = None
    wx_compiler_prefix = None
    wx_libs_dir = None
    wx_lib_name_formats = [
        "wxbase{version}{unicode}{debug}",
        "wxbase{version}{unicode}{debug}_net",
        "wxbase{version}{unicode}{debug}_xml",
        "wx{platform}{version}{unicode}{debug}_adv",
        "wx{platform}{version}{unicode}{debug}_aui",
        "wx{platform}{version}{unicode}{debug}_core",
        "wx{platform}{version}{unicode}{debug}_gl",
        "wx{platform}{version}{unicode}{debug}_html",
        "wx{platform}{version}{unicode}{debug}_media",
        "wx{platform}{version}{unicode}{debug}_propgrid",
        "wx{platform}{version}{unicode}{debug}_qa",
        "wx{platform}{version}{unicode}{debug}_ribbon",
        "wx{platform}{version}{unicode}{debug}_richtext",
        "wx{platform}{version}{unicode}{debug}_stc",
        "wx{platform}{version}{unicode}{debug}_webview",
        "wx{platform}{version}{unicode}{debug}_xrc",
        "wxexpat{debug}",
        "wxjpeg{debug}",
        "wxpng{debug}",
        "wxregex{unicode}{debug}",
        "wxscintilla{debug}",
        "wxtiff{debug}",
        "wxzlib{debug}"
    ]
    wx_lib_names = []
    wx_unicode_suffix = ""
    wx_debug_suffix = ""
    wx_build_dir = None
    wx_include_dir = None
    wx_compiler_include_dir = None
    wx_platform_include_dir = None
    wx_compiler_defines = []
    wx_version = None

    wx_compiler_prefix_map = {
        "Visual Studio": "vc"
    }
    wx_compiler_include_dir_map = {
        "Visual Studio": "msvc"
    }
    wx_platform_map = {
        "Windows": "msw"
    }
    wx_compiler_defines_for_platform_map = {
        "Windows": ["__WXMSW__", "WINVER=0x0500"]
    }
    wx_compiler_defines_for_compiler_map = {
        "Visual Studio": ["_CRT_SECURE_NO_WARNINGS", "UNICODE", "_UNICODE"]
    }

    def config(self):
        pass

    def conan_info(self):
        # This option is just for clients, not for building the library. It should not generate a new variation of the package.
        self.info.options.use_gui = "Any"

    def source(self):
        git_branch = self.git_branch_format.format(version=self.version)
        git_clone_params = [
            "--depth 1",
            "--branch %s" % git_branch,
            self.git_repository_url,
            self.repo_subdir
        ]

        self.run("git clone %s" % string.join(git_clone_params, " "))

        self.wx_version = self.read_wx_version(os.path.join(self.repo_subdir, "include/wx/version.h"))
        self.wx_lib_name_version = "".join([str(self.wx_version.major), str(self.wx_version.minor)])
        self.wx_lib_names = self.wx_expand_lib_name_vars(self.wx_lib_name_formats)

    def build(self):
        os.chdir(os.path.join(self.repo_subdir, self.wx_build_dir))
        if self.settings.compiler != "Visual Studio":
            self.build_with_visual_studio()
        else:
            self.build_with_make()

    def package(self):
        repo_libs_dir = posixpath.join(self.repo_subdir, self.wx_libs_dir)
        #libs_include_dir_name = self.wx_platform + self.wx_unicode_suffix + self.wx_debug_suffix
        self.copy(pattern="*.dll", dst="bin", src=repo_libs_dir)
        self.copy(pattern="*.lib", dst="lib", src=repo_libs_dir)
        self.copy(pattern="*.h", dst=self.wx_libs_dir, src=repo_libs_dir)
        #self.copy(pattern=libs_include_dir_name, dst="lib", src=repo_libs_dir)
        self.copy(pattern="*", dst="include", src=posixpath.join(self.repo_subdir, self.wx_include_dir))

    def package_info(self):
        self.gather_wx_config()

        self.cpp_info.includedirs = [self.wx_include_dir, self.wx_platform_include_dir, self.wx_compiler_include_dir]
        self.cpp_info.libs = self.wx_lib_names
        self.cpp_info.defines = self.wx_compiler_defines

    def config_compiler_defines(self):
        if self.settings.build_type == "Debug":
            self.wx_compiler_defines.append("__WXDEBUG__")

        self.wx_compiler_defines.append("wxUSE_GUI=%s" % 1 if self.options.use_gui else 0)

        if self.options.shared:
            if self.settings.os == "Windows":
                self.wx_compiler_defines.append("WXUSINGDLL")

        self.wx_compiler_defines.extend(self.wx_compiler_defines_for_platform_map[str(self.settings.os)])
        self.wx_compiler_defines.extend(self.wx_compiler_defines_for_compiler_map[str(self.settings.compiler)])

    def config_include_dirs(self):
        self.wx_include_dir = "include"
        self.wx_compiler_include_dir = posixpath.join(self.wx_include_dir, self.wx_compiler_include_dir_map[str(self.settings.compiler)])
        self.wx_platform_include_dir = posixpath.join("lib", self.wx_platform + self.wx_unicode_suffix)

    def wx_expand_lib_name_vars(self, name_format_list):
        return [
            name_format.format(
                platform=self.wx_platform,
                version=self.wx_lib_name_version,
                unicode=self.wx_unicode_suffix,
                debug=self.wx_debug_suffix
            ) for name_format in name_format_list
        ]

    def read_wx_version(self, version_header_path):
        with open(version_header_path, "r") as f:
            content = f.read()
            version = Version(
                int(re.search("wxMAJOR_VERSION\s+(\d+)", content).groups()[0]),
                int(re.search("wxMINOR_VERSION\s+(\d+)", content).groups()[0]),
                int(re.search("wxRELEASE_NUMBER\s+(\d+)", content).groups()[0])
            )
            return version

    def gather_wx_config(self):
        self.wx_platform = self.wx_platform_map[str(self.settings.os)]
        self.wx_compiler_prefix = self.wx_compiler_prefix_map[str(self.settings.compiler)]

        # Unicode should always be enabled
        self.wx_unicode_suffix = "u"

        if self.settings.build_type == "Debug":
            self.wx_debug_suffix = "d"

        self.wx_libs_dir = posixpath.join("lib/{0}_{1}{2}".format(
            self.wx_compiler_prefix,
            "x64" + "_" if self.settings.arch == "x86_64" else "",
            # TODO: Check this for platforms other than Windows
            "dll" if self.options.shared else "lib"
        ))

        self.config_compiler_defines()
        self.config_include_dirs()

        self.wx_build_dir = posixpath.join("build", self.wx_platform)

    def build_with_visual_studio(self):
        solution_file_name = "wx_vc{0}.sln".format(str(self.settings.compiler.version))
        config_name_prefix = "DLL " if self.options.shared else "" 
        config_name = config_name_prefix + str(self.settings.build_type)
        platform = "x64" if self.settings.arch == "x86_64" else "Win32"
        runtime_map = {
            "MDd": "MultiThreadedDebugDLL",
            "MD": "MultiThreadedDLL",
            "MTd": "MultiThreadedDebug",
            "MT": "MultiThreaded"
        }
        runtime = runtime_map[str(self.settings.compiler.runtime)]
        vs_version = self.settings.compiler.version

        # Replace runtime library in all project files
        project_file_paths = glob("*.vcxproj")
        for file_path in project_file_paths:
            patched_content = load(file_path)
            patched_content = re.sub("(?<=<RuntimeLibrary>)[^<]*", runtime, patched_content)
            save(file_path, patched_content)

        build_cmd = "msbuild \"{solution}\" /t:Build \"/p:Configuration={config}\" \"/p:Platform={platform}\" \"/p:VisualStudioVersion={vs_version}\" /m".format(
            solution=solution_file_name,
            config=config_name,
            platform=platform,
            vs_version=vs_version
        )
        self.run(build_cmd)

    def build_with_make(self):
        compiler_configs = {
            "Visual Studio": {
                "runtime": {"MDd": "dynamic", "MD": "dynamic", "MTd": "static", "MT": "static"},
                "make_command_format": "nmake -f makefile.vc {0}"
            }
        }

        # Conan build type to wx build type
        build_type_map = {
            "Debug": "debug",
            "Release": "release"
        }

        compiler_config = compiler_configs[str(self.settings.compiler)]

        # Default runtime library
        runtime_libs = "dynamic"
        if self.settings.compiler.runtime != None:
            runtime_map = compiler_config["runtime"]
            runtime_libs = runtime_map[str(self.settings.compiler.runtime)]

        make_params = "RUNTIME_LIBS={runtime_libs} UNICODE={unicode} SHARED={shared} MONOLITHIC={monolithic} TARGET_CPU={target_cpu} BUILD={build}".format(
            runtime_libs=runtime_libs,
            unicode=1,
            shared=1 if self.options.shared else 0,
            monolithic=0,
            target_cpu="x64" if self.settings.arch == "x86_64" else "x86",
            build=build_type_map[str(self.settings.build_type)]
        )

        cmd = compiler_config["make_command_format"].format(make_params)
        self.run(cmd)

class Version:
    major = None
    minor = None
    release = None

    def __init__(self, major, minor, release):
        self.major = major
        self.minor = minor
        self.release = release 
