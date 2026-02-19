"""SSE (Server-Sent Events) manager for broadcasting live pipeline updates."""

import json
import queue
import time
from datetime import datetime


class SSEManager:
    """Thread-safe SSE broadcaster. Clients subscribe, pipeline emits events."""

    def __init__(self):
        self._clients = []

    def subscribe(self):
        """Create a new SSE client queue and return it."""
        q = queue.Queue(maxsize=100)
        self._clients.append(q)
        return q

    def unsubscribe(self, q):
        """Remove a client queue."""
        try:
            self._clients.remove(q)
        except ValueError:
            pass

    def publish(self, event_type, data):
        """Broadcast an event to all connected clients."""
        msg = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        dead = []
        for q in self._clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            self._clients.remove(q)

    def stream(self, client_queue):
        """Generator that yields SSE-formatted messages for a client."""
        try:
            while True:
                try:
                    msg = client_queue.get(timeout=30)
                    yield f"event: {msg['type']}\ndata: {json.dumps(msg['data'])}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield ": keepalive\n\n"
        except GeneratorExit:
            self.unsubscribe(client_queue)


# Singleton
sse = SSEManager()
