from abc import ABC, abstractmethod

class Datasource(ABC):

    @abstractmethod
    def get_client(self):
        pass 

