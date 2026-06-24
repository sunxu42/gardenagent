class BaseSessionBackend:
    def __init__(self, *args, **kwargs):
        pass

    async def add_task(self, query, **kwargs):
        pass

    async def achat(self, query, **kwargs):
        pass

    async def shutdown(self):
        pass
