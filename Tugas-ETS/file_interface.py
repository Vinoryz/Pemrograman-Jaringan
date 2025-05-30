import os
import json
import base64
from glob import glob

from IPython.core.guarded_eval import dict_keys


class FileInterface:
    def __init__(self):
        os.chdir('files/')

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if filename == '':
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def upload(self, params=[]):
        if len(params) != 2:
            return dict(status='ERROR',data="This command need 2 parameters")

        try:
            filename = params[0]
            file_content = params[1]
            file_content = base64.b64decode(file_content.encode())
            fp = open(filename,'wb+')
            fp.write(file_content)
            print(f"Successfully uploaded {filename}")
            # os.remove(filename)
            return dict(status='OK', data=f"Uploaded {filename}")
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        try:
            filename = params[0]
            os.remove(filename)
            print(f"Successfully deleted {filename}")
            return dict(status='OK', data=f"Successfully deleted {filename}")
        except Exception as e:
            return dict(status='ERROR', data=str(e))

if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    # print(f.get(['pokijan.jpg']))
    # print(f.upload(["test.txt", "SGVsbG8sIHdvcmxkIQ=="]))
    # print(f.list())
