import setuptools
import os
import subprocess
import shutil
import re

from pathlib import Path

from setuptools import Command

with open('eth2validatorwizard/__init__.py', 'rt') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

class Bundle(Command):
    ''' Create a bundle for release
    '''
    description = 'create a bundle for release'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        project_path = Path(os.getcwd())
        src_package_path = Path(project_path, 'eth2validatorwizard')

        # Create and clean the build dir
        build_path = Path(project_path, 'build')
        if build_path.exists():
            if build_path.is_dir():
                shutil.rmtree(build_path)
            elif build_path.is_file():
                build_path.unlink()
        
        build_path.mkdir(parents=True, exist_ok=True)

        # Copy package into build dir
        build_package_path = Path(build_path, 'eth2validatorwizard')
        shutil.copytree(src_package_path, build_package_path)

        # Install packages from requirements.txt file into build dir
        requirements_path = Path(project_path, 'requirements.txt')
        subprocess.run([
            'python3', '-m', 'pip', 'install', '-r', requirements_path,
            '--target', build_path
        ])

        # Copy __main__.py into build root
        src_main_path = Path(src_package_path, '__main__.py')
        build_main_path = Path(build_path, '__main__.py')
        shutil.copyfile(src_main_path, build_main_path)

        # Clean __pycache__ directories
        package_pycache_path = Path(build_package_path, '__pycache__')
        if package_pycache_path.exists() and package_pycache_path.is_dir():
            shutil.rmtree(package_pycache_path)

        # Clean .dist-info directories
        with os.scandir(build_path) as dir_it:
            for entry in dir_it:
                if entry.name.startswith('.') or not entry.is_dir():
                    continue
                
                if entry.name.endswith('.dist-info'):
                    shutil.rmtree(entry.path)

        # Bundle with zipapp
        dist_path = Path(project_path, 'dist')
        dist_path.mkdir(parents=True, exist_ok=True)

        bundle_name = f'eth2validatorwizard-{version}.pyz'
        bundle_path = Path(dist_path, bundle_name)
        if bundle_path.exists():
            if bundle_path.is_dir():
                shutil.rmtree(bundle_path)
            elif bundle_path.is_file():
                bundle_path.unlink()
        
        subprocess.run([
            'python3', '-m', 'zipapp', build_path, '-p', '/usr/bin/env python3',
            '-c', '-o', bundle_path
        ])

        # Sign bundle with GPG key
        bundle_sign_name = f'{bundle_name}.asc'
        bundle_sign_path = Path(dist_path, bundle_sign_name)
        if bundle_sign_path.exists():
            if bundle_sign_path.is_dir():
                shutil.rmtree(bundle_sign_path)
            elif bundle_sign_path.is_file():
                bundle_sign_path.unlink()
        
        subprocess.run([
            'gpg', '--default-key', '6EEC4CD326C4BBC79F51F55AE68A0CC47982CB5F', '--sign',
            '--armor', '--output', bundle_sign_path, '--detach-sig', bundle_path
        ])
   
if __name__ == "__main__":
    setuptools.setup(
        version=version,
        cmdclass={
            'bundle': Bundle
        }
    )