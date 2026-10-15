from faststream.nats import JStream, NatsBroker

from core.config import settings

broker = NatsBroker(settings.NATS_URL)
orders_stream = JStream(name="ORDERS", subjects=["orders.>"])

order_created_publisher = broker.publisher("orders.created", stream=orders_stream)

order_cancelled_publisher = broker.publisher("orders.cancelled", stream=orders_stream)
