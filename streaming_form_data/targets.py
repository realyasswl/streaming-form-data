import hashlib


class BaseTarget:
    """Targets determine what to do with some input once the parser is done with
    it.
    """

    def __init__(self, validator=None):
        self.multipart_filename = None
        self.multipart_content_type = None

        self._started = False
        self._finished = False
        self._validator = validator

    def _validate(self, chunk: bytes):
        if self._validator:
            self._validator(chunk)

    def start(self):
        self._started = True
        self.on_start()

    def on_start(self):
        pass

    def finish(self):
        self.on_finish()
        self._finished = True

    def on_finish(self):
        pass

    def is_async(self):
        raise NotImplementedError()


class SyncTarget(BaseTarget):
    def is_async(self):
        return False

    def data_received(self, chunk: bytes):
        self._validate(chunk)
        self.on_data_received(chunk)

    def on_data_received(self, chunk: bytes):
        raise NotImplementedError()


class AsyncTarget(BaseTarget):
    def is_async(self):
        return True

    async def data_received(self, chunk: bytes):
        self._validate(chunk)
        await self.on_data_received(chunk)

    async def on_data_received(self, chunk: bytes):
        raise NotImplementedError()


class NullTarget(SyncTarget):
    def on_data_received(self, chunk: bytes):
        pass


class ValueTarget(SyncTarget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._values = []

    def on_data_received(self, chunk: bytes):
        self._values.append(chunk)

    @property
    def value(self):
        return b''.join(self._values)


class FileTarget(SyncTarget):
    def __init__(self, filename, allow_overwrite=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filename = filename

        self._mode = 'wb' if allow_overwrite else 'xb'
        self._fd = None

    def on_start(self):
        self._fd = open(self.filename, self._mode)

    def on_data_received(self, chunk: bytes):
        self._fd.write(chunk)

    def on_finish(self):
        self._fd.close()


class SHA256Target(SyncTarget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._hash = hashlib.sha256()

    def on_data_received(self, chunk: bytes):
        self._hash.update(chunk)

    @property
    def value(self):
        return self._hash.hexdigest()
