from conan.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add_common_builds(shared_option_name="wxWidgets_custom:shared", pure_c=False, stable_branch_pattern=r"release/")
    builder.run()
