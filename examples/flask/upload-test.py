#!/usr/bin/python3

import os
import tempfile
import time
from textwrap import dedent

from flask import Flask, request

from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget

from streaming_form_data.targets import BaseTarget


class MultiFileTarget(BaseTarget):
    def __init__(self, dirpath, allow_overwrite=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dirpath = dirpath
        print(dirpath)
        os.mkdir(dirpath)

        self._mode = 'wb' if allow_overwrite else 'xb'
        self._fd = None
        self.count = 0
        self.filenames = []
        self.content_types = []

    def on_start(self):
        print(f'on_start {self.multipart_filename}')
        self.count += 1
        self._fd = open(
            os.path.join(self.dirpath, f'{self.count}'), self._mode
        )

    def on_data_received(self, chunk: bytes):
        self._fd.write(chunk)

    def on_finish(self):
        print(
            f'on_finish {self.multipart_filename} {self.multipart_content_type}'
        )
        self.filenames.append(self.multipart_filename)
        self.content_types.append(self.multipart_content_type)
        self._fd.close()


app = Flask(__name__)


page = dedent(
    '''
    <!doctype html>
    <head>
        <title>Upload new File</title>
    </head>
    <body>
        <h1>Upload new File</h1>
        <form method="post" enctype="multipart/form-data" id="upload-file">
          <input type="file" name="file" multiple>
          <input type="submit" value="Upload">
        </form>
    </body>
'''
)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file_ = MultiFileTarget(os.path.join(tempfile.gettempdir(), 'test'))

        parser = StreamingFormDataParser(headers=request.headers)

        parser.register('file', file_)

        time_start = time.perf_counter()

        while True:
            chunk = request.stream.read(8192)
            if not chunk:
                break
            parser.data_received(chunk)

        time_finish = time.perf_counter()

        response = dedent(
            '''
            <!doctype html>
            <head>
                <title>Done!</title>
            </head>
            <body>
                <h1>
                    {file_name} ({content_type}): upload done
                </h1>
                <h2>
                    Time spent on file reception: {duration}s
                </h2>
            </body>
        '''.format(
                file_name=file_.multipart_filename,
                content_type=file_.multipart_content_type,
                duration=(time_finish - time_start),
            )
        )

        return response
    return page


if __name__ == '__main__':
    app.run(host='0.0.0.0')
