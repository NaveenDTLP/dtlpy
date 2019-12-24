from behave.__main__ import main as behave_main
import logging
logging.basicConfig(level='DEBUG')

# feature_filename = 'test_annotations_edit.feature'
feature_filename = 'plugins_flow.feature'

behave_main(['tests/features', '-i', feature_filename, '--stop', '--no-capture'])
