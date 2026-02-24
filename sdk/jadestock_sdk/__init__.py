"""SDK oficial do Jade-stock.

Modulos:
- WMS: pronto para uso
- IA: placeholder para proxima fase
- Contabil: placeholder para proxima fase
"""

from .client import JadeStockClient, JadeStockSDKError
from .ia_client import IAClient
from .contabil_client import ContabilClient

__all__ = [
    "JadeStockClient",
    "JadeStockSDKError",
    "IAClient",
    "ContabilClient",
]
