"""Introspect fx.mono.colors and fx.mono.effects for GUI form generation."""
import inspect

def _params_from_module(module, skip_first=0):
    """Get callables and their param names (after skip_first) and optional defaults."""
    result = {}
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        sig = inspect.signature(obj)
        param_names = list(sig.parameters.keys())
        if len(param_names) <= skip_first:
            result[name] = []
            continue
        param_names = param_names[skip_first:]
        params_with_defaults = []
        for pname in param_names:
            p = sig.parameters[pname]
            default = p.default if p.default is not inspect.Parameter.empty else None
            params_with_defaults.append((pname, default))
        result[name] = params_with_defaults
    return result

def get_color_meta():
    """Returns dict: color_name -> [(param_name, default_value), ...]. Skips first arg 'strip'."""
    from fx.mono import colors
    return _params_from_module(colors, skip_first=1)

def get_effect_meta():
    """Returns dict: effect_name -> [(param_name, default_value), ...]. Skips first arg 'strip'."""
    from fx.mono import effects
    return _params_from_module(effects, skip_first=1)
