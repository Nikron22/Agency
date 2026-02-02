# run.py
# -*- coding: utf-8 -*-
import sys
import os

# Устанавливаем кодировку
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

from app import app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)