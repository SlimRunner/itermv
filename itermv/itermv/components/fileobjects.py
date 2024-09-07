import os


class NewFile:
    def __init__(self, path: str) -> None:
        self.__path = path
        fdir, fname = os.path.split(path)
        self.__name = fname
        self.__parent = fdir

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def parent(self) -> str:
        return self.__parent

    @property
    def path(self) -> str:
        return self.__path


class FileEntry:
    def __init__(self, name: str, path: str) -> None:
        self.__path = os.path.join(path, name)
        fullpath = self.__path
        fdir, fname = os.path.split(fullpath)
        if not os.path.exists(fullpath):
            raise FileNotFoundError(f"file does not exist: {fullpath}")
        noxname, ext = os.path.splitext(fname)
        self.__name = fname
        self.__noextname = noxname
        self.__extension = ext
        self.__parent = fdir
        self.__mtime = os.path.getmtime(fullpath)
        self.__atime = os.path.getatime(fullpath)
        # ctime is not consistent across platforms.
        self.__ctime = os.path.getctime(fullpath)
        self.__size = os.path.getsize(fullpath)

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def noextname(self) -> str:
        return self.__noextname

    @property
    def extension(self) -> str:
        return self.__extension

    @property
    def parent(self) -> str:
        return self.__parent

    @property
    def path(self) -> str:
        return self.__path

    @property
    def mtime(self) -> float:
        return self.__mtime

    @property
    def atime(self) -> float:
        return self.__atime

    @property
    def ctime(self) -> float:
        return self.__ctime

    @property
    def size(self) -> int:
        return self.__size


class InputPath:
    def __init__(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory was not found: {path}")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Provided file is not a directory: {path}")

        self.__path = os.path.abspath(path)

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def path(self) -> str:
        return self.__path
