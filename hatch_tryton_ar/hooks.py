# This file is part of hatch-tryton-ar.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin import hookimpl

class TrytonArGitMappingHook(MetadataHookInterface):
    PLUGIN_NAME = 'tryton-ar'

    def update(self, metadata):
        version = metadata.get('version', '8.0.0')
        branch = '.'.join(version.split('.')[:2]) # "8.0"

        dependencies = metadata.get('dependencies', [])
        new_deps = []

        for dep in dependencies:
            if dep.startswith('trytonar_'):
                # Extraemos el nombre del módulo limpio (ej: trytonar_party_ar -> party_ar)
                module_name = dep.split()[0].replace('trytonar_', '')
                # Reemplazamos por la URL de Git apuntando al branch correcto
                new_deps.append(f"trytonar_{module_name} @ git+https://github.com/tryton-ar/{module_name}.git@{branch}")
            else:
                new_deps.append(dep)

        metadata['dependencies'] = new_deps

# Registramos el Hook en el gestor de plugins de Hatch
@hookimpl
def hatch_register_metadata_hook():
    return TrytonArGitMappingHook
