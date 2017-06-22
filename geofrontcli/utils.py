""":mod:`geofrontcli.utils` --- Utility functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import re

__all__ = ('resolve_cmdarg_template', )


CMDARG_VAR_PATTERN = re.compile(r'\$(?P<name>[A-Za-z]\w*)')


def resolve_cmdarg_template(template, vars):
    resolved = template[:]

    def resolve_var(matchobj):
        name = matchobj.group('name')
        return str(vars[name])

    for idx, piece in enumerate(resolved):
        if isinstance(piece, bytes):
            continue
        new_piece, num_replaced = CMDARG_VAR_PATTERN.subn(resolve_var, piece)
        if num_replaced:
            resolved[idx] = new_piece

    return resolved
