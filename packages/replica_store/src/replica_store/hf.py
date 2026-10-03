"""Generic HF bucket adapter. Standard SDK authentication remains private."""
class HFRemote:
    def __init__(self,bucket,api=None):
        if api is None:
            from huggingface_hub import HfApi
            api=HfApi()
        self.api=api;self.bucket=bucket
    def info(self,key):
        from huggingface_hub.errors import EntryNotFoundError
        try:rows=list(self.api.get_bucket_paths_info(self.bucket,[key]))
        except EntryNotFoundError:return None
        rows=[r for r in rows if getattr(r,'path',None)==key]
        if not rows:return None
        if len(rows)!=1 or getattr(rows[0],'type','file')!='file':raise ValueError('Ambiguous remote object')
        return rows[0].size
    def upload(self,path,key):self.api.batch_bucket_files(self.bucket,add=[(path,key)])
    def download(self,key,destination):self.api.download_bucket_files(self.bucket,[(key,destination)],raise_on_missing_files=True)
    def list(self,prefix):
        for entry in self.api.list_bucket_tree(self.bucket,prefix=prefix,recursive=True):
            if getattr(entry,'type',None)=='file':yield entry.path,entry.size
