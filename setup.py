#!/usr/bin/python3
"""Setup module for provisioner pkg."""
from setuptools import setup, find_packages
import os
import sys
import shutil
import stat
from setuptools.command.develop import develop
from setuptools.command.install import install

pkg_name = "text_img_creator"
parent_dir = os.path.dirname(os.path.realpath(__file__))
data_src_dir = pkg_name + "_data"
config_src_dir = pkg_name + "_config"
defaults_location = os.path.join(pkg_name, "defaults")
requires = list(())

# Create scripts list
script_dir = os.path.join(parent_dir, "bin")
scripts = []
try:
    for f in os.listdir(script_dir):
        scripts.append(os.path.join(script_dir, str(f)))

except FileNotFoundError:
    pass

pkg_has_config = not True
if pkg_has_config:
    requires.append("provision_py_proj")


def copy_pkg_files():
    """Copy config and data files."""
    from appdirs import user_data_dir, user_config_dir

    pkg_dirs_to_copy = [
        (data_src_dir, user_data_dir()),
        (config_src_dir, user_config_dir())
    ]
    for d, t in pkg_dirs_to_copy:
        t = os.path.join(t, d)
        d = os.path.join(pkg_name, d)

        shutil.rmtree(t, ignore_errors=True)
        shutil.copytree(d, t)

        user = os.environ["SUDO_USER"]

        for root, dirs, files in os.walk(t):
            shutil.chown(root, user=user, group=user)
            os.chmod(root, stat.S_IRWXU)

            for d in dirs:
                d_path = os.path.join(root, d)
                shutil.chown(d_path, user=user, group=user)
                os.chmod(d_path, stat.S_IRWXU)

            for f in files:
                f_path = os.path.join(root, f)
                shutil.chown(f_path, user=user, group=user)
                os.chmod(f_path, stat.S_IRUSR | stat.S_IWUSR)


def reset():
    """Remove build dirs."""
    dirnames_to_remove = [pkg_name + ".egg-info", "dist", "build"]
    for d in dirnames_to_remove:
        shutil.rmtree(d, ignore_errors=True)


def setuptools_setup():
    """Setup provisioner."""
    setup(
        name="text_img_creator",
        version="0.1",
        description="",
        url="default url",
        author="Kevin Wolf",
        author_email="kevinuwolf@gmail.com",
        license="gplv3.txt",
        packages=find_packages(),
        scripts=scripts,
        install_requires=requires,
        setup_requires=requires,
    )


def main():
    """Main method."""
    os.chdir(parent_dir)

    if sys.argv[1] == "reset":
        reset()
    else:
        setuptools_setup()
        if pkg_has_config:
            copy_pkg_files()

if __name__ == "__main__":
    main()
