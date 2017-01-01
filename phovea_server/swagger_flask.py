import codecs
import yaml
from swagger_spec_validator.validator20 import validate_spec

with codecs.open('./swagger/idtype.yml', 'r', 'utf-8') as swagger_yaml:
  specification = yaml.load(swagger_yaml.read())

s = validate_spec(specification)
print s


connexion.decorators.validation.ParameterValidator
validator_map = {
    'body': CustomRequestBodyValidator,
    'parameter': CustomParameterValidator
}
app = connexion.App(__name__, ..., validator_map=validator_map)
