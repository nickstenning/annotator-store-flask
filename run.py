import os

import annotator.store as store
import annotator.model as model

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath( __file__ ))

    if 'ANNOTATOR_CONFIG' in os.environ:
        store.app.config.from_envvar('ANNOTATOR_CONFIG')
    else:
        store.app.config.from_pyfile(here + '/annotator.cfg')

    model.metadata.bind = store.app.config['DB']

    # Create tables
    model.setup_all(True)
    # Setup app
    store.setup_app()

    # For testing purposes only
    if store.app.config.get('TEST_CONSUMER'):
        from annotator.test_consumer import consumer
        consumer.test_consumer_key  = store.app.config['TEST_CONSUMER_KEY']
        consumer.test_consumer_user = store.app.config['TEST_CONSUMER_USER']
        store.app.register_module(consumer, url_prefix='/auth')

    store.app.run()
