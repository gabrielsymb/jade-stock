"""SDK oficial do Jade-stock.

Modulos:
- WMS core + trilha XML dedicada: pronto para uso
- IA: placeholder para proxima fase
- Contabil: placeholder para proxima fase
"""

from .client import JadeStockClient, JadeStockSDKError
from .ia_client import IAClient
from .contabil_client import ContabilClient
from .utils import new_correlation_id

__all__ = [
    "JadeStockClient",
    "JadeStockSDKError",
    "IAClient",
    "ContabilClient",
    "new_correlation_id",
]
