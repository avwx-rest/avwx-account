"""
This script runs the AVWX application using a development server.
"""

from avwx_account import app

app.run(port=8000, debug=True)
