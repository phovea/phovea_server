__author__ = 'Samuel Gratzl'

import sys
import argparse

sys.path.append('plugins/')
import caleydo_server.config

parser = argparse.ArgumentParser(description='Caleydo Web Server')
parser.add_argument('--application', '-a', help='application to generate the scripts for', default=None)
parser.add_argument('--context', '-c', help='application context', default=None)
parser.add_argument('--target', '-t', help='the target directory', default='_dist')
args = parser.parse_args()

#append the plugin directories as primary lookup path
sys.path.extend(caleydo_server.config.getlist('pluginDirs','caleydo_server'))

if __name__ == '__main__':
  import mainapp
  mainapp.dump_generated_files(args.target, args.application, args.context)

