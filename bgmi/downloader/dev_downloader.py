from bgmi.downloader.base import BaseDownloadService


class DevDownloadDelegate(BaseDownloadService):

    def __init__(self, *args, **kwargs):
        super(DevDownloadDelegate, self).__init__(**kwargs)

    def download(self):
        print(self.torrent, self.save_path)
        print(self.overwrite)
        pass

    @staticmethod
    def install():
        pass

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        pass
