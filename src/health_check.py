import requests

class HealthChecker:
    """
    Classe para verificar o estado (health) de um endpoint HTTP.
    """

    def __init__(self, url: str, timeout: int = 5):
        """
        :param url: endpoint que será verificado
        :param timeout: tempo máximo (em segundos) de espera pela resposta
        """
        self.url = url
        self.timeout = timeout

    def is_healthy(self) -> bool:
        """
        Faz um GET na URL configurada e retorna True se o status code for 200.
        Em qualquer outra situação (status diferente ou exceção), retorna False.
        """
        try:
            response = requests.get(self.url, timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False
