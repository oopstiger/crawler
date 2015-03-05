#!/usr/bin/python
# jpc - JSON prototype compiler for python
#   jpc takes several JSON files as input then generates python code that
# can be used to serialize/deserialize those JSON data structures.

import os
import sys
import json
from keyword import iskeyword


class PythonFormatWriter(object):
    def __init__(self, tab_spaces=4, line_ending='\n'):
        self._line_ending = line_ending
        self._tab = ''.join([' ' for _ in range(0, tab_spaces)])
        self._filebuf = []
        self._indent_level = 0
        self._indent = ''

    def __str__(self):
        return self.getstr()

    @property
    def tab(self):
        return self._tab

    def set_indent(self, indent=0):
        self._indent_level = indent
        self._indent = ''.join(['  ' for _ in range(0, indent)])

    def indent(self):
        self._indent_level += 1
        self._indent += self._tab

    def back(self):
        self._indent_level -= 1
        self._indent = self._indent[:-len(self._tab)]

    def putln(self, s=""):
        self._filebuf.append(self._indent)
        if s:
            self._filebuf.append(s)
        self._filebuf.append(self._line_ending)

    def put(self, s):
        self._filebuf.append(s)

    def clear(self):
        self._filebuf = []
        self._indent_level = 0
        self._indent = ''

    def getstr(self):
        return ''.join(self._filebuf)


class JSONObjectMetadata(object):
    def __init__(self, name):
        if iskeyword(name):
            raise SyntaxError("Can't use a python keyword as class name: %s" % name)
        self._classname = name
        self._members = []

    def add_member(self, key, hint, decoder=None):
        name = key
        if iskeyword(name):
            name += '_'
        if isinstance(hint, str) or isinstance(hint, unicode):
            default = "\'\'"
        elif isinstance(hint, bool):  # ATTENTION: bool test must precede int test
            default = "False"
        elif isinstance(hint, int):
            default = "0"
        elif isinstance(hint, float):
            default = "0.0"
        elif isinstance(hint, list):
            default = "[]"
        elif isinstance(hint, dict):
            default = self._classname + "_" + name + "()"
        else:
            default = "None"
        self._members.append((name, key, default, decoder))

    def python_code(self):
        w = PythonFormatWriter()
        w.putln("class %s(object):" % self._classname)
        w.indent()

        # __init__ method
        w.putln("def __init__(self):")
        w.indent()
        for name, key, default, decoder in self._members:
            w.putln("self.%s = %s" % (name, default))
        w.back()  # __init__
        w.putln()

        # from_dict method
        w.putln("@staticmethod")
        w.putln("def from_dict(dct):")
        w.indent()
        w.putln("if not dct:")
        w.indent()
        w.putln("return None")
        w.back()

        w.putln("obj = %s()" % self._classname)
        for name, key, default, decoder in self._members:
            if decoder:
                w.putln("obj.%s = %s(dct.get(\"%s\"))" % (name, decoder, key))
            else:
                w.putln("obj.%s = dct.get(\"%s\")" % (name, key))
        w.putln("return obj")
        w.back()  # from_dict

        w.back()  # class
        return w.getstr()


class JSONPrototypeCompiler(object):
    def __init__(self):
        self._objs = []
        self._metas = []
        self._decoders = []

    def compile_object(self, name, dct):
        self._objs = []
        self._metas = []
        self._decoders = []
        self._parse_dict(name, dct)

    def python_code(self):
        code = []
        for m in self._metas:
            code.append(m.python_code())

        for d in self._decoders:
            code.append(d)
        return "\n\n".join(code)

    def _parse_dict(self, name, dct):
        obj = JSONObjectMetadata(name)
        self._metas.append(obj)
        self._objs.append((name, dct))
        for member, value in dct.items():
            decoder = None
            if not value:
                # null or empty values
                pass
            elif isinstance(value, dict):
                decoder = self._parse_dict(name+"_"+member, value)
            elif isinstance(value, list):
                decoder = self._parse_list(name+"_"+member, value)
            obj.add_member(member, value, decoder)
        return name + ".from_dict"

    def _parse_list(self, name, lst):
        elem = lst[0]
        item_decoder = None
        if isinstance(elem, dict):
            item_decoder = self._parse_dict(name+"_item", elem)
        elif isinstance(elem, list):
            item_decoder = self._parse_list(name+"_item", elem)

        if item_decoder:
            list_decoder = name + "_from_list"
            w = PythonFormatWriter()
            w.putln("def %s(lst):" % list_decoder)
            w.indent()
            w.putln("if not lst:")
            w.indent()
            w.putln("return None")
            w.back()

            w.putln("values = []")
            w.putln("for v in lst:")
            w.indent()
            w.putln("values.append(%s(v))" % item_decoder)
            w.back()
            w.putln("return values")
            w.back()
            self._decoders.append(w.getstr())
            return list_decoder
        return None


if __name__ == "__main__":
    from sys import stdout
    from sys import stderr

    if len(sys.argv) < 2:
        print("Usage: jpc.py [OPTIONS] <FILE1 [FILE2...]>")
        print("Available OPTIONS:")
        print("  -stdout    print python code to standard output instead of files")
        exit(0)

    option_start = 1
    option_end = 1
    while sys.argv[option_end].startswith('-'):
        option_end += 1
    options = sys.argv[option_start:option_end]

    use_stdout = "-stdout" in options

    jpc = JSONPrototypeCompiler()
    for fpath in sys.argv[option_end:]:
        try:
            d = json.load(open(fpath))
            fname = os.path.basename(fpath)
            fdir = fpath[:-len(fname)]
            name = fname.split('.', 1)[0]
            jpc.compile_object(name, d)
            if use_stdout:
                f = stdout
            else:
                e = name.rfind('.')
                if e >= 0:
                    f = open(fdir+name+".py", 'w')
                else:
                    f = open(fdir+name+".py", 'w')
            f.write("# The following code is auto generated by jpc.py\n")
            f.write("# Source JSON file: " + fpath + "\n")
            f.write(jpc.python_code())
            if not use_stdout:
                f.close()
        except Exception, e:
            stderr.write("** ERROR ** Bad JSON file \"%s\"\n" % fpath)
            stderr.write("Exception: %s\n" % str(e))
    exit(0)
