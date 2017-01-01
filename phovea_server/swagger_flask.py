
from swagger_parser import SwaggerParser

parser = SwaggerParser(swagger_path='./swagger/last_deployment.yml')

print parser.specification
