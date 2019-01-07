import stripe
from avwx_account import app

stripe.api_key = app.config['STRIPE_SECRET_KEY']

plans = {
    'basic': {
        'id': app.config['STRIPE_BASIC_ID'],
        'description': 'AVWX Basic Monthly',
        'price': 10,
    },
    'enterprise': {
        'id': app.config['STRIPE_ENTERPRISE_ID'],
        'description': 'AVWX Enterprise Monthly',
        'price': 40,
    },
}
