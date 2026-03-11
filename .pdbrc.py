import pdb


def dump_obj(self, obj_name):
    import json
    import tempfile

    import jsonpickle

    obj = self._getval(obj_name)

    serialized = jsonpickle.encode(obj, unpicklable=False, max_depth=5)
    dumped = json.dumps(json.loads(serialized), indent=2)
    print(dumped)

    _, file = tempfile.mkstemp(prefix="dump_", suffix=".json")
    with open(file, "w") as f:
        f.write(dumped)
        print("Content dumped to:", f.name)


def decode_jwt(self, token):
    import jwt
    print(jwt.decode(token, options={"verify_signature": False}))


def force_exit(self, *args):
    import os
    os._exit(1)



class Config(pdb.DefaultConfig):
    sticky_by_default = True
    use_pygments = True
    current_line_color = 50
    editor = "nvim"

    def setup(self, pdb):
        super().setup(pdb)
        Pdb = pdb.__class__
        Pdb.do_dump = dump_obj
        Pdb.do_decode_jwt = decode_jwt
        Pdb.do_Exit = force_exit
        Pdb.do_EOF = force_exit


# Save history across sessions
# https://github.com/pdbpp/pdbpp/issues/52
def _pdbrc_init():
    import readline
    import os

    home = os.environ["HOME"]
    histfile = home + "/.pdb_history"
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    import atexit

    atexit.register(readline.write_history_file, histfile)
    readline.set_history_length(1000)


_pdbrc_init()
del _pdbrc_init
