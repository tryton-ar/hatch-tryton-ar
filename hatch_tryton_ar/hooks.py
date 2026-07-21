# This file is part of hatch-tryton-ar.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from typing import Dict, Optional, Tuple

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin import hookimpl


class TrytonArGitMappingHook(MetadataHookInterface):
    PLUGIN_NAME = 'tryton-ar'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._external_repos: Dict[str, Tuple[str, str]] = {}
        raw = self.config.get('external-repos', {})
        for key, value in raw.items():
            parts = value.split('/')
            if len(parts) != 2:
                raise ValueError(
                    f"[tool.hatch.metadata.hooks.tryton-ar.external-repos]"
                    f"\nKey '{key}' must be formatted as 'org/repo', got: '{value}'"
                )
            org, repo = parts
            if not org or not repo:
                raise ValueError(
                    f"[tool.hatch.metadata.hooks.tryton-ar.external-repos]"
                    f"\nKey '{key}': 'org/repo' values cannot be empty"
                )
            self._external_repos[key] = (org, repo)

        # New: support for mapping modules to external repos via [repos] section
        self._repos: Dict[str, Tuple[str, str]] = {}
        raw = self.config.get('repos', {})
        for key, value in raw.items():
            parts = value.split('/')
            if len(parts) != 2:
                raise ValueError(
                    f"[tool.hatch.metadata.hooks.tryton-ar.repos]"
                    f"\nKey '{key}' must be formatted as 'org/repo', got: '{value}'"
                )
            org, repo = parts
            if not org or not repo:
                raise ValueError(
                    f"[tool.hatch.metadata.hooks.tryton-ar.repos]"
                    f"\nKey '{key}': 'org/repo' values cannot be empty"
                )
            self._repos[key] = (org, repo)

    def _resolve_git_url(self, module_name: str, branch: str) -> str:
        """Resuelve la URL de Git para un módulo dado."""
        if module_name in self._external_repos:
            org, repo = self._external_repos[module_name]
            return f"git+https://github.com/{org}/{repo}.git@{branch}"
        return f"git+https://github.com/tryton-ar/{module_name}.git@{branch}"

    def _resolve_external_repo_url(self, module_name: str, branch: str) -> Optional[str]:
        """Resuelve la URL de Git para un módulo con prefijo externo (nantic_, gcoop_, etc.)."""
        if module_name in self._repos:
            org, repo = self._repos[module_name]
            return f"git+https://github.com/{org}/{repo}.git@{branch}"
        # Fallback to tryton-ar org for modules not explicitly mapped
        return None

    def _process_dep(self, dep: str, branch: str) -> str:
        """Transform a dependency to git URL if it's an external repo."""
        parts = dep.split()
        pkg_name = parts[0]

        # 1. Deps con prefijo trytonar_ → resuelve con external-repos existente
        if pkg_name.startswith('trytonar_'):
            module_name = pkg_name.replace('trytonar_', '')
            url = self._resolve_git_url(module_name, branch)
            return f"{pkg_name} @ {url}"

        # 2. Deps con prefijo externo (nantic_, gcoop_, etc.) → resuelve con repos
        if '_' in pkg_name:
            prefix, module_name = pkg_name.rsplit('_', 1)
            if prefix != 'trytond' and module_name in self._repos:
                url = self._resolve_external_repo_url(module_name, branch)
                if url:
                    return f"{pkg_name} @ {url}"

        # 3. Sin cambios (deps standard como trytond_*)
        return dep

    def update(self, metadata):
        version = metadata.get('version', '8.0.0')
        branch = '.'.join(version.split('.')[:2])  # "8.0"

        # Process regular dependencies
        dependencies = metadata.get('dependencies', [])
        new_deps = [self._process_dep(dep, branch) for dep in dependencies]
        metadata['dependencies'] = new_deps

        # Process optional-dependencies (extras_depend from tryton.cfg)
        optional_deps = metadata.get('optional-dependencies', {})
        if not optional_deps:
            return
        for section_name, section_deps in optional_deps.items():
            if isinstance(section_deps, list):
                processed = [self._process_dep(dep, branch) for dep in section_deps]
                optional_deps[section_name] = processed


# Registramos el Hook en el gestor de plugins de Hatch
@hookimpl
def hatch_register_metadata_hook():
    return TrytonArGitMappingHook
