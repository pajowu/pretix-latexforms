Pretix LaTeX Forms
==========================

This is a plugin for `pretix`_.

Development setup
-----------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository, eg to ``local/pretix-latexforms``.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.


License
-------
Heavily based on pretix pages and django-tex

Copyright 2020 Karl Engelhardt

Released under the terms of the Apache License 2.0

The code in ``tex.py`` is based on http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs and the django-tex software and release under the MIT License



.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
