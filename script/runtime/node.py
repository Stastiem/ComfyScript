from __future__ import annotations
from typing import Callable

from . import data

def _positional_args_to_keyword(node: dict, args: tuple) -> dict:
    args = list(args)
    kwargs = {}
    for group in 'required', 'optional':
        group: dict = node['input'].get(group)
        if group is None:
            continue
        for name in group:
            kwargs[name] = args.pop(0)
            if len(args) == 0:
                return kwargs
    if len(args) != 0:
        print(f'ComfyScript: {node["name"]} has more positional arguments than expected: {args}')
    return kwargs

class Node:
    output_hook: Callable[[data.NodeOutput | list[data.NodeOutput]], None] | None = None

    def __init__(self, info: dict, defaults: dict, output_types: list[type]):
        self.info = info
        self.defaults = defaults
        self.output_types = output_types
    
    def __call__(self, *args, **kwds):
        # print(self.info['name'], args, kwds)

        inputs = _positional_args_to_keyword(self.info, args) | kwds
        for k in list(inputs.keys()):
            v = inputs[k]
            if v is None:
                del inputs[k]
            elif isinstance(v, data.NodeOutput) and v.output_slot is None:
                raise TypeError(f'Argument "{k}" is an empty output: {v}')
        inputs = self.defaults | inputs

        node_prompt = {
            'inputs': inputs,
            'class_type': self.info['name'],
        }

        outputs = len(self.output_types)
        if outputs == 0:
            r = data.NodeOutput(self.info, node_prompt, None)
        elif outputs == 1:
            r = self.output_types[0](self.info, node_prompt, 0)
        else:
            r = [output_type(self.info, node_prompt, i) for i, output_type in enumerate(self.output_types)]
        
        if self.info.get('output_node') is True and self.output_hook is not None:
            self.output_hook(r)

        return r

    @classmethod
    def set_output_hook(cls, hook: Callable[[data.NodeOutput | list[data.NodeOutput]], None]):
        if cls.output_hook is not None:
            # TODO: Stack?
            raise RuntimeError('Output hook already set')
        cls.output_hook = hook
    
    @classmethod
    def clear_output_hook(cls):
        cls.output_hook = None

__all__ = ['Node']