from django.utils.translation import ugettext_lazy
try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    name = 'pretix_latexforms'
    verbose_name = 'Pretix LaTeX Forms'

    class PretixPluginMeta:
        name = ugettext_lazy('Pretix LaTeX Forms')
        author = 'Karl Engelhardt'
        description = ugettext_lazy('Add option generate PDFs with LaTeX after ordering')
        visible = True
        version = '1.0.3'
        compatibility = "pretix>=3.7.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_latexforms.PluginApp'
